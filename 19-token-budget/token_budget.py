#!/usr/bin/env python3
"""Lab 19: Token Budget.

Count tokens, estimate costs across providers, and track context window usage.
Uses word-based approximation by default; uses tiktoken if installed.
"""

from typing import Dict, List


PROVIDERS: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00, "context_k": 128},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context_k": 128},
    "gpt-4o-mini-batch": {"input": 0.075, "output": 0.30, "context_k": 128},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "context_k": 200},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "context_k": 200},
    "o1": {"input": 15.00, "output": 60.00, "context_k": 200},
    "o1-mini": {"input": 1.10, "output": 4.40, "context_k": 128},
}


def count_tokens_approx(text: str) -> int:
    """Word-based approximation: ~1.3 tokens per word for English."""
    words = len(text.split())
    return max(1, int(words * 1.3))


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens using tiktoken if available, else approximation."""
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return count_tokens_approx(text)


def count_messages(messages: List[dict], model: str = "gpt-4o") -> dict:
    """Count tokens in a chat-style messages array."""
    total_input = 0
    for message in messages:
        content = str(message.get("content", ""))
        total_input += count_tokens(content, model)
        total_input += 4
    return {"input_tokens": total_input}


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> dict:
    """Estimate request cost and context usage for one model."""
    if model not in PROVIDERS:
        return {"error": f"Unknown model: {model}"}

    pricing = PROVIDERS[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    context_used_pct = round(
        100 * (input_tokens + output_tokens) / (pricing["context_k"] * 1000), 1
    )
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(input_cost + output_cost, 6),
        "context_window_k": int(pricing["context_k"]),
        "context_used_pct": context_used_pct,
    }


def compare_all_models(input_tokens: int, output_tokens: int) -> None:
    """Print a lowest-to-highest cost comparison across all configured models."""
    results = [estimate_cost(input_tokens, output_tokens, model) for model in PROVIDERS]
    results.sort(key=lambda result: result.get("total_cost_usd", 999))

    print(
        f"\nCost comparison for {input_tokens:,} input + {output_tokens:,} output tokens:"
    )
    print(f"{'Model':<25} {'Total cost':>12} {'Input cost':>12} {'Output cost':>12}")
    print("─" * 65)
    for result in results:
        if "error" not in result:
            print(
                f"{result['model']:<25} "
                f"${result['total_cost_usd']:>11.5f} "
                f"${result['input_cost_usd']:>11.5f} "
                f"${result['output_cost_usd']:>11.5f}"
            )


def monthly_projection(
    input_tokens: int, output_tokens: int, calls_per_day: int, model: str
) -> None:
    """Print a simple monthly cost projection."""
    single_call = estimate_cost(input_tokens, output_tokens, model)
    if "error" in single_call:
        print(single_call["error"])
        return

    monthly_calls = calls_per_day * 30
    monthly_cost = single_call["total_cost_usd"] * monthly_calls
    print(f"\nMonthly projection ({model}, {calls_per_day} calls/day):")
    print(f"  Calls per month: {monthly_calls:,}")
    print(f"  Cost per call: ${single_call['total_cost_usd']:.6f}")
    print(f"  Monthly estimate: ${monthly_cost:.2f}")


def main() -> None:
    sample_system = "You are a helpful assistant that answers questions concisely."
    sample_user = "Explain the difference between RAG and fine-tuning in simple terms."
    sample_output = (
        "RAG retrieves relevant documents at runtime and injects them into the prompt. "
        "Fine-tuning updates model weights with new training data. RAG is better for "
        "dynamic knowledge, fine-tuning for consistent behavior."
    )

    print("Token Budget Tool")
    print("─" * 50)

    input_tokens = count_tokens(sample_system + "\n" + sample_user)
    output_tokens = count_tokens(sample_output)

    try:
        import tiktoken  # noqa: F401

        method = "tiktoken (exact)"
    except ImportError:
        method = "word approximation (install tiktoken for exact counts)"

    print(f"\nToken counting method: {method}")
    print(f"Sample system+user: {input_tokens} input tokens")
    print(f"Sample response: {output_tokens} output tokens")

    compare_all_models(input_tokens, output_tokens)
    monthly_projection(input_tokens, output_tokens, calls_per_day=1000, model="gpt-4o")
    monthly_projection(
        input_tokens, output_tokens, calls_per_day=1000, model="gpt-4o-mini"
    )

    print("\nTip: pip install tiktoken for exact OpenAI token counts")


if __name__ == "__main__":
    main()
