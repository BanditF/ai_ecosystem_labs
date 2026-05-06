#!/usr/bin/env python3
import argparse
import json
import os
import urllib.error
import urllib.request


REAL_CHAT_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def call_model(prompt, endpoint, api_key, model):
    redacted_key = "set" if api_key else "missing"

    # Real call when key is set, toy mode otherwise.
    if api_key:
        request_model = model if model and model != "toy-v1" else "gpt-4o-mini"
        body = json.dumps(
            {
                "model": request_model,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            REAL_CHAT_COMPLETIONS_ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            message = payload.get("choices", [{}])[0].get("message", {})
            return {
                "ok": True,
                "endpoint": REAL_CHAT_COMPLETIONS_ENDPOINT,
                "api_key": redacted_key,
                "model": request_model,
                "prompt": prompt,
                "response": message.get("content", ""),
            }
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            return {
                "ok": False,
                "endpoint": REAL_CHAT_COMPLETIONS_ENDPOINT,
                "api_key": redacted_key,
                "model": request_model,
                "prompt": prompt,
                "response": f"HTTP {error.code}: {detail}",
            }
        except urllib.error.URLError as error:
            return {
                "ok": False,
                "endpoint": REAL_CHAT_COMPLETIONS_ENDPOINT,
                "api_key": redacted_key,
                "model": request_model,
                "prompt": prompt,
                "response": f"Request failed: {error.reason}",
            }

    return {
        "ok": True,
        "endpoint": endpoint,
        "api_key": redacted_key,
        "model": model,
        "prompt": prompt,
        "response": f"Toy model response to: {prompt}",
    }


def main():
    parser = argparse.ArgumentParser(description="Tiny CLI around model access.")
    parser.add_argument("prompt")
    parser.add_argument("--endpoint", default=os.getenv("TOY_MODEL_ENDPOINT", "local://toy-model"))
    parser.add_argument("--api-key", default=os.getenv("TOY_MODEL_API_KEY", ""))
    parser.add_argument("--model", default=os.getenv("TOY_MODEL_NAME", "toy-v1"))
    parser.add_argument("--json", action="store_true", help="Return structured output.")
    args = parser.parse_args()

    result = call_model(args.prompt, args.endpoint, args.api_key, args.model)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["response"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
