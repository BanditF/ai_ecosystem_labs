# Lab 03b: Real MCP Server

Uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) to build a minimal server with two tools, then wire it to a real host.

## Setup

```bash
pip install mcp
python server.py
```

## Inspect without a host

```bash
pip install "mcp[cli]"
mcp dev server.py
```

## Wire to a host

See the [Lab 03b page](https://banditf.github.io/education/docs/labs/03b-real-mcp.html) for host-specific config snippets (Claude Desktop, Cursor).

## Tools exposed

- `count_words(text)` — returns word count
- `reverse_text(text)` — returns reversed string
