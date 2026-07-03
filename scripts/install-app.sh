#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SUPPORT="$HOME/Library/Application Support/JusYap"
RUNTIME_DIR="$APP_SUPPORT/runtime"
APP_DEST_DIR="$HOME/Applications"
APP_DEST="$APP_DEST_DIR/JusYap.app"
LOG_DIR="$HOME/Library/Logs/jusyap"

mkdir -p "$APP_SUPPORT" "$APP_DEST_DIR" "$LOG_DIR"

rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"

rsync -a \
  --exclude 'JusYap.app' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  "$SOURCE_DIR/" "$RUNTIME_DIR/"

rm -rf "$APP_DEST"
cp -R "$SOURCE_DIR/JusYap.app" "$APP_DEST"
chmod +x "$APP_DEST/Contents/MacOS/JusYap"

echo "Installed JusYap app: $APP_DEST"
echo "Installed JusYap runtime: $RUNTIME_DIR"
echo
echo "Open it with:"
echo "  open \"$APP_DEST\""
