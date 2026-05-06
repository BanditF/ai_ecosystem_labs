#!/usr/bin/env bash
set -euo pipefail
# Lightweight CI loop for tool governance: rerun eval_runner.py whenever saved calls change.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/eval_runner.py" "$@"
