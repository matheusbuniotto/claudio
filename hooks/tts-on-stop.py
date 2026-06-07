#!/usr/bin/env python3
"""Claude Code Stop hook: reads the last assistant message aloud via Groq TTS, with local `say` fallback."""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/speech"
MAX_CHARS = 3000


def clean_text(text: str) -> str:
    # Remove fenced code blocks (file content, diffs, tool output)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Strip inline code backticks but keep the text so it reads naturally
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    # Strip XML-style tags but keep inner content
    text = re.sub(r"<[a-zA-Z][^>]*>([\s\S]*?)</[a-zA-Z][^>]*>", r"\1", text)
    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def speak_groq(text: str, api_key: str, voice: str, speed: float) -> None:
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    payload = json.dumps(
        {
            "model": "playai-tts",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
            "speed": speed,
        }
    ).encode()

    req = urllib.request.Request(
        GROQ_TTS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as resp:
        audio_bytes = resp.read()

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        player = "afplay" if sys.platform == "darwin" else "mpg123"
        subprocess.run([player, tmp_path], check=True, capture_output=True)
    finally:
        os.unlink(tmp_path)


def speak_local(text: str) -> None:
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    if sys.platform == "darwin":
        subprocess.run(["say", text], check=True, capture_output=True)
    else:
        subprocess.run(["espeak", text], check=True, capture_output=True)


def main() -> None:
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    # Prevent recursive hook loop
    if data.get("stop_hook_active"):
        sys.exit(0)

    text = data.get("last_assistant_message", "")
    if not text:
        sys.exit(0)

    cleaned = clean_text(text)
    if len(cleaned) < 10:
        sys.exit(0)

    if os.environ.get("CLAUDIO_TTS_ENABLED", "1") == "0":
        sys.exit(0)

    if os.path.exists(os.path.expanduser("~/.claude/claudio-tts.disabled")):
        sys.exit(0)

    voice = os.environ.get("CLAUDIO_TTS_VOICE", "Aaliyah-PlayAI")
    speed = float(os.environ.get("CLAUDIO_TTS_SPEED", "1.0"))
    api_key = os.environ.get("GROQ_API_KEY", "")

    if api_key:
        try:
            speak_groq(cleaned, api_key, voice, speed)
            return
        except urllib.error.HTTPError as e:
            print(f"claudio-tts: Groq API error {e.code}, falling back to local TTS", file=sys.stderr)
        except Exception as e:
            print(f"claudio-tts: Groq failed ({e}), falling back to local TTS", file=sys.stderr)

    try:
        speak_local(cleaned)
    except Exception as e:
        print(f"claudio-tts: local TTS failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
