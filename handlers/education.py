"""Образовательный контент — темы о строительстве, компании, профессиях."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MAIN_MENU, EDUCATION_TOPIC, EDUCATION_DETAIL
from data.content import EDUCATION_TOPICS


async def education_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for key, topic in EDUCATION_TOPICS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{topic['icon']} {topic['title']}", callback_data=f"edu_topic:{key}"
            )
        ])
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")])

    await query.edit_message_text(
        "\U0001f4da <b>Образовательные материалы</b>\n\n"
        "Выбери тему, которая тебе интересна:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return EDUCATION_TOPIC


async def topic_sections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    topic_key = query.data.split(":")[1]
    topic = EDUCATION_TOPICS.get(topic_key)
    if not topic:
        await query.edit_message_text("Тема не найдена.")
        return MAIN_MENU

    context.user_data["current_topic"] = topic_key

    keyboard = []
    for sec_key, section in topic["sections"].items():
        keyboard.append([
            InlineKeyboardButton(
                section["title"], callback_data=f"edu_section:{topic_key}:{sec_key}"
            )
        ])
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f К темам", callback_data="education")])

    await query.edit_message_text(
        f"{topic['icon']} <b>{topic['title']}</b>\n\n"
        "Выбери раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return EDUCATION_DETAIL


async def section_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    topic_key = parts[1]
    section_key = parts[2]

    topic = EDUCATION_TOPICS.get(topic_key)
    if not topic:
        return MAIN_MENU

    section = topic["sections"].get(section_key)
    if not section:
        return MAIN_MENU

    # Кнопки навигации между разделами
    section_keys = list(topic["sections"].keys())
    current_idx = section_keys.index(section_key)

    nav_buttons = []
    if current_idx > 0:
        prev_key = section_keys[current_idx - 1]
        nav_buttons.append(
            InlineKeyboardButton(
                "\u2b05\ufe0f Назад",
                callback_data=f"edu_section:{topic_key}:{prev_key}"
            )
        )
    if current_idx < len(section_keys) - 1:
        next_key = section_keys[current_idx + 1]
        nav_buttons.append(
            InlineKeyboardButton(
                "Далее \u27a1\ufe0f",
                callback_data=f"edu_section:{topic_key}:{next_key}"
            )
        )

    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([
        InlineKeyboardButton(
            f"\U0001f4cb К разделам «{topic['title']}»",
            callback_data=f"edu_topic:{topic_key}"
        )
    ])
    keyboard.append([InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")])

    progress = f"({current_idx + 1}/{len(section_keys)})"

    full_text = f"{section['text']}\n\n<i>{progress}</i>"
    # Telegram ограничивает сообщения 4096 символами
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "..."

    await query.edit_message_text(
        full_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return EDUCATION_DETAIL
