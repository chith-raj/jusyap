#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PROJECT_DIR/Yapr.app"

mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
chmod +x "$APP_DIR/Contents/MacOS/Yapr"

echo "Yapr app ready: $APP_DIR"
echo "You can open it from Finder, Spotlight, or with: open \"$APP_DIR\""
