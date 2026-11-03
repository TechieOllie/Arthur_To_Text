# Keep the Python version in step with flake.nix and pyproject.toml.
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /bin/

# ffmpeg converts the voice messages to the 16 kHz WAV Whisper reads.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first, in their own layer: code changes don't reinstall them.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY bot/ bot/

CMD ["python", "-m", "bot"]
