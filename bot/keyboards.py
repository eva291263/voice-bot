from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def kb_persistent_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📋 Меню")]],
        resize_keyboard=True,
        is_persistent=True,
    )


def kb_start_onboarding() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙️ Попробовать бесплатно", callback_data="try_free")]
    ])


def kb_after_intro() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙️ Отправить голосовое", callback_data="send_voice")],
        [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="how_it_works")],
    ])


def kb_trial_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙️ Использовать пробные минуты", callback_data="send_voice")],
        [InlineKeyboardButton(text="💰 Посмотреть Pro подписку", callback_data="show_pro")],
    ])


def kb_after_transcription(is_pro: bool, has_trial: bool) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📋 Скопировать текст", callback_data="copy_text"),
            InlineKeyboardButton(text="💾 Сохранить .txt", callback_data="save_txt"),
        ],
    ]
    if is_pro or has_trial:
        buttons.append([
            InlineKeyboardButton(text="✂️ Краткое резюме", callback_data="ai_summary"),
            InlineKeyboardButton(text="✅ Список задач", callback_data="ai_tasks"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📚 Конспект", callback_data="ai_outline"),
            InlineKeyboardButton(text="🌍 Перевести", callback_data="ai_translate"),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="✂️ Резюме (Pro)", callback_data="upsell_pro"),
            InlineKeyboardButton(text="✅ Задачи (Pro)", callback_data="upsell_pro"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📚 Конспект (Pro)", callback_data="upsell_pro"),
            InlineKeyboardButton(text="🌍 Перевод (Pro)", callback_data="upsell_pro"),
        ])
    buttons.append([
        InlineKeyboardButton(text="🎙️ Отправить ещё", callback_data="send_voice"),
        InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_trial_exhausted() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Оформить Pro", callback_data="buy_pro")],
        [InlineKeyboardButton(text="🎙️ Попробовать 1 мин/день", callback_data="send_voice")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


def kb_audio_too_long() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✂️ Обрезать до 1 минуты", callback_data="trim_audio")],
        [InlineKeyboardButton(text="🚀 Оформить Pro", callback_data="buy_pro")],
        [InlineKeyboardButton(text="⏸ Позже", callback_data="cancel")],
    ])


def kb_pro_info() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 290 ₽", callback_data="buy_pro")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")],
    ])


def kb_pro_exhausted() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ждать новый месяц", callback_data="cancel")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])


def kb_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙️ Расшифровать голосовое", callback_data="send_voice")],
        [
            InlineKeyboardButton(text="📜 История", callback_data="history"),
            InlineKeyboardButton(text="💰 Тариф Pro", callback_data="show_pro"),
        ],
        [
            InlineKeyboardButton(text="👥 Пригласить друга", callback_data="referral"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="🆘 Помощь", callback_data="help"),
        ],
    ])


def kb_history_item(transcription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Скопировать", callback_data=f"copy_hist_{transcription_id}"),
            InlineKeyboardButton(text="💾 Сохранить .txt", callback_data=f"save_txt_hist_{transcription_id}"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"del_hist_{transcription_id}"),
        ],
        [
            InlineKeyboardButton(text="✂️ Резюме", callback_data=f"sum_hist_{transcription_id}"),
            InlineKeyboardButton(text="✅ Задачи", callback_data=f"tasks_hist_{transcription_id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ К истории", callback_data="history"),
            InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu"),
        ],
    ])


def kb_confirm_delete_data() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ Да, удалить всё", callback_data="confirm_delete_data")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def kb_settings(auto_summary: bool, language: str) -> InlineKeyboardMarkup:
    summary_text = "✅ Авто-резюме: Вкл" if auto_summary else "❌ Авто-резюме: Выкл"
    lang_text = "🇷🇺 Язык: RU" if language == "ru" else "🇬🇧 Язык: EN"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=summary_text, callback_data="toggle_auto_summary")],
        [InlineKeyboardButton(text=lang_text, callback_data="toggle_language")],
        [InlineKeyboardButton(text="🗑️ Удалить мои данные", callback_data="delete_data")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")],
    ])


def kb_back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
    ])


def kb_upsell() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Оформить Pro", callback_data="buy_pro")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")],
    ])


def kb_help() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆘 Сообщить о проблеме", callback_data="sos")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")],
    ])
