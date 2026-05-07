#!/usr/bin/env python3
"""Lab 18: Fine-tune Dataset Preparation
Prepare, validate, and analyze an instruction fine-tuning dataset.
No GPU required — this covers the data pipeline, not the training run.
"""
import json
import sys
import random
from pathlib import Path

# ── sample raw data ───────────────────────────────────────────
RAW_EXAMPLES = [
    ("What is the capital of France?", "Paris."),
    ("What is the capital of Germany?", "Berlin."),
    ("What is the capital of Japan?", "Tokyo."),
    ("What is the capital of Brazil?", "Brasília."),
    ("What is the capital of Australia?", "Canberra."),
    ("What is 2 + 2?", "4."),
    ("What is 10 * 7?", "70."),
    ("What color is the sky?", "Blue."),
    ("How many days are in a week?", "7."),
    ("What is the largest planet in our solar system?", "Jupiter."),
]

SYSTEM_PROMPT = "You are a concise, factual assistant. Answer questions briefly and accurately."


# ── format conversion ─────────────────────────────────────────
def to_openai_format(user: str, assistant: str, system: str = SYSTEM_PROMPT) -> dict:
    """Convert a Q/A pair to OpenAI fine-tuning JSONL format."""
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def to_alpaca_format(instruction: str, output: str, input_text: str = "") -> dict:
    """Convert to Alpaca format (used by many open-source fine-tuning tools)."""
    return {"instruction": instruction, "input": input_text, "output": output}


# ── validation ────────────────────────────────────────────────
def validate_openai_example(example: dict) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors = []
    if "messages" not in example:
        errors.append("Missing 'messages' key")
        return errors
    messages = example["messages"]
    if not isinstance(messages, list) or len(messages) < 2:
        errors.append("'messages' must be a list with at least 2 items")
        return errors
    roles = [m.get("role") for m in messages]
    if "user" not in roles:
        errors.append("No user turn found")
    if "assistant" not in roles:
        errors.append("No assistant turn found")
    for i, msg in enumerate(messages):
        if not msg.get("content", "").strip():
            errors.append(f"Empty content in message {i}")
    return errors


def validate_dataset(examples: list[dict]) -> dict:
    """Validate all examples and return stats."""
    errors = []
    for i, ex in enumerate(examples):
        errs = validate_openai_example(ex)
        if errs:
            errors.append({"index": i, "errors": errs})

    token_counts = []
    for ex in examples:
        messages = ex.get("messages")
        if not isinstance(messages, list):
            continue
        token_counts.append(
            sum(len(str(m.get("content", "")).split()) for m in messages if isinstance(m, dict))
        )

    return {
        "total": len(examples),
        "valid": len(examples) - len(errors),
        "invalid": len(errors),
        "errors": errors,
        "avg_tokens_approx": sum(token_counts) // len(token_counts) if token_counts else 0,
        "max_tokens_approx": max(token_counts) if token_counts else 0,
    }


# ── train/val split ───────────────────────────────────────────
def split_dataset(examples: list[dict], val_ratio: float = 0.15) -> tuple[list, list]:
    shuffled = examples.copy()
    random.shuffle(shuffled)
    split = max(1, int(len(shuffled) * (1 - val_ratio)))
    return shuffled[:split], shuffled[split:]


def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("18-finetune-prep/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert raw examples
    examples = [to_openai_format(q, a) for q, a in RAW_EXAMPLES]
    print(f"Prepared {len(examples)} examples\n")

    # Validate
    stats = validate_dataset(examples)
    print("Validation:")
    print(f"  Valid: {stats['valid']}/{stats['total']}")
    print(f"  Avg tokens (approx): {stats['avg_tokens_approx']}")
    print(f"  Max tokens (approx): {stats['max_tokens_approx']}")
    if stats["errors"]:
        print(f"  Errors: {stats['errors']}")
    print()

    # Split
    train, val = split_dataset(examples)
    print(f"Split: {len(train)} train / {len(val)} validation\n")

    # Write JSONL files
    train_path = output_dir / "train.jsonl"
    val_path = output_dir / "val.jsonl"

    with open(train_path, "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")

    with open(val_path, "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")

    print("Output:")
    print(f"  {train_path} ({len(train)} examples)")
    print(f"  {val_path} ({len(val)} examples)")

    # Show a sample
    print("\nSample training example:")
    print(json.dumps(train[0], indent=2))

    # Also write Alpaca format for comparison
    alpaca = [to_alpaca_format(q, a) for q, a in RAW_EXAMPLES]
    alpaca_path = output_dir / "alpaca_format.jsonl"
    with open(alpaca_path, "w") as f:
        for ex in alpaca:
            f.write(json.dumps(ex) + "\n")
    print(f"\nAlso wrote Alpaca format: {alpaca_path}")


if __name__ == "__main__":
    main()
