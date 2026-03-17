import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN", "")

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID", "")
YANDEX_GPT_MODEL = os.environ.get("YANDEX_GPT_MODEL", "yandexgpt-lite")

YANDEX_SA_KEY_ID = os.environ.get("YANDEX_SA_KEY_ID", "")
YANDEX_SA_ID = os.environ.get("YANDEX_SA_ID", "")
YANDEX_SA_PRIVATE_KEY = os.environ.get("YANDEX_SA_PRIVATE_KEY", "")

_SA_KEY_FILE = os.path.join(os.path.dirname(__file__), "sa_key.json")
if not YANDEX_SA_PRIVATE_KEY and os.path.exists(_SA_KEY_FILE):
    import json as _json
    with open(_SA_KEY_FILE) as _f:
        _sa = _json.load(_f)
    YANDEX_SA_KEY_ID = _sa.get("id", YANDEX_SA_KEY_ID)
    YANDEX_SA_ID = _sa.get("service_account_id", YANDEX_SA_ID)
    YANDEX_SA_PRIVATE_KEY = _sa.get("private_key", YANDEX_SA_PRIVATE_KEY)

ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", "0"))

TRIAL_MINUTES = 5
TRIAL_BONUS_MINUTES = 3
DAILY_FREE_MINUTES = 1
PRO_MONTHLY_MINUTES = 150
PRO_PRICE_RUB = 290
PRO_PRICE_STARS = 290
MAX_REFERRAL_BONUS_MINUTES_FREE = 15
REFERRAL_BONUS_MINUTES = 3

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "sslmode=" in DATABASE_URL:
    import re
    DATABASE_URL = re.sub(r"[?&]sslmode=[^&]*", "", DATABASE_URL).rstrip("?")
