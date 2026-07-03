from __future__ import annotations

import argparse
import fcntl
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict

from pynput import keyboard

from .audio import Recorder
from .config import default_config_path, load_config, write_default_config
from .paste import paste_text
from .rewrite import Rewriter
from .transcribe import Transcriber

_LOCK_FILE = None


class DictationApp:
    def __init__(self, config: Dict[str, Any], print_only: bool = False):
        self.config = config
        self.print_only = print_only
        recording_config = config["recording"]
        self.recorder = Recorder(
            sample_rate=int(recording_config["sample_rate"]),
            channels=int(recording_config["channels"]),
            device=recording_config.get("device"),
        )
        self.transcriber = Transcriber(config["whisper"])
        self.rewriter = Rewriter(config["rewriter"])
        self._processing_lock = threading.Lock()

    def toggle_recording(self) -> None:
        if self.recorder.is_recording():
            self.stop_recording()
            return

        self.start_recording("Press the hotkey again to stop.")

    def start_recording(self, stop_hint: str) -> None:
        if self.recorder.is_recording():
            return

        if self._processing_lock.locked():
            print("Still processing the previous dictation.", flush=True)
            return

        print(f"Recording. {stop_hint}", flush=True)
        self.recorder.start()

    def stop_recording(self) -> None:
        if not self.recorder.is_recording():
            return

        print("Stopping recording...", flush=True)
        audio_path = self.recorder.stop_to_wav()
        threading.Thread(
            target=self._process_audio, args=(audio_path,), daemon=True
        ).start()

    def record_once_until_enter(self) -> None:
        print("Recording. Press Enter to stop.", flush=True)
        self.recorder.start()
        input()
        audio_path = self.recorder.stop_to_wav()
        self._process_audio(audio_path)

    def _process_audio(self, audio_path: Path) -> None:
        with self._processing_lock:
            try:
                print("Transcribing...", flush=True)
                transcript = self.transcriber.transcribe(audio_path)
                if not transcript:
                    print("No speech detected.", flush=True)
                    return

                print(f"Transcript: {transcript}", flush=True)
                if self.config["rewriter"].get("provider") == "none":
                    print("Using transcript without rewriting.", flush=True)
                else:
                    print("Polishing...", flush=True)
                final_text = self.rewriter.rewrite(transcript)
                print(f"Final: {final_text}", flush=True)

                if self.print_only:
                    return

                paste_text(final_text, self.config["paste"])
                print("Inserted into the active field.", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"Error: {exc}", file=sys.stderr, flush=True)
            finally:
                try:
                    audio_path.unlink(missing_ok=True)
                except OSError:
                    pass


def run_hotkey_daemon(app: DictationApp, hotkey: str) -> None:
    parsed_hotkey = keyboard.HotKey(
        keyboard.HotKey.parse(hotkey),
        app.toggle_recording,
    )

    def on_press(key):  # noqa: ANN001
        parsed_hotkey.press(listener.canonical(key))

    def on_release(key):  # noqa: ANN001
        parsed_hotkey.release(listener.canonical(key))

    print(f"Listening for hotkey: {hotkey}", flush=True)
    print("Keep this terminal open, or install the LaunchAgent from scripts/.", flush=True)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        threading.Event().wait()


def run_hold_key_daemon(app: DictationApp, hold_key: str) -> None:
    parsed_keys = keyboard.HotKey.parse(hold_key)
    if len(parsed_keys) != 1:
        raise ValueError(f"Hold trigger must be a single key: {hold_key}")

    target_key = parsed_keys[0]
    pressed = False
    press_lock = threading.Lock()

    def matches_target(key):  # noqa: ANN001
        if key == target_key:
            return True
        if target_key == keyboard.Key.alt:
            return key == keyboard.Key.alt_r
        return False

    def on_press(key):  # noqa: ANN001
        nonlocal pressed
        canonical_key = listener.canonical(key)
        if not matches_target(canonical_key):
            return
        with press_lock:
            if pressed:
                return
            pressed = True
        app.start_recording("Release Option to stop.")

    def on_release(key):  # noqa: ANN001
        nonlocal pressed
        canonical_key = listener.canonical(key)
        if not matches_target(canonical_key):
            return
        with press_lock:
            if not pressed:
                return
            pressed = False
        app.stop_recording()

    print(f"Listening for hold key: {hold_key}", flush=True)
    print("Hold Option to record. Release Option to stop.", flush=True)
    print("Keep this terminal open, or install the LaunchAgent from scripts/.", flush=True)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        threading.Event().wait()


def run_trigger_daemon(app: DictationApp, config: Dict[str, Any]) -> None:
    trigger = config.get("trigger", {})
    mode = trigger.get("mode", "hotkey")

    if mode == "hold":
        run_hold_key_daemon(app, trigger.get("key", "<alt>"))
    elif mode == "hotkey":
        run_hotkey_daemon(app, trigger.get("key", config["hotkey"]))
    else:
        raise ValueError(f"Unsupported trigger mode: {mode}")


def debug_keys() -> None:
    print("Key debug mode. Press keys to verify macOS is delivering events.", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    def on_press(key):  # noqa: ANN001
        print(f"press: {key!r}", flush=True)

    def on_release(key):  # noqa: ANN001
        print(f"release: {key!r}", flush=True)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="JusYap: local dictation, Whisper transcription, local rewrite, and paste."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="Path to config JSON.",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create the default config and exit.",
    )
    parser.add_argument(
        "--overwrite-config",
        action="store_true",
        help="Overwrite the config when used with --init-config.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Record immediately and stop when Enter is pressed.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print final text instead of pasting.",
    )
    parser.add_argument(
        "--debug-keys",
        action="store_true",
        help="Print global key events to verify macOS keyboard permissions.",
    )
    return parser


def acquire_single_instance_lock() -> bool:
    global _LOCK_FILE

    state_dir = Path.home() / "Library" / "Application Support" / "JusYap"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "jusyap.lock"
    _LOCK_FILE = lock_path.open("w", encoding="utf-8")

    try:
        fcntl.flock(_LOCK_FILE, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("JusYap is already running.", flush=True)
        return False

    _LOCK_FILE.write(f"{os.getpid()}\n")
    _LOCK_FILE.flush()
    return True


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.init_config:
        path = write_default_config(args.config, overwrite=args.overwrite_config)
        print(f"Config ready: {path}")
        return 0

    if args.debug_keys:
        debug_keys()
        return 0

    if not acquire_single_instance_lock():
        return 0

    config = load_config(args.config)
    app = DictationApp(config, print_only=args.print_only)

    if args.once:
        app.record_once_until_enter()
    else:
        run_trigger_daemon(app, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
