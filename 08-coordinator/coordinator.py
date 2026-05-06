#!/usr/bin/env python3
import argparse
import json
import pathlib
import time


LAB_ROOT = pathlib.Path(__file__).resolve().parent
QUEUE_PATH = LAB_ROOT / "queue.json"
EVENTS_PATH = LAB_ROOT / "events.jsonl"


def load_queue():
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(data):
    QUEUE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def event(record):
    record["time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with EVENTS_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")


def claim(worker, kind):
    data = load_queue()
    claimed_ids = {claim["task_id"] for claim in data["claims"]}
    for task in data["tasks"]:
        if task["status"] == "ready" and task["kind"] == kind and task["id"] not in claimed_ids:
            data["claims"].append({"worker": worker, "task_id": task["id"]})
            save_queue(data)
            event({"event": "claimed", "worker": worker, "task_id": task["id"]})
            return {"ok": True, "task": task}
    return {"ok": False, "error": "no_ready_task"}


def complete(worker, task_id):
    data = load_queue()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = "done"
            data["claims"] = [claim for claim in data["claims"] if claim["task_id"] != task_id]
            save_queue(data)
            event({"event": "completed", "worker": worker, "task_id": task_id})
            return {"ok": True, "task": task}
    return {"ok": False, "error": "unknown_task"}


def main():
    parser = argparse.ArgumentParser(description="Tiny workspace coordinator.")
    sub = parser.add_subparsers(dest="command", required=True)
    claim_cmd = sub.add_parser("claim")
    claim_cmd.add_argument("worker")
    claim_cmd.add_argument("kind")
    complete_cmd = sub.add_parser("complete")
    complete_cmd.add_argument("worker")
    complete_cmd.add_argument("task_id")
    args = parser.parse_args()

    if args.command == "claim":
        print(json.dumps(claim(args.worker, args.kind), indent=2))
    if args.command == "complete":
        print(json.dumps(complete(args.worker, args.task_id), indent=2))


if __name__ == "__main__":
    main()
