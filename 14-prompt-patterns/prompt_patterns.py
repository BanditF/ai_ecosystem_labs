#!/usr/bin/env python3
"""Lab 14: Prompt Patterns
Demonstrates zero-shot, few-shot, chain-of-thought, and structured output prompting.
"""

import json
import os
import sys
import urllib.error
import urllib.request


REAL_CHAT_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# ── mock response for demo without API key ──────────────────
MOCK_RESPONSES = {
    "zero_shot": "Berlin",
    "few_shot": "Berlin",
    "cot": "Step 1: The question asks about Germany.\nStep 2: Germany's capital is Berlin.\nAnswer: Berlin",
    "structured": '{"capital": "Berlin", "country": "Germany", "confidence": "high"}',
}


def build_zero_shot_prompt(question: str) -> list[dict]:
    return [
        {"role": "system", "content": "Answer geography questions concisely."},
        {"role": "user", "content": question},
    ]


def build_few_shot_prompt(question: str) -> list[dict]:
    return [
        {"role": "system", "content": "Answer geography questions concisely."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "Paris"},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
        {"role": "user", "content": question},
    ]


def build_cot_prompt(question: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": "Answer geography questions. Think step by step before giving your final answer.",
        },
        {"role": "user", "content": question},
    ]


def build_structured_prompt(question: str) -> list[dict]:
    schema = {"capital": "string", "country": "string", "confidence": "high|medium|low"}
    return [
        {
            "role": "system",
            "content": f"Answer geography questions. Respond ONLY with valid JSON matching this schema: {json.dumps(schema)}",
        },
        {"role": "user", "content": question},
    ]


def call_model(messages: list[dict], pattern_name: str) -> str:
    api_key = os.environ.get("TOY_MODEL_API_KEY")
    if not api_key:
        print("Prompt structure:")
        print(json.dumps(messages, indent=2))
        print("Expected output:")
        return MOCK_RESPONSES.get(pattern_name, "[mock response]")

    request_model = os.environ.get("TOY_MODEL_NAME", "gpt-3.5-turbo")
    payload = json.dumps(
        {"model": request_model, "messages": messages, "max_tokens": 150}
    ).encode("utf-8")
    request = urllib.request.Request(
        REAL_CHAT_COMPLETIONS_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return f"HTTP {error.code}: {detail}"
    except urllib.error.URLError as error:
        return f"Request failed: {error.reason}"


def run_pattern(name: str, messages: list[dict], question: str):
    print(f"\n{'─' * 50}")
    print(f"Pattern: {name.upper()}")
    print(f"Messages in prompt: {len(messages)}")
    print(f"Question: {question}")
    response = call_model(messages, name)
    print(f"Response: {response}")


def main():
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the capital of Germany?"
    print(f"Comparing prompt patterns for: '{question}'")
    print("Set TOY_MODEL_API_KEY for real responses, or see mock outputs below.\n")

    run_pattern("zero_shot", build_zero_shot_prompt(question), question)
    run_pattern("few_shot", build_few_shot_prompt(question), question)
    run_pattern("cot", build_cot_prompt(question), question)
    run_pattern("structured", build_structured_prompt(question), question)

    print(f"\n{'─' * 50}")
    print("Key observations:")
    print("  zero_shot  — minimal tokens, works for simple factual tasks")
    print("  few_shot   — more tokens, higher format consistency")
    print("  cot        — shows reasoning, better for complex tasks")
    print("  structured — explicit schema, most predictable output shape")


if __name__ == "__main__":
    main()
