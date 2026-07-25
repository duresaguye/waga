"""Download Telegram voice notes and transcribe via Addis AI."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from telegram import Bot, Message

from telegram_bot.config import TelegramBotSettings
from telegram_bot.services.addis_stt import (
    AddisSTTClient,
    AddisSTTError,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


async def transcribe_message_audio(
    *,
    bot: Bot,
    message: Message,
    settings: TelegramBotSettings,
    language_code: str | None = None,
) -> TranscriptionResult:
    voice = message.voice
    audio = message.audio
    if voice is None and audio is None:
        raise AddisSTTError("Please send a voice note.")

    file_id = voice.file_id if voice is not None else audio.file_id  # type: ignore[union-attr]
    suffix = ".ogg" if voice is not None else _suffix_from_audio(audio)
    telegram_file = await bot.get_file(file_id)

    with tempfile.TemporaryDirectory(prefix="waga-voice-") as tmp:
        raw_path = Path(tmp) / f"input{suffix}"
        await telegram_file.download_to_drive(custom_path=str(raw_path))

        send_path = raw_path
        send_name = raw_path.name
        content_type: str | None = None

        # Addis AI accepts wav/mp3/m4a/webm — not Telegram ogg/opus.
        if suffix in {".ogg", ".oga"}:
            wav_path = Path(tmp) / "input.wav"
            if not _convert_to_wav(raw_path, wav_path):
                raise AddisSTTError(
                    "Could not convert voice note for Addis AI. "
                    "Please send again, or type the market name."
                )
            send_path = wav_path
            send_name = "input.wav"
            content_type = "audio/wav"

        client = AddisSTTClient(settings)
        return await client.transcribe_file(
            send_path,
            language_code=language_code,
            filename=send_name,
            content_type=content_type,
        )


def _suffix_from_audio(audio: object) -> str:
    file_name = getattr(audio, "file_name", None)
    if isinstance(file_name, str) and "." in file_name:
        return "." + file_name.rsplit(".", 1)[-1].lower()
    mime = getattr(audio, "mime_type", None)
    if mime == "audio/mpeg":
        return ".mp3"
    if mime in {"audio/mp4", "audio/x-m4a"}:
        return ".m4a"
    return ".ogg"


def _ffmpeg_exe() -> str | None:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as error:  # noqa: BLE001
        logger.warning("imageio-ffmpeg unavailable: %s", error)
        return None


def _convert_to_wav(source: Path, dest: Path) -> bool:
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        logger.error("No ffmpeg binary available for voice conversion")
        return False
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        logger.warning("ffmpeg conversion failed: %s", error)
        return False
    return dest.exists() and dest.stat().st_size > 0
