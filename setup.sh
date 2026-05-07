#!/bin/bash
# One-command setup for ai_ecosystem_labs
# Most labs run with stdlib Python only.
# This installs optional dependencies for labs that need them.

set -e

python3 --version || { echo "Python 3 is required. Install from https://python.org"; exit 1; }
echo "Python OK"

echo "Installing optional lab dependencies..."
pip install "mcp[cli]" 2>/dev/null && echo "mcp installed (needed for lab 03b)" || echo "mcp install skipped (lab 03b won't run without it)"

echo ""
echo "Setup complete. Try: python3 00-model-access/model_cli.py hello"
