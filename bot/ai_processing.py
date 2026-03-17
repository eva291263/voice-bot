import asyncio
import logging
import os
import tempfile

import aiohttp

import config
from bot.yandex_auth import get_iam_token

logger = logging.getLogger(__name__)

YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

STT_CHUNK_SECONDS = 25


async def _auth_headers() -> dict:
    if config.YANDEX_SA_PRIVATE_KEY:
        token = await get_iam_token()
        return {"Authorization": f"Bearer {token}"}
    return {"Authorization": f"Api-Key {config.YANDEX_API_KEY}"}


def _model_uri() -> str:
    return f"gpt://{config.YANDEX_FOLDER_ID}/{config.YANDEX_GPT_MODEL}"


async def generate_answer_with_yandexgpt(
    prompt: str,
    system_prompt: str = "Ты полезный ИИ-помощник.",
    max_tokens: int = 1000,
    temperature: float = 0.3,
) -> str:
    payload = {
        "modelUri": _model_uri(),
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": str(max_tokens),
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": prompt},
        ],
    }
    headers = {**await _auth_headers(), "Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=90)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(YANDEX_GPT_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"YandexGPT error {resp.status}: {body}")
            data = await resp.json()

    return data["result"]["alternatives"][0]["message"]["text"].strip()


def _split_audio_chunks(file_path: str, chunk_seconds: int = STT_CHUNK_SECONDS) -> list[str]:
    from pydub import AudioSegment

    audio = AudioSegment.from_file(file_path)
    chunk_ms = chunk_seconds * 1000
    chunks = []
    for start in range(0, len(audio), chunk_ms):
        chunk = audio[start: start + chunk_ms]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        tmp.close()
        chunk.export(tmp.name, format="ogg", codec="libopus")
        chunks.append(tmp.name)
    return chunks


async def _transcribe_chunk(file_path: str, lang: str = "ru-RU") -> str:
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    params = {
        "folderId": config.YANDEX_FOLDER_ID,
        "lang": lang,
        "topic": "general",
    }
    headers = {**await _auth_headers(), "Content-Type": "audio/ogg;codecs=opus"}

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            YANDEX_STT_URL, data=audio_bytes, headers=headers, params=params
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"SpeechKit error {resp.status}: {body}")
            data = await resp.json()

    return data.get("result", "").strip()


def _get_duration_safe(file_path: str) -> float:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception:
        pass
    try:
        import subprocess, json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", file_path],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if "duration" in stream:
                return float(stream["duration"])
    except Exception:
        pass
    logger.warning(f"Could not determine duration for {file_path}, forcing chunked mode")
    return 9999.0


async def transcribe_audio(file_path: str, language: str = "ru") -> str:
    lang_code = "ru-RU" if language == "ru" else language if "-" in language else f"{language}-{language.upper()}"

    duration_seconds = _get_duration_safe(file_path)
    logger.info(f"Audio duration detected: {duration_seconds:.1f}s for {file_path}")

    if duration_seconds <= STT_CHUNK_SECONDS:
        return await _transcribe_chunk(file_path, lang=lang_code)

    chunk_paths = _split_audio_chunks(file_path, chunk_seconds=STT_CHUNK_SECONDS)
    try:
        results = []
        for chunk_path in chunk_paths:
            try:
                text = await _transcribe_chunk(chunk_path, lang=lang_code)
                if text:
                    results.append(text)
            finally:
                try:
                    os.remove(chunk_path)
                except Exception:
                    pass
        return " ".join(results).strip()
    except Exception:
        for p in chunk_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        raise


async def make_summary(text: str, language: str = "ru") -> str:
    lang_instruction = "на русском языке" if language == "ru" else "in English"
    system = (
        f"Ты помощник. Сделай краткое резюме следующего текста {lang_instruction}. "
        "Выдели только главное, структурируй по пунктам если нужно."
    )
    return await generate_answer_with_yandexgpt(text, system_prompt=system, max_tokens=800)


async def make_task_list(text: str, language: str = "ru") -> str:
    lang_instruction = "на русском языке" if language == "ru" else "in English"
    system = (
        f"Ты помощник. Из следующего текста извлеки список конкретных задач и действий {lang_instruction}. "
        "Оформи как пронумерованный список с глаголами действия. Если задач нет — скажи об этом."
    )
    return await generate_answer_with_yandexgpt(text, system_prompt=system, max_tokens=800)


async def make_outline(text: str, language: str = "ru") -> str:
    lang_instruction = "на русском языке" if language == "ru" else "in English"
    system = (
        f"Ты помощник. Сделай структурированный конспект следующего текста {lang_instruction}. "
        "Используй заголовки, подпункты и ключевые тезисы."
    )
    return await generate_answer_with_yandexgpt(text, system_prompt=system, max_tokens=1200)


async def translate_text(text: str, target_language: str = "en") -> str:
    lang_map = {"en": "английский", "ru": "русский", "de": "немецкий", "es": "испанский"}
    lang_name = lang_map.get(target_language, "английский")
    system = f"Переведи следующий текст на {lang_name} язык. Сохрани структуру и форматирование."
    return await generate_answer_with_yandexgpt(text, system_prompt=system, max_tokens=1500)
