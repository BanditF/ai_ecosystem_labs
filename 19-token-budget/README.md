# Lab 19: Token Budget

Count tokens, compare approximate request cost across providers, and project monthly spend.

## Run

```bash
python3 19-token-budget/token_budget.py
```

Optional for exact OpenAI counts:

```bash
pip install tiktoken
python3 19-token-budget/token_budget.py
```

## What it shows

- approximate token counting with a simple word-based fallback
- exact OpenAI counts when `tiktoken` is installed
- per-model input, output, and total cost estimates
- context window usage percentage
- monthly cost projections at a given call volume
