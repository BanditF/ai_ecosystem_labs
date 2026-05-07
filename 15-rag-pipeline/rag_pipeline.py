#!/usr/bin/env python3
"""Lab 15: RAG Pipeline
A minimal retrieval-augmented generation pipeline in pure Python.
Uses TF-IDF term frequency for retrieval (no external deps required).
"""
import math
import re
from collections import Counter

# ── sample document corpus ──────────────────────────────────
DOCUMENTS = [
    {"id": "doc1", "text": "Python is a high-level programming language known for its clear syntax and readability. It was created by Guido van Rossum and first released in 1991."},
    {"id": "doc2", "text": "Python supports multiple programming paradigms including procedural, object-oriented, and functional programming."},
    {"id": "doc3", "text": "The Python Package Index (PyPI) hosts thousands of third-party modules. pip is the standard package manager for Python."},
    {"id": "doc4", "text": "Python is widely used in data science, machine learning, web development, and automation. Libraries like NumPy, pandas, and scikit-learn are popular."},
    {"id": "doc5", "text": "JavaScript is a scripting language primarily used for web development. It runs in browsers and on servers via Node.js."},
    {"id": "doc6", "text": "Rust is a systems programming language focused on safety, speed, and concurrency. It prevents memory safety bugs at compile time."},
]

# ── chunking ──────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 100, overlap: int = 20) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

# ── TF-IDF retrieval ──────────────────────────────────────────
def tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())

def build_index(docs: list[dict]) -> dict:
    index = {}
    for doc in docs:
        tokens = tokenize(doc["text"])
        tf = Counter(tokens)
        total = len(tokens)
        index[doc["id"]] = {
            "text": doc["text"],
            "tf": {t: c / total for t, c in tf.items()},
            "tokens": set(tokens),
        }
    return index

def idf(term: str, index: dict) -> float:
    n_docs = len(index)
    n_with_term = sum(1 for d in index.values() if term in d["tokens"])
    return math.log((n_docs + 1) / (n_with_term + 1)) + 1

def score(query: str, index: dict) -> list[tuple[str, float]]:
    query_tokens = tokenize(query)
    scores = {}
    for doc_id, doc in index.items():
        s = sum(doc["tf"].get(t, 0) * idf(t, index) for t in query_tokens)
        scores[doc_id] = s
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def retrieve(query: str, index: dict, top_k: int = 3) -> list[dict]:
    ranked = score(query, index)
    results = []
    for doc_id, score_val in ranked[:top_k]:
        if score_val > 0:
            results.append({"id": doc_id, "text": index[doc_id]["text"], "score": round(score_val, 4)})
    return results

# ── augmented prompt ──────────────────────────────────────────
def build_augmented_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
    return f"""Answer the question using only the provided context. Cite the source ID.

Context:
{context}

Question: {query}
Answer:"""

def mock_generate(prompt: str, query: str) -> str:
    """Simulate generation — real implementation would call an LLM API."""
    if "python" in query.lower() and "created" in query.lower():
        return "Python was created by Guido van Rossum and first released in 1991. [doc1]"
    if "package" in query.lower() or "pip" in query.lower():
        return "pip is the standard package manager for Python. Packages are hosted on PyPI. [doc3]"
    return "[Mock] Based on the retrieved context, here is the answer to your question."

def main():
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Who created Python and when?"

    print(f"Query: {query}\n")

    # Index
    index = build_index(DOCUMENTS)
    print(f"Indexed {len(DOCUMENTS)} documents\n")

    # Retrieve
    results = retrieve(query, index, top_k=3)
    print("Top retrieved chunks:")
    for r in results:
        print(f"  [{r['id']}] score={r['score']}  {r['text'][:80]}...")

    # Augment
    prompt = build_augmented_prompt(query, results)
    print(f"\nAugmented prompt ({len(prompt)} chars):")
    print("─" * 40)
    print(prompt)
    print("─" * 40)

    # Generate
    answer = mock_generate(prompt, query)
    print(f"\nGenerated answer:\n{answer}")
    print("\nSet TOY_MODEL_API_KEY to connect a real LLM for generation.")

if __name__ == "__main__":
    main()
