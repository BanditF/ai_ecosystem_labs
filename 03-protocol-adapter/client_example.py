#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUESTS = [
    {"id": 1, "method": "tools/list"},
    {
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "term_count",
            "arguments": {
                "term": "agent",
                "files": [str(ROOT / "sample_docs/agents.txt"), str(ROOT / "sample_docs/protocols.txt")],
            },
        },
    },
]


def main():
    payload = "\n".join(json.dumps(request) for request in REQUESTS) + "\n"
    result = subprocess.run(
        [sys.executable, str(ROOT / "03-protocol-adapter/protocol_server.py")],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
