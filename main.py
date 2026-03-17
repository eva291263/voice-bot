import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, ErrorEvent

import config
from bot.database import init_db
from bot.handlers import commands, voice_handler, callbacks, payments
from bot.yandex_auth import get_iam_token
from bot import notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def _health_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="OK"))
    app.router.add_get("/health", lambda r: web.Response(text="OK"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server started on port {port}")


async def _setup_bot(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / главное меню"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="profile", description="Мой профиль и лимиты"),
        BotCommand(command="history", description="История расшифровок"),
        BotCommand(command="referral", description="Пригласить друга (+3 мин)"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="delete_data", description="Удалить мои данные"),
    ])
    try:
        await bot.set_my_description(
            description=(
                "🎙 Отправь голосовое, аудио или видео — получи точный текст за секунды.\n\n"
                "✔️ Голосовые сообщения и аудиофайлы\n"
                "✔️ Видео и кружочки (video note)\n"
                "✔️ Краткое резюме и список задач\n"
                "✔️ Конспект и перевод на любой язык\n\n"
                "🎁 Первые 5 минут — бесплатно!\n"
                "📅 Затем 1 минута бесплатно каждый день.\n\n"
                "👇 Нажми СТАРТ и попробуй прямо сейчас!"
            )
        )
        await bot.set_my_short_description(
            short_description="Голосовые, аудио и видео → текст за секунды. 5 минут бесплатно!"
        )
    except Exception as e:
        logger.warning(f"Could not set bot description: {e}")
    if config.YANDEX_SA_PRIVATE_KEY or config.YANDEX_API_KEY:
        try:
            await get_iam_token()
            logger.info("IAM token prewarmed.")
        except Exception as e:
            logger.warning(f"Could not prewarm IAM token: {e}")
    logger.info("Bot setup complete.")


async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        sys.exit(1)

    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    await _health_server()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    notifier.set_bot(bot)

    dp = Dispatcher()

    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        logger.error(f"Unhandled exception: {event.exception}", exc_info=event.exception)
        await notifier.notify_error(event.exception, context="глобальный обработчик")
        return True

    dp.include_router(payments.router)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(voice_handler.router)

    await _setup_bot(bot)
    await notifier.notify_startup()

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "pre_checkout_query"],
        )
    finally:
        await notifier.notify_shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
