#!/usr/bin/env python3
import argparse
import pathlib
import sys


def count_term(term, files, case_sensitive=False):
    needle = term if case_sensitive else term.lower()
    total = 0
    for name in files:
        path = pathlib.Path(name)
        text = path.read_text(encoding="utf-8", errors="ignore")
        haystack = text if case_sensitive else text.lower()
        count = haystack.count(needle)
        total += count
        print(f"{path}: {count}")
    print(f"total: {total}")


def main():
    parser = argparse.ArgumentParser(description="Count a term across files.")
    parser.add_argument("term")
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Match letter casing exactly instead of using case-insensitive search.",
    )
    args = parser.parse_args()

    missing = [name for name in args.files if not pathlib.Path(name).is_file()]
    if missing:
        for name in missing:
            print(f"missing file: {name}", file=sys.stderr)
        return 1

    count_term(args.term, args.files, case_sensitive=args.case_sensitive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
