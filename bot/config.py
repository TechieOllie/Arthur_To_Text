import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Everything the bot reads from the environment.

    Locally that's .env (loaded by direnv, or VS Code's launch config); in the
    container, the compose file's env_file.
    """

    token: str
    # faster-whisper model: tiny, base, small, medium, large-v3...
    whisper_model: str
    language: str
    beam_size: int

    @classmethod
    def from_env(cls) -> Config:
        token = os.environ.get("DISCORD_TOKEN")
        if not token:
            raise SystemExit(
                "DISCORD_TOKEN is not set: copy .env.example to .env and fill it in"
            )
        return cls(
            token=token,
            whisper_model=os.environ.get("WHISPER_MODEL", "medium"),
            language=os.environ.get("WHISPER_LANGUAGE", "fr"),
            beam_size=int(os.environ.get("WHISPER_BEAM_SIZE", "15")),
        )
