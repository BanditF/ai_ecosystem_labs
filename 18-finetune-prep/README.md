# Lab 18: Fine-tune Dataset Prep

Prepare, validate, and analyze a small instruction fine-tuning dataset.

## Run

```bash
python3 18-finetune-prep/finetune_prep.py
```

## What it does

- converts raw Q/A pairs into OpenAI fine-tuning JSONL format
- validates the dataset shape
- creates a train/validation split
- writes OpenAI JSONL and Alpaca-format outputs

## Output

By default the script writes:

- `18-finetune-prep/output/train.jsonl`
- `18-finetune-prep/output/val.jsonl`
- `18-finetune-prep/output/alpaca_format.jsonl`

No GPU is required. This lab is about the dataset pipeline, not the training run.
