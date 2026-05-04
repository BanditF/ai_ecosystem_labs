#!/usr/bin/env python3
import argparse
import json
import pathlib


DEFAULT_PATH = pathlib.Path("labs/07-task-graph/tasks.json")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ready_tasks(data):
    tasks = {task["id"]: task for task in data["tasks"]}
    ready = []
    for task in data["tasks"]:
        if task["status"] != "pending":
            continue
        if all(tasks[dep]["status"] == "done" for dep in task.get("deps", [])):
            ready.append(task)
    return ready


def main():
    parser = argparse.ArgumentParser(description="Tiny dependency-aware task graph.")
    parser.add_argument("--file", default=str(DEFAULT_PATH))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ready")
    done = sub.add_parser("done")
    done.add_argument("task_id")
    args = parser.parse_args()

    path = pathlib.Path(args.file)
    data = load(path)

    if args.command == "ready":
        print(json.dumps({"ready": ready_tasks(data)}, indent=2))
        return 0

    if args.command == "done":
        for task in data["tasks"]:
            if task["id"] == args.task_id:
                task["status"] = "done"
                save(path, data)
                print(json.dumps({"ok": True, "task": task}, indent=2))
                return 0
        print(json.dumps({"ok": False, "error": "unknown_task"}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
