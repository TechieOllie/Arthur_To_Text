import asyncio
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

import discord
from faster_whisper import WhisperModel

from .config import Config

log = logging.getLogger(__name__)


@dataclass
class TranscriptionJob:
    message: discord.Message
    workdir: tempfile.TemporaryDirectory
    wav_path: Path


class Bot(discord.Client):
    """Replies to every audio attachment with its transcription."""

    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        # Privileged: also enabled under Bot → Privileged Gateway Intents.
        intents.message_content = True
        super().__init__(intents=intents)
        self.config = config
        self.queue: asyncio.Queue[TranscriptionJob] = asyncio.Queue()
        self.model: WhisperModel | None = None

    async def setup_hook(self) -> None:
        # Runs once, before connecting (on_ready runs again on every
        # reconnect, which would start another worker each time).
        log.info("Loading Whisper model '%s'...", self.config.whisper_model)
        self.model = await asyncio.to_thread(
            WhisperModel, self.config.whisper_model, device="cpu", compute_type="int8"
        )
        log.info("Model loaded")
        self.worker = asyncio.create_task(self._process_queue())

    async def on_ready(self) -> None:
        log.info("Logged in as %s", self.user)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        for attachment in message.attachments:
            if attachment.content_type and "audio" in attachment.content_type:
                workdir = tempfile.TemporaryDirectory()
                ogg_path = Path(workdir.name) / "input.ogg"
                wav_path = Path(workdir.name) / "input.wav"
                ogg_path.write_bytes(await attachment.read())

                ffmpeg = await asyncio.create_subprocess_exec(
                    "ffmpeg",
                    "-i",
                    ogg_path,
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    wav_path,
                    "-y",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await ffmpeg.wait()

                await self.queue.put(TranscriptionJob(message, workdir, wav_path))
                break

    async def _process_queue(self) -> None:
        assert self.model is not None
        while True:
            job = await self.queue.get()
            try:
                async with job.message.channel.typing():
                    text = await asyncio.to_thread(self._transcribe, job.wav_path)
                    await job.message.reply(f"📝 **Transcription:** {text}")
            except Exception:
                log.exception("Transcription failed")
            finally:
                job.workdir.cleanup()
                self.queue.task_done()

    def _transcribe(self, wav_path: Path) -> str:
        """Blocking: runs in a worker thread."""
        assert self.model is not None
        segments, _ = self.model.transcribe(
            str(wav_path),
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=True,
        )
        # segments is a lazy generator: the decoding happens while joining.
        return "".join(seg.text for seg in segments)
