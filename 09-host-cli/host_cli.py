#!/usr/bin/env python3
import argparse
import json
import pathlib


TOOLS = {
    "term_count": {
        "description": "Count a term across sample docs.",
        "requires_approval": True,
    }
}


def term_count(arguments):
    term = arguments["term"].lower()
    total = 0
    items = []
    for name in arguments["files"]:
        text = pathlib.Path(name).read_text(encoding="utf-8", errors="ignore").lower()
        count = text.count(term)
        items.append({"file": name, "count": count})
        total += count
    return {"ok": True, "items": items, "summary": {"total": total}}


def main():
    parser = argparse.ArgumentParser(description="Tiny host-like CLI.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("tools")
    run = sub.add_parser("run")
    run.add_argument("tool")
    run.add_argument("arguments_json")
    run.add_argument("--approve", action="store_true")
    args = parser.parse_args()

    if args.command == "tools":
        print(json.dumps({"tools": TOOLS}, indent=2))
        return 0

    if args.command == "run":
        if args.tool not in TOOLS:
            print(json.dumps({"ok": False, "error": "unknown_tool"}, indent=2))
            return 1
        if TOOLS[args.tool]["requires_approval"] and not args.approve:
            print(json.dumps({"ok": False, "approval_required": True, "tool": args.tool}, indent=2))
            return 2
        arguments = json.loads(args.arguments_json)
        print(json.dumps(term_count(arguments), indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
