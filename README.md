# claudio-tts

A [Claude Code](https://claude.ai/code) hook that reads Claude's last message aloud after every response.

Uses [Groq TTS](https://console.groq.com) when a `GROQ_API_KEY` is set, and falls back to the system's built-in speech (`say` on macOS, `espeak` on Linux) — no extra setup needed.

## Quick Install

Add the community marketplace, then install:

```bash
/plugin marketplace add anthropics/claude-plugins-community
/plugin install claudio-tts@claude-community
```

Set your Groq API key (free tier available at [console.groq.com](https://console.groq.com)):

```bash
export GROQ_API_KEY=your_key_here
```

That's it. Claude will start speaking after the next response.

## Usage

Once installed, the hook runs automatically on every Claude Code session. No commands needed.

Toggle it on or off at any time:

```
/claudio-tts:off
/claudio-tts:on
```

Or set an env var to disable for the current session only:

```bash
export CLAUDIO_TTS_ENABLED=0
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `CLAUDIO_TTS_ENABLED` | `1` | Set to `0` to disable |
| `CLAUDIO_TTS_VOICE` | `Aaliyah-PlayAI` | Groq TTS voice name |
| `CLAUDIO_TTS_SPEED` | `1.0` | Playback speed multiplier |

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`) to make them persistent.

## Groq TTS vs Local

| | Groq TTS | Local (`say` / `espeak`) |
|---|---|---|
| Voice quality | Natural, expressive | Robotic |
| Setup | `GROQ_API_KEY` required | Zero config |
| Works offline | No | Yes |
| Cost | Free tier is generous | Free |

If Groq is unavailable or the key is missing, the hook silently falls back to local TTS — you always get audio, just with different quality.

## Manual Install

If you prefer not to use the marketplace:

1. Clone the repo:

```bash
git clone https://github.com/matheusbuniotto/claudio ~/.claude/plugins/claudio-tts
```

2. Add the hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/plugins/claudio-tts/hooks/tts-on-stop.py"
          }
        ]
      }
    ]
  }
}
```

## Roadmap

- [ ] Local Whisper-based TTS (fully offline, high-quality)

## License

MIT
