# Lab 17: Model Selector

A small decision helper for picking a model based on context window, cost, speed, privacy, and capability.

This lab uses static model metadata, so you do not need an API key.

## Run

```bash
python3 model_selector.py
python3 model_selector.py '{"private": true, "cost_sensitivity": "high"}'
```

## What it does

- scores each model against a requirements profile
- estimates monthly token cost for hosted models
- filters to local models when privacy is a hard requirement
- prints a ranked recommendation table

## Try changing it

- raise or lower a model's `capability` score
- change `monthly_tokens` to see cost move
- add or remove values in `strengths`

For the walk-through, see the Lab 17 page in the Field Guide.
