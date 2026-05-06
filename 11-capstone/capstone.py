#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import subprocess
import sys


LAB_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = LAB_ROOT.parent
SAMPLE_DOCS = REPO_ROOT / "sample_docs"
TASK_GRAPH_PATH = REPO_ROOT / "07-task-graph" / "tasks.json"
PROTOCOL_SERVER_PATH = REPO_ROOT / "03-protocol-adapter" / "protocol_server.py"
OUTPUT_PATH = LAB_ROOT / "capstone_run.json"
SAMPLE_FILES = [str(SAMPLE_DOCS / "agents.txt"), str(SAMPLE_DOCS / "protocols.txt")]

for lab_dir in ("05-hook", "09-host-cli", "10-governance"):
    lab_path = REPO_ROOT / lab_dir
    if str(lab_path) not in sys.path:
        sys.path.insert(0, str(lab_path))

from eval_runner import evaluate
from hook_runner import blocked_terms, run_tool as run_hooked_tool
from host_cli import request_tool_approval


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


def protocol_term_count(arguments):
    return protocol_call("term_count", arguments)


def ready_tasks():
    data = json.loads(TASK_GRAPH_PATH.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in data["tasks"]}
    return [
        task["id"]
        for task in data["tasks"]
        if task["status"] == "pending"
        and all(tasks[dep]["status"] == "done" for dep in task.get("deps", []))
    ]


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
    tool_name = "term_count"
    arguments = {"term": "agent", "files": SAMPLE_FILES}
    host = request_tool_approval(tool_name, approve=True, approved_by="toy-user")
    hook_record = run_hooked_tool(tool_name, arguments, executor=protocol_term_count, block_term=args.block_term)
    policy = {
        "allowed": hook_record["decision"]["allow"],
        "reason": hook_record["decision"]["reason"],
    }

    record = {
        "time": hook_record["time"],
        "goal": "Find agent mentions in sample docs and leave an auditable trail.",
        "host": host,
        "tool": tool_name,
        "arguments": arguments,
        "policy": policy,
        "policy_config": {
            "block_term": args.block_term,
            "effective_blocked_terms": sorted(blocked_terms(args.block_term)),
        },
        "ready_tasks": ready_tasks(),
        "tool_result": hook_record["result"],
        "hook": hook_record,
    }
    record["eval"] = evaluate(
        {
            "tool": tool_name,
            "policy": policy,
            "result": record["tool_result"],
            "ready_tasks": record["ready_tasks"],
        }
    )

    OUTPUT_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0 if record["eval"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
