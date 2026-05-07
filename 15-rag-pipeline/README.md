# Lab 15: RAG Pipeline

A minimal retrieval-augmented generation pipeline in pure Python.

## Run it

```bash
python3 15-rag-pipeline/rag_pipeline.py "Who created Python?"
```

No external dependencies are required.

## What it shows

- a tiny sample document corpus
- simple chunking by overlapping word windows
- TF-IDF-like retrieval with no embedding server
- prompt augmentation with source IDs
- a mocked generation step you can later swap for a real LLM call

## Good experiments

1. Try different queries and watch which docs are retrieved.
2. Add two new documents to `DOCUMENTS` and rerun the script.
3. Change `top_k` from `3` to `1` and compare the answer quality.
