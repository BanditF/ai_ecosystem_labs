#!/usr/bin/env python3
import json
import pathlib
import sys
import time


LAB_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = LAB_ROOT.parent
SAMPLE_DOCS = REPO_ROOT / "sample_docs"
LOG_PATH = LAB_ROOT / "tool_calls.jsonl"
DEFAULT_BLOCKED_TERMS = {"password", "secret", "token"}


def blocked_terms(block_term=None):
    if block_term:
        return {block_term.lower()}
    return DEFAULT_BLOCKED_TERMS


def before_tool_call(name, arguments, block_term=None):
    term = str(arguments.get("term", "")).lower()
    if term in blocked_terms(block_term):
        return {"allow": False, "reason": f"blocked sensitive term: {term}"}
    return {"allow": True, "reason": "read-only search"}


def after_tool_call(record):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")


def fake_tool(arguments):
    term = arguments["term"].lower()
    total = 0
    for name in arguments["files"]:
        text = pathlib.Path(name).read_text(encoding="utf-8", errors="ignore").lower()
        total += text.count(term)
    return {"ok": True, "summary": {"total": total}}


def run_tool(name, arguments, executor=None, block_term=None):
    decision = before_tool_call(name, arguments, block_term=block_term)
    record = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": name,
        "arguments": arguments,
        "decision": decision,
    }
    if not decision["allow"]:
        record["result"] = {"ok": False, "error": "blocked_by_hook"}
        after_tool_call(record)
        return record

    tool_executor = executor or fake_tool
    record["result"] = tool_executor(arguments)
    after_tool_call(record)
    return record


def main():
    term = sys.argv[1] if len(sys.argv) > 1 else "agent"
    record = run_tool("term_count", {"term": term, "files": [str(SAMPLE_DOCS / "agents.txt")]})
    print(json.dumps(record, indent=2))
    return 0 if record["result"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
