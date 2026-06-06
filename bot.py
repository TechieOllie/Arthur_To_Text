import sys

if not sys.stdout.isatty():
    sys.stdout.isatty = lambda: True

import asyncio
import os
import subprocess
import tempfile
from dataclasses import dataclass
from functools import partial

import discord
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")

print(f"Loading Whisper model '{MODEL_SIZE}'...", flush=True)
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
print("Model loaded successfully.", flush=True)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
queue = asyncio.Queue()


@dataclass
class TranscriptionJob:
    message: discord.Message
    ogg_path: str
    wav_path: str


async def process_queue():
    while True:
        job = await queue.get()
        async with job.message.channel.typing():
            try:
                transcribe = partial(
                    model.transcribe,
                    job.wav_path,
                    language="fr",
                    beam_size=15,
                    vad_filter=True,
                )
                segments, _ = await asyncio.to_thread(transcribe)
                text = "".join(seg.text for seg in segments)
                await job.message.reply(f"📝 **Transcription:** {text}")
            finally:
                os.unlink(job.ogg_path)
                os.unlink(job.wav_path)
                queue.task_done()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(process_queue())


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    for attachment in message.attachments:
        if attachment.content_type and "audio" in attachment.content_type:
            audio_bytes = await attachment.read()

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(audio_bytes)
                ogg_path = f.name

            wav_path = ogg_path.replace(".ogg", ".wav")
            subprocess.run(
                ["ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                capture_output=True,
            )

            await queue.put(TranscriptionJob(message, ogg_path, wav_path))
            break


bot.run(TOKEN)
