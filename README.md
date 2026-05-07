# AI Ecosystem Labs

Runnable lab files for the [AI Tooling Field Guide](https://github.com/BanditF/education).

Each lab is a deliberately small Python script that builds one piece of the AI tooling stack — model access, CLI wrappers, protocol adapters, agents, governance, and more. The goal is not polished software. It is a clear, inspectable artifact that makes one concept concrete.

## Quick start

```bash
git clone https://github.com/BanditF/ai_ecosystem_labs.git
cd ai_ecosystem_labs
python3 run_all.py
```

**Python 3.9+ required.** Most labs run with no extra packages. One lab (03b) needs `pip install "mcp[cli]"`.

To run a single lab:

```bash
python3 00-model-access/model_cli.py hello
```

To install optional dependencies:

```bash
bash setup.sh
```

## Labs

| Lab | Concept |
|-----|---------|
| [00-model-access](00-model-access/) | Toy model surface — endpoint, API key, structured response |
| [01-cli](01-cli/) | Minimal CLI wrapper around a model call |
| [02-json-wrapper](02-json-wrapper/) | Structured output and response parsing |
| [03-protocol-adapter](03-protocol-adapter/) | Protocol adapter shape — tools, resources, prompts |
| [03b-real-mcp](03b-real-mcp/) | Real MCP server with the official Python SDK* |
| [04-skill](04-skill/) | Skill: reusable packaged behavior for a host |
| [05-hook](05-hook/) | Hook: intercept and modify host behavior |
| [06-agent-loop](06-agent-loop/) | The observe → decide → act → evaluate loop |
| [07-task-graph](07-task-graph/) | Multi-step task decomposition |
| [08-coordinator](08-coordinator/) | Coordinator pattern — routing across agents |
| [09-host-cli](09-host-cli/) | A minimal host CLI that connects the pieces |
| [10-governance](10-governance/) | Approvals, audit logs, policy checks |
| [11-capstone](11-capstone/) | Full small stack end to end |
| [12-persistent-platform](12-persistent-platform/) | State persistence across agent runs |
| [13-local-broker](13-local-broker/) | Local credential broker for API keys |
| [14-prompt-patterns](14-prompt-patterns/) | Zero-shot, few-shot, chain-of-thought, and structured output prompting |
| [15-rag-pipeline](15-rag-pipeline/) | Retrieval-augmented generation pipeline in pure Python |
| [16-eval-suite](16-eval-suite/) | Systematic eval runner with assertions, scoring, and filtering |
| [17-model-selector](17-model-selector/) | Model comparison by cost, speed, privacy, and fit |
| [18-finetune-prep](18-finetune-prep/) | Fine-tuning dataset preparation and validation |
| [19-token-budget](19-token-budget/) | Token counting, cost comparison, and spend projection |

* `03b-real-mcp` needs the optional `mcp[cli]` package.

## Setup notes

Most labs use only the Python standard library. Labs 12 and 13 write local state, and lab 13 starts a local server during the exercise.

Run all labs in sequence:

```bash
python3 run_all.py
```

Reset state between runs:

```bash
python3 reset.py
```

## Philosophy

These labs are practice pieces, not production code. Read them, run them, and change them. The point is to make the invisible boundaries between layers visible — what a protocol adapter actually does, what an agent loop actually looks like, where governance hooks actually sit.

The companion site explains the concepts. The labs make them tangible.
