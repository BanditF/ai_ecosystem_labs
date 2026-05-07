# Lab 14: Prompt Patterns

This lab demonstrates how prompt structure changes model behavior.

It compares four common patterns side by side:
- zero-shot
- few-shot
- chain-of-thought
- structured output prompting

## Run it

```bash
cd ai_ecosystem_labs
python3 14-prompt-patterns/prompt_patterns.py "What is the capital of Germany?"
```

If `TOY_MODEL_API_KEY` is set, the script makes a real chat completions call using the prompt messages it builds. Otherwise it stays in mock mode, prints each prompt structure, and shows expected demo outputs.
