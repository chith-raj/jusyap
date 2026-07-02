from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "<cmd>+<shift>+d",
    "recording": {
        "sample_rate": 16000,
        "channels": 1,
        "device": None,
    },
    "whisper": {
        "model": "tiny.en",
        "device": "auto",
        "compute_type": "int8",
        "language": "en",
    },
    "rewriter": {
        "provider": "none",
        "model": "llama3.2:1b",
        "ollama_url": "http://127.0.0.1:11434/api/generate",
        "timeout_seconds": 90,
        "style": "polished, concise, and well structured",
        "preserve_intent": True,
    },
    "paste": {
        "enabled": True,
        "restore_clipboard": False,
        "paste_delay_seconds": 0.1,
    },
}


def default_config_path() -> Path:
    return Path.home() / ".yapr" / "config.json"


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path | None = None) -> Dict[str, Any]:
    config_path = path or default_config_path()
    if not config_path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        user_config = json.load(file)

    if not isinstance(user_config, dict):
        raise ValueError(f"Config must be a JSON object: {config_path}")

    return deep_merge(DEFAULT_CONFIG, user_config)


def write_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists() and not overwrite:
        return config_path

    with config_path.open("w", encoding="utf-8") as file:
        json.dump(DEFAULT_CONFIG, file, indent=2)
        file.write("\n")

    return config_path
