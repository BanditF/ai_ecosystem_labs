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


TOOL_HANDLERS = {"term_count": term_count}


def request_tool_approval(tool_name, approve=False, approved_by=None):
    tool = TOOLS.get(tool_name)
    if tool is None:
        return {"ok": False, "error": "unknown_tool", "tool": tool_name}

    requires_approval = tool.get("requires_approval", False)
    decision = {
        "ok": True,
        "tool": tool_name,
        "requires_approval": requires_approval,
        "approved": True,
    }
    if approved_by is not None:
        decision["approved_by"] = approved_by

    if requires_approval and not approve:
        decision["ok"] = False
        decision["approved"] = False
        decision["approval_required"] = True

    return decision


def run_tool(tool_name, arguments, approve=False):
    decision = request_tool_approval(tool_name, approve=approve)
    if not decision["ok"]:
        return decision
    return TOOL_HANDLERS[tool_name](arguments)


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
        result = run_tool(args.tool, json.loads(args.arguments_json), approve=args.approve)
        print(json.dumps(result, indent=2))
        if result.get("approval_required"):
            return 2
        return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
