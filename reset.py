#!/usr/bin/env python3
import json
import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parent

TASKS = {
    "tasks": [
        {"id": "write-wrapper", "title": "Write JSON wrapper", "status": "done", "deps": []},
        {"id": "add-hook", "title": "Add pre-tool hook", "status": "pending", "deps": ["write-wrapper"]},
        {"id": "agent-loop", "title": "Wire agent loop", "status": "pending", "deps": ["add-hook"]},
        {"id": "log-calls", "title": "Log tool calls", "status": "pending", "deps": ["agent-loop"]},
    ]
}

QUEUE = {
    "tasks": [
        {"id": "inspect-docs", "kind": "docs", "status": "ready"},
        {"id": "run-validation", "kind": "validation", "status": "ready"},
        {"id": "publish-summary", "kind": "docs", "status": "blocked"},
    ],
    "claims": [],
}

PLATFORM_STATE = {
    "assistant_name": "toy-platform",
    "channels": {
        "cli": {"kind": "interactive", "messages": 0},
        "companion": {"kind": "async", "messages": 0},
        "ops": {"kind": "worker", "messages": 0},
    },
    "memory": [],
    "searches": [],
    "delegations": [],
    "schedules": [],
    "next_ids": {"memory": 1, "schedule": 1, "delegation": 1},
}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def remove(path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main():
    write_json(ROOT / "07-task-graph" / "tasks.json", TASKS)
    write_json(ROOT / "08-coordinator" / "queue.json", QUEUE)
    write_json(ROOT / "12-persistent-platform" / "state.json", PLATFORM_STATE)

    for relative in [
        "05-hook/tool_calls.jsonl",
        "08-coordinator/events.jsonl",
        "10-governance/eval_results.jsonl",
        "11-capstone/capstone_run.json",
        "12-persistent-platform/events.jsonl",
        "12-persistent-platform/messages.jsonl",
        "13-local-broker/events.jsonl",
    ]:
        remove(ROOT / relative)

    for cache in ROOT.rglob("__pycache__"):
        remove(cache)

    print("labs reset")


if __name__ == "__main__":
    main()
