import os
import tempfile
import asyncio
import aiofiles
import aiohttp
from pathlib import Path


async def download_file(bot, file_id: str, suffix: str = ".ogg") -> str:
    file = await bot.get_file(file_id)
    file_path = file.file_path
    url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            async with aiofiles.open(tmp.name, "wb") as f:
                while True:
                    chunk = await resp.content.read(65536)
                    if not chunk:
                        break
                    await f.write(chunk)

    return tmp.name


def get_audio_duration(file_path: str) -> float:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception:
        return 0.0


def trim_audio(file_path: str, max_seconds: float = 60.0) -> str:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        trimmed = audio[:int(max_seconds * 1000)]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        tmp.close()
        trimmed.export(tmp.name, format="ogg")
        return tmp.name
    except Exception:
        return file_path


def extract_audio_from_video(video_path: str) -> str:
    import subprocess
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    tmp.close()
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn",
         "-acodec", "libopus", "-b:a", "64k", tmp.name],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()}")
    return tmp.name


def cleanup_file(file_path: str) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
