#!/usr/bin/env python3
import json
import pathlib
import sys


TOOL_SCHEMA = {
    "name": "term_count",
    "description": "Count how often a term appears across local text files.",
    "input_schema": {
        "type": "object",
        "required": ["term", "files"],
        "properties": {
            "term": {"type": "string"},
            "files": {"type": "array", "items": {"type": "string"}},
        },
    },
}


def term_count(arguments):
    term = arguments.get("term")
    files = arguments.get("files")
    if not isinstance(term, str) or not isinstance(files, list):
        return {"ok": False, "errors": [{"error": "invalid_arguments"}]}

    total = 0
    items = []
    errors = []
    lowered = term.lower()
    for name in files:
        path = pathlib.Path(name)
        if not path.is_file():
            errors.append({"file": name, "error": "missing_file"})
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        count = text.count(lowered)
        total += count
        items.append({"file": str(path), "count": count})
    return {"ok": not errors, "items": items, "summary": {"total": total}, "errors": errors}


def handle(request):
    method = request.get("method")
    if method == "tools/list":
        return {"id": request.get("id"), "result": {"tools": [TOOL_SCHEMA]}}
    if method == "tools/call":
        params = request.get("params", {})
        if params.get("name") != "term_count":
            return {"id": request.get("id"), "error": {"message": "unknown tool"}}
        return {"id": request.get("id"), "result": term_count(params.get("arguments", {}))}
    return {"id": request.get("id"), "error": {"message": "unknown method"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle(request)
        except json.JSONDecodeError as exc:
            response = {"id": None, "error": {"message": f"invalid json: {exc.msg}"}}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
