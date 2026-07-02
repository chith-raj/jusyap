#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

python3 -m venv .venv
".venv/bin/python" -m pip install --upgrade pip
".venv/bin/pip" install -r requirements.txt
".venv/bin/python" -m dictation_polisher.app --init-config
chmod +x "$PROJECT_DIR/yapr"
chmod +x "$PROJECT_DIR/Yapr.app/Contents/MacOS/Yapr"
chmod +x "$PROJECT_DIR/scripts/create-app.sh"
chmod +x "$PROJECT_DIR/scripts/install-app.sh"
chmod +x "$PROJECT_DIR/scripts/generate-icon.py"

cat <<'MSG'

Setup complete.

Next:
1. Start Yapr: ./yapr
2. To enable local polishing later, install Ollama and run: ollama pull llama3.2:1b
3. Switch polishing on with: ./scripts/set-mode.sh polish

macOS may ask for Microphone, Accessibility, and Input Monitoring permissions.
MSG
