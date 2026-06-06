import sys

# Force tqdm progress bars in Docker (non-TTY environment)
if not sys.stdout.isatty():
    sys.stdout.isatty = lambda: True

import os
import subprocess
import tempfile

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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    for attachment in message.attachments:
        if attachment.content_type and "audio" in attachment.content_type:
            async with message.channel.typing():
                audio_bytes = await attachment.read()

                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                    f.write(audio_bytes)
                    ogg_path = f.name

                wav_path = ogg_path.replace(".ogg", ".wav")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        ogg_path,
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        wav_path,
                        "-y",
                    ],
                    capture_output=True,
                )

                segments, _ = model.transcribe(
                    wav_path, language="fr", beam_size=15, vad_filter=True
                )
                text = "".join(seg.text for seg in segments)

                os.unlink(ogg_path)
                os.unlink(wav_path)

                await message.reply(f"📝 **Transcription:** {text}")
            break


bot.run(TOKEN)
