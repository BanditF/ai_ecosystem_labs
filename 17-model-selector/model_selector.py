#!/usr/bin/env python3
"""Lab 17: Model Selector
A decision tool for choosing the right LLM for your use case.
Scores models against your requirements and estimates cost.
"""
import sys
import json

# ── model catalog (prices in $ per 1M tokens, as of early 2025) ──
# Pricing last verified: early 2025. Verify at provider pricing pages before use.
MODELS = [
    {
        "name": "gpt-4o",
        "provider": "OpenAI",
        "context_k": 128,
        "input_cost": 2.50,
        "output_cost": 10.00,
        "speed": "medium",
        "capability": 9,
        "local": False,
        "strengths": ["general", "code", "reasoning", "vision"],
    },
    {
        "name": "gpt-4o-mini",
        "provider": "OpenAI",
        "context_k": 128,
        "input_cost": 0.15,
        "output_cost": 0.60,
        "speed": "fast",
        "capability": 7,
        "local": False,
        "strengths": ["general", "cost-efficient", "high-volume"],
    },
    {
        "name": "claude-3-5-sonnet",
        "provider": "Anthropic",
        "context_k": 200,
        "input_cost": 3.00,
        "output_cost": 15.00,
        "speed": "medium",
        "capability": 9,
        "local": False,
        "strengths": ["general", "code", "long-context", "writing"],
    },
    {
        "name": "claude-3-haiku",
        "provider": "Anthropic",
        "context_k": 200,
        "input_cost": 0.25,
        "output_cost": 1.25,
        "speed": "fast",
        "capability": 7,
        "local": False,
        "strengths": ["cost-efficient", "high-volume", "long-context"],
    },
    {
        "name": "llama-3.3-70b",
        "provider": "Local (Ollama)",
        "context_k": 128,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "speed": "medium",
        "capability": 8,
        "local": True,
        "strengths": ["private", "general", "code"],
    },
    {
        "name": "llama-3.2-3b",
        "provider": "Local (Ollama)",
        "context_k": 128,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "speed": "very-fast",
        "capability": 5,
        "local": True,
        "strengths": ["private", "fast", "low-resource"],
    },
    {
        "name": "gemini-1.5-pro",
        "provider": "Google",
        "context_k": 1000,
        "input_cost": 1.25,
        "output_cost": 5.00,
        "speed": "medium",
        "capability": 8,
        "local": False,
        "strengths": ["long-context", "general", "vision"],
    },
]


def score_model(model: dict, requirements: dict) -> float:
    score = 0.0

    # Hard constraint — filter out models below minimum context
    if model["context_k"] < requirements.get("min_context_k", 0):
        return 0.0

    # Privacy
    if requirements.get("private") and not model["local"]:
        return 0.0  # Hard requirement
    if requirements.get("private") and model["local"]:
        score += 3.0

    # Cost sensitivity
    cost_sensitivity = requirements.get("cost_sensitivity", "medium")
    monthly_cost = estimate_cost(model, requirements.get("monthly_tokens", 100_000))
    if cost_sensitivity == "high":
        score += max(0, 3.0 - monthly_cost / 10)
    elif cost_sensitivity == "medium":
        score += max(0, 2.0 - monthly_cost / 50)

    # Speed
    speed_needed = requirements.get("speed", "medium")
    speed_order = {"very-fast": 4, "fast": 3, "medium": 2, "slow": 1}
    if speed_order.get(model["speed"], 2) >= speed_order.get(speed_needed, 2):
        score += 1.5

    # Capability
    min_cap = requirements.get("min_capability", 5)
    if model["capability"] >= min_cap:
        score += model["capability"] * 0.3

    # Task strengths
    required_strengths = requirements.get("strengths", [])
    score += sum(1.0 for strength in required_strengths if strength in model["strengths"])

    return round(score, 2)


def estimate_cost(model: dict, monthly_tokens: int) -> float:
    if model["local"]:
        return 0.0
    # Assume 70% input, 30% output
    input_tokens = monthly_tokens * 0.7
    output_tokens = monthly_tokens * 0.3
    return (input_tokens * model["input_cost"] + output_tokens * model["output_cost"]) / 1_000_000


def main() -> None:
    # Default requirements — can be overridden via JSON arg
    requirements = {
        "min_context_k": 32,
        "private": False,
        "cost_sensitivity": "medium",
        "speed": "medium",
        "min_capability": 6,
        "monthly_tokens": 500_000,
        "strengths": ["general"],
    }

    if len(sys.argv) > 1:
        try:
            requirements.update(json.loads(sys.argv[1]))
        except json.JSONDecodeError:
            print("Usage: python3 model_selector.py '{\"private\": true, \"cost_sensitivity\": \"high\"}'")
            sys.exit(1)

    print("Model Selection Tool")
    print(f"Requirements: {json.dumps(requirements, indent=2)}\n")

    scored = [(model, score_model(model, requirements)) for model in MODELS]
    scored.sort(key=lambda item: item[1], reverse=True)

    print(f"{'Model':<22} {'Provider':<20} {'Score':>6} {'Est. $/mo':>10} {'Context':>9}")
    print("─" * 72)
    for model, score in scored:
        if score == 0:
            continue
        cost = estimate_cost(model, requirements["monthly_tokens"])
        cost_str = "free" if cost == 0 else f"${cost:.2f}"
        print(f"{model['name']:<22} {model['provider']:<20} {score:>6} {cost_str:>10} {model['context_k']:>7}K")

    if scored and scored[0][1] > 0:
        best = scored[0][0]
        print(f"\nRecommendation: {best['name']} ({best['provider']})")
        print(f"Strengths: {', '.join(best['strengths'])}")
        print("\nNote: prices change — verify at provider pricing pages before budgeting.")


if __name__ == "__main__":
    main()
