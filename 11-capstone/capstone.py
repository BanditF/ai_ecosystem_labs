#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time


LAB_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = LAB_ROOT.parent
SAMPLE_DOCS = REPO_ROOT / "sample_docs"
TASK_GRAPH_PATH = REPO_ROOT / "07-task-graph" / "tasks.json"
PROTOCOL_SERVER_PATH = REPO_ROOT / "03-protocol-adapter" / "protocol_server.py"
OUTPUT_PATH = LAB_ROOT / "capstone_run.json"
SAMPLE_FILES = [str(SAMPLE_DOCS / "agents.txt"), str(SAMPLE_DOCS / "protocols.txt")]
DEFAULT_BLOCKED_TERMS = {"password", "secret", "token"}


def blocked_terms(block_term=None):
    if block_term:
        return {block_term.lower()}
    return DEFAULT_BLOCKED_TERMS


def approve_tool_call(arguments, block_term=None):
    term = arguments.get("term", "").lower()
    if term in blocked_terms(block_term):
        return {"allowed": False, "reason": "sensitive term"}
    if not all(pathlib.Path(path).resolve().parent == SAMPLE_DOCS.resolve() for path in arguments.get("files", [])):
        return {"allowed": False, "reason": "only sample docs are allowed"}
    return {"allowed": True, "reason": "read-only sample docs query"}


def protocol_call(name, arguments):
    request = {
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    result = subprocess.run(
        [sys.executable, str(PROTOCOL_SERVER_PATH)],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or "protocol_server_failed"}
    response = json.loads(result.stdout)
    return response.get("result", {"ok": False, "error": response.get("error", {})})


def ready_tasks():
    data = json.loads(TASK_GRAPH_PATH.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in data["tasks"]}
    return [
        task["id"]
        for task in data["tasks"]
        if task["status"] == "pending"
        and all(tasks[dep]["status"] == "done" for dep in task.get("deps", []))
    ]


def evaluate(record):
    result = record["tool_result"]
    checks = [
        {"name": "policy_allowed", "passed": record["policy"]["allowed"]},
        {"name": "tool_returned_ok", "passed": result.get("ok") is True},
        {"name": "summary_present", "passed": "summary" in result},
        {"name": "ready_tasks_visible", "passed": bool(record["ready_tasks"])},
    ]
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--block-term",
        default=os.environ.get("BLOCK_TERM"),
        help="Override the blocked term at runtime. Defaults to BLOCK_TERM or the built-in sensitive terms.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    arguments = {"term": "agent", "files": SAMPLE_FILES}
    record = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "goal": "Find agent mentions in sample docs and leave an auditable trail.",
        "host": {"approved_by": "toy-user"},
        "tool": "term_count",
        "arguments": arguments,
        "policy": approve_tool_call(arguments, block_term=args.block_term),
        "policy_config": {
            "block_term": args.block_term,
            "effective_blocked_terms": sorted(blocked_terms(args.block_term)),
        },
        "ready_tasks": ready_tasks(),
    }

    if record["policy"]["allowed"]:
        record["tool_result"] = protocol_call("term_count", arguments)
    else:
        record["tool_result"] = {"ok": False, "error": "blocked_by_policy"}

    record["eval"] = evaluate(record)
    OUTPUT_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0 if record["eval"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
