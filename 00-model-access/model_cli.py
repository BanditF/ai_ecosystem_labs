#!/usr/bin/env python3
import argparse
import json
import os


def call_model(prompt, endpoint, api_key):
    redacted_key = "set" if api_key else "missing"
    return {
        "ok": True,
        "endpoint": endpoint,
        "api_key": redacted_key,
        "prompt": prompt,
        "response": f"Toy model response to: {prompt}",
    }


def main():
    parser = argparse.ArgumentParser(description="Tiny CLI around model access.")
    parser.add_argument("prompt")
    parser.add_argument("--endpoint", default=os.getenv("TOY_MODEL_ENDPOINT", "local://toy-model"))
    parser.add_argument("--api-key", default=os.getenv("TOY_MODEL_API_KEY", ""))
    parser.add_argument("--json", action="store_true", help="Return structured output.")
    args = parser.parse_args()

    result = call_model(args.prompt, args.endpoint, args.api_key)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["response"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
