#!/usr/bin/env python3
import argparse
import json
import urllib.error
import urllib.request


def fetch_json(url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def list_models(base_url, kind):
    if kind == "ollama":
        payload = fetch_json(base_url.rstrip("/") + "/api/tags")
        return {"ok": True, "kind": kind, "models": [item["name"] for item in payload.get("models", [])]}
    payload = fetch_json(base_url.rstrip("/") + "/v1/models")
    return {"ok": True, "kind": kind, "models": [item["id"] for item in payload.get("data", [])]}


def prompt_once(base_url, kind, model, prompt):
    if kind == "ollama":
        payload = fetch_json(
            base_url.rstrip("/") + "/api/generate",
            {"model": model, "prompt": prompt, "stream": False},
        )
        return {"ok": True, "kind": kind, "model": model, "response": payload.get("response", "")}
    payload = fetch_json(
        base_url.rstrip("/") + "/v1/chat/completions",
        {"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    message = payload.get("choices", [{}])[0].get("message", {})
    return {"ok": True, "kind": kind, "model": model, "response": message.get("content", "")}


def main():
    parser = argparse.ArgumentParser(description="Probe a real local model endpoint.")
    parser.add_argument("--kind", choices=["ollama", "openai-compatible"], required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model")
    parser.add_argument("--prompt", default="Say hello from the local bootstrap probe.")
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()

    try:
        if args.list_models or not args.model:
            result = list_models(args.base_url, args.kind)
        else:
            result = prompt_once(args.base_url, args.kind, args.model, args.prompt)
    except urllib.error.URLError as error:
        result = {"ok": False, "error": "endpoint_unreachable", "detail": str(error.reason)}
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        result = {"ok": False, "error": "http_error", "status": error.code, "detail": body}

    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
