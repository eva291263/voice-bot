import time
import asyncio
import logging
import aiohttp
import jwt

import config

logger = logging.getLogger(__name__)

_cached_token: str = ""
_token_expires_at: float = 0.0
_lock = asyncio.Lock()

IAM_TOKEN_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
TOKEN_LIFETIME = 3600


def _build_jwt() -> str:
    private_key = config.YANDEX_SA_PRIVATE_KEY.replace("\\n", "\n")
    now = int(time.time())
    payload = {
        "iss": config.YANDEX_SA_ID,
        "aud": IAM_TOKEN_URL,
        "iat": now,
        "exp": now + TOKEN_LIFETIME,
    }
    headers = {
        "kid": config.YANDEX_SA_KEY_ID,
    }
    return jwt.encode(payload, private_key, algorithm="PS256", headers=headers)


async def get_iam_token() -> str:
    global _cached_token, _token_expires_at

    async with _lock:
        now = time.time()
        if _cached_token and now < _token_expires_at - 60:
            return _cached_token

        signed_jwt = _build_jwt()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                IAM_TOKEN_URL,
                json={"jwt": signed_jwt},
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"IAM token error {resp.status}: {body}")
                data = await resp.json()

        _cached_token = data["iamToken"]
        _token_expires_at = now + TOKEN_LIFETIME
        logger.info("IAM token refreshed successfully")
        return _cached_token


def auth_header_sync() -> dict:
    return {}
