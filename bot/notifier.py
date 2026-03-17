import logging
import traceback

import config

logger = logging.getLogger(__name__)

_bot = None


def set_bot(bot):
    global _bot
    _bot = bot


async def notify_admin(text: str):
    if not _bot or not config.ADMIN_TELEGRAM_ID:
        return
    try:
        await _bot.send_message(config.ADMIN_TELEGRAM_ID, text)
    except Exception as e:
        logger.warning(f"Failed to send admin notification: {e}")


async def notify_error(error: Exception, context: str = ""):
    lines = [
        "🚨 <b>Ошибка в боте</b>",
    ]
    if context:
        lines.append(f"📍 <b>Где:</b> {context}")
    lines.append(f"❗ <b>Тип:</b> {type(error).__name__}")
    lines.append(f"💬 <b>Сообщение:</b> {str(error)[:300]}")
    tb = traceback.format_exc()
    if tb and tb.strip() != "NoneType: None":
        lines.append(f"<pre>{tb[-800:]}</pre>")
    await notify_admin("\n".join(lines))


async def notify_startup():
    await notify_admin("✅ <b>Бот запущен</b> и готов к работе")


async def notify_shutdown():
    await notify_admin("🔴 <b>Бот остановлен</b>")
