#!/usr/bin/env python3
import json
import pathlib
import time


LAB_ROOT = pathlib.Path(__file__).resolve().parent
CALLS_PATH = LAB_ROOT / "saved_calls.json"
LOG_PATH = LAB_ROOT / "eval_results.jsonl"


def evaluate(call):
    checks = []
    result = call.get("result", {})
    policy = call.get("policy", {})
    allowed = policy.get("allowed")
    successful = allowed is True and result.get("ok") is True

    checks.append({"name": "has_policy_decision", "passed": "allowed" in policy})
    if allowed is False:
        checks.append({"name": "blocked_calls_do_not_succeed", "passed": result.get("ok") is False})

    checks.append(
        {
            "name": "successful_calls_include_summary",
            "passed": True if not successful else "summary" in result,
            "applies": successful,
        }
    )

    return {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": call.get("tool"),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def main():
    calls = json.loads(CALLS_PATH.read_text(encoding="utf-8"))
    results = [evaluate(call) for call in calls]
    with LOG_PATH.open("w", encoding="utf-8") as log:
        for result in results:
            log.write(json.dumps(result) + "\n")
    print(json.dumps({"results": results}, indent=2))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
