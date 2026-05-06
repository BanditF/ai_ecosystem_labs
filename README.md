# AI Ecosystem Labs

Runnable lab files for the [AI Tooling Field Guide](https://github.com/BanditF/education).

Each lab is a deliberately small Python script that builds one piece of the AI tooling stack — model access, CLI wrappers, protocol adapters, agents, governance, and more. The goal is not polished software. It is a clear, inspectable artifact that makes one concept concrete.

## Labs

| Lab | Concept |
|-----|---------|
| [00-model-access](00-model-access/) | Toy model surface — endpoint, API key, structured response |
| [01-cli](01-cli/) | Minimal CLI wrapper around a model call |
| [02-json-wrapper](02-json-wrapper/) | Structured output and response parsing |
| [03-protocol-adapter](03-protocol-adapter/) | Protocol adapter shape — tools, resources, prompts |
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

## Setup

No external dependencies required for most labs — they use a toy model backend so you can run them without an API key. Labs 12 and 13 have their own notes.

```bash
python3 00-model-access/model_cli.py "hello"
```

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