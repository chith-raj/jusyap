# JusYap

JusYap is a local macOS dictation tool for turning your free-form yapping into usable text. Press a shortcut, speak naturally, and JusYap inserts the transcribed text into the active input field. You can keep it lightweight with local Whisper transcription only, or enable local Ollama rewriting for polished text.

```text
Default shortcut: Command + Shift + D
```

## What It Does

- Records your voice with a global hotkey.
- Transcribes locally with `faster-whisper`.
- Optionally rewrites locally with Ollama.
- Pastes into the active browser form, editor, chat box, document, or note.
- Runs without a cloud API.
- Can run from Terminal or as a macOS app launcher.

## Quick Start

Follow this path if you are setting up JusYap for the first time:

```text
[ ] Clone the repo
[ ] Run setup
[ ] Start JusYap
[ ] Approve macOS permissions
[ ] Press Command + Shift + D inside any text field
```

### 1. Clone The Repo

```bash
git clone https://github.com/chith-raj/jusyap.git
cd jusyap
```

### 2. Run Setup

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This creates a Python virtual environment, installs dependencies, and creates:

```text
~/.jusyap/config.json
```

### 3. Start JusYap

```bash
./jusyap
```

You should see:

```text
Listening for hotkey: <cmd>+<shift>+d
```

### 4. Dictate

1. Click any text field.
2. Press `Command + Shift + D`.
3. Speak.
4. Press `Command + Shift + D` again.
5. JusYap transcribes and inserts the final text.

## Choose A Mode

JusYap starts in lightweight mode by default.

| Mode | Best For | Local Model Load | Command |
| --- | --- | --- | --- |
| Light | Fast transcription while working | Low | `./scripts/set-mode.sh light` |
| Polish | Cleaner rewritten text | Higher | `./scripts/set-mode.sh polish` |

### Light Mode

Use this when you want minimal system impact.

```bash
./scripts/set-mode.sh light
```

Light mode uses:

```text
Whisper: tiny.en
Rewriting: disabled
```

### Polish Mode

Use this when you want JusYap to clean up grammar and structure.

First install Ollama from:

```text
https://ollama.com
```

Then pull a small local model:

```bash
ollama pull llama3.2:1b
```

Enable polishing:

```bash
./scripts/set-mode.sh polish
```

When polishing is enabled, Ollama must be running.

## Launch Without Terminal

If you do not want to run `./jusyap` manually every time, install the app launcher:

```bash
./scripts/install-app.sh
```

Then open:

```text
~/Applications/JusYap.app
```

You can drag `JusYap.app` to the Dock.

If macOS blocks the app from reading files in a protected folder like `Documents`, use the installed app from `~/Applications`.

## Start On Login

Install the LaunchAgent:

```bash
chmod +x scripts/install-launch-agent.sh scripts/uninstall-launch-agent.sh
./scripts/install-launch-agent.sh
```

Remove it later:

```bash
./scripts/uninstall-launch-agent.sh
```

Logs are written to:

```text
~/Library/Logs/jusyap/
```

## macOS Permissions

JusYap needs a few macOS permissions.

| Permission | Why |
| --- | --- |
| Microphone | Records dictation |
| Accessibility | Pastes text into the active app |
| Input Monitoring | Receives the global hotkey |

Open:

```text
System Settings -> Privacy & Security
```

Then check:

```text
Microphone
Accessibility
Input Monitoring
```

Allow the app you use to launch JusYap:

- `Terminal`, `iTerm`, `Warp`, or `Visual Studio Code` if running from Terminal.
- `JusYap` if launching `JusYap.app`.

After changing permissions, quit and reopen the app or terminal.

## Test Commands

Record once, stop with Enter, and print output instead of pasting:

```bash
./jusyap --once --print-only
```

Check whether macOS is sending key events to JusYap:

```bash
./jusyap --debug-keys
```

Press a few keys. If nothing prints, check `Input Monitoring`.

## Customize

Edit:

```text
~/.jusyap/config.json
```

Common settings:

```json
{
  "hotkey": "<cmd>+<shift>+d",
  "whisper": {
    "model": "tiny.en"
  },
  "rewriter": {
    "provider": "none",
    "model": "llama3.2:1b",
    "style": "polished, concise, and well structured"
  },
  "paste": {
    "restore_clipboard": false
  }
}
```

Hotkey examples:

```text
<cmd>+<shift>+d
<ctrl>+<alt>+<space>
<ctrl>+<shift>+f12
```

Whisper model examples:

```text
tiny.en
base.en
small.en
medium.en
```

Smaller Whisper models are faster. Larger models are more accurate.

## Troubleshooting

### Hotkey Does Nothing

Run:

```bash
./jusyap --debug-keys
```

If no key events appear, enable `Input Monitoring` for your terminal or `JusYap.app`.

### Text Does Not Paste

Enable `Accessibility` permission for your terminal or `JusYap.app`.

### App Opens But Nothing Is Visible

JusYap is a background app. It does not show a window. Click into a text field and press:

```text
Command + Shift + D
```

### Polishing Does Not Work

Make sure Ollama is running and the model is installed:

```bash
ollama pull llama3.2:1b
./scripts/set-mode.sh polish
```

### Switch Back To Lightweight Mode

```bash
./scripts/set-mode.sh light
```

## Notes

- JusYap uses clipboard paste because it works across most macOS apps.
- The first transcription can take longer while Whisper downloads and caches the model.
- The default setup is intentionally lightweight for MacBook Air-class machines.
- Regenerate the app icon with `./scripts/generate-icon.py` if you edit the icon generator.
- This project was previously named VoiceInk and Yapr. It was renamed to JusYap to avoid confusion with existing tools.
