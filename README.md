# Arthur To Text

Discord bot that replies to every voice message (any audio attachment) with
its transcription, using [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
on the CPU. Jobs are queued and handled one at a time.

## Configuration

`.env` (copy `.env.example`):

| Variable | Default | |
| --- | --- | --- |
| `DISCORD_TOKEN` | — | Required. The bot needs the **Message Content** intent (Developer Portal → Bot → Privileged Gateway Intents). |
| `WHISPER_MODEL` | `medium` | `tiny`, `base`, `small`, `medium`, `large-v3`... Downloaded on first start into `~/.cache` (the `whisper-models` volume in the container). |
| `WHISPER_LANGUAGE` | `fr` | |
| `WHISPER_BEAM_SIZE` | `15` | |

## Development

`direnv allow` gives a dev shell (Python, uv, ruff, ffmpeg from `flake.nix`)
with `.venv` synced from `uv.lock` and `.env` loaded.

| | |
| --- | --- |
| Run | `python -m bot`, or `F5` in VS Code |
| Add a dependency | `uv add <package>` |
| Lint / format | `ruff check --fix && ruff format` |
| Run the container | `docker compose up --build` |

## Deploying

Every push to `main` publishes `ghcr.io/techieollie/arthur_to_text:latest`;
the server's stack (DockerComposeFiles `arthur-to-text`) pulls it:
`docker compose pull && docker compose up -d`.
