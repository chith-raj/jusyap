#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="$HOME/.jusyap/config.json"
MODE="${1:-}"

if [[ "$MODE" != "light" && "$MODE" != "polish" ]]; then
  echo "Usage: $0 light|polish"
  exit 2
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found: $CONFIG_PATH"
  echo "Run ./scripts/setup.sh first."
  exit 1
fi

python3 - "$CONFIG_PATH" "$MODE" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
mode = sys.argv[2]
config = json.loads(config_path.read_text())

config.setdefault("whisper", {})["model"] = "tiny.en"
rewriter = config.setdefault("rewriter", {})

if mode == "light":
    rewriter["provider"] = "none"
else:
    rewriter["provider"] = "ollama"
    rewriter["model"] = "llama3.2:1b"

config_path.write_text(json.dumps(config, indent=2) + "\n")
PY

if [[ "$MODE" == "light" ]]; then
  echo "Mode set to light: tiny.en transcription, no rewriting."
else
  echo "Mode set to polish: tiny.en transcription, Ollama llama3.2:1b rewriting."
fi
