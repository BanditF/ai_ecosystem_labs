#!/usr/bin/env python3
import json
import pathlib
import time


CALLS_PATH = pathlib.Path("labs/10-governance/saved_calls.json")
LOG_PATH = pathlib.Path("labs/10-governance/eval_results.jsonl")


def evaluate(call):
    checks = []
    result = call.get("result", {})
    policy = call.get("policy", {})

    checks.append({"name": "has_policy_decision", "passed": "allowed" in policy})
    if policy.get("allowed"):
        checks.append({"name": "valid_success_shape", "passed": result.get("ok") is True and "summary" in result})
    else:
        checks.append({"name": "blocked_calls_do_not_succeed", "passed": result.get("ok") is False})

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
