"""
Lab 03b: Real MCP Server
========================
A minimal MCP server using the official Python SDK (https://github.com/modelcontextprotocol/python-sdk).

Install:
    pip install mcp

Run (standalone test):
    python server.py

Inspect (browser UI):
    pip install "mcp[cli]"
    mcp dev server.py

Wire to Claude Desktop (~/.../claude_desktop_config.json):
    {
      "mcpServers": {
        "word-counter": {
          "command": "python",
          "args": ["/absolute/path/to/server.py"]
        }
      }
    }

Wire to Cursor (Settings → MCP):
    {
      "name": "word-counter",
      "command": "python /absolute/path/to/server.py"
    }
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("word-counter")


@mcp.tool()
def count_words(text: str) -> str:
    """Count the number of words in a string.

    Use this when the user wants to know how many words are in a piece of text.
    Returns a plain-English sentence with the count.
    """
    count = len(text.split())
    return f"{count} words"


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the characters in a string.

    Use this when the user wants to see text reversed.
    """
    return text[::-1]


if __name__ == "__main__":
    mcp.run()
