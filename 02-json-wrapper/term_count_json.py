#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys


def count_term(term, files):
    items = []
    errors = []
    total = 0
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

    return {
        "ok": not errors,
        "version": "1.0",
        "tool": "term_count",
        "input": {"term": term, "files": files},
        "items": items,
        "summary": {"total": total},
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Count a term and return JSON.")
    parser.add_argument("term")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        result = {
            "ok": True,
            "version": "1.0",
            "tool": "term_count",
            "dry_run": True,
            "planned": {"term": args.term, "files": args.files},
        }
    else:
        result = count_term(args.term, args.files)

    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
