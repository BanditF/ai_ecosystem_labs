#!/usr/bin/env python3
import argparse
import json
import pathlib


LAB_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = LAB_ROOT.parent
SAMPLE_DOCS = REPO_ROOT / "sample_docs"
FILES = [
    str(SAMPLE_DOCS / "agents.txt"),
    str(SAMPLE_DOCS / "protocols.txt"),
    str(SAMPLE_DOCS / "memory.txt"),
]


def term_count(term, files):
    items = []
    total = 0
    for name in files:
        text = pathlib.Path(name).read_text(encoding="utf-8", errors="ignore").lower()
        count = text.count(term.lower())
        items.append({"file": name, "count": count})
        total += count
    return {"ok": True, "items": items, "summary": {"total": total}}


def decide_next_step(state):
    if not state["steps"]:
        return {
            "type": "tool_call",
            "tool": "term_count",
            "arguments": {"term": state["term"], "files": FILES},
            "reason": "Need evidence before answering.",
        }
    total = state["steps"][-1]["result"]["summary"]["total"]
    return {
        "type": "done",
        "answer": f"Found {total} mentions of {state['term']!r} across sample docs.",
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum number of loop steps before stopping (default: 10).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    state = {
        "goal": "Find where the docs discuss agents.",
        "term": "agent",
        "steps": [],
        "max_steps": args.max_steps,
    }

    while True:
        if len(state["steps"]) >= args.max_steps:
            state["final"] = f"Step limit reached after {args.max_steps} steps."
            break

        decision = decide_next_step(state)
        if decision["type"] == "done":
            state["final"] = decision["answer"]
            break
        if decision["tool"] == "term_count":
            result = term_count(decision["arguments"]["term"], decision["arguments"]["files"])
        else:
            result = {"ok": False, "error": "unknown_tool"}
        state["steps"].append({"decision": decision, "result": result})

    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
