"""Опросы — встроенные Telegram-опросы."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputPollOption
from telegram.ext import ContextTypes

from config import MAIN_MENU, POLL_SELECT
from data.content import POLLS
from database import increment_stat, update_user_score


async def poll_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = []
    for i, poll in enumerate(POLLS):
        keyboard.append([
            InlineKeyboardButton(
                poll["question"][:50] + ("..." if len(poll["question"]) > 50 else ""),
                callback_data=f"poll_send:{i}"
            )
        ])
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")])

    text = (
        "\U0001f4ca <b>Опросы</b>\n\n"
        "Выбери опрос и поделись своим мнением!\n"
        "За каждый ответ ты получишь <b>+2 балла</b> \U0001f4b0"
    )
    if query:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return POLL_SELECT


async def poll_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    poll_idx = int(query.data.split(":")[1])
    if poll_idx >= len(POLLS):
        return POLL_SELECT

    poll_data = POLLS[poll_idx]

    # Удаляем сообщение с меню, чтобы не было визуального мусора
    try:
        await query.message.delete()
    except Exception:
        pass

    # Отправляем нативный Telegram-опрос (PTB 22.x требует InputPollOption)
    options = [InputPollOption(text=opt) for opt in poll_data["options"]]
    await context.bot.send_poll(
        chat_id=query.message.chat_id,
        question=poll_data["question"],
        options=options,
        is_anonymous=poll_data.get("is_anonymous", False),
        type="regular",
    )

    # Кнопка возврата
    keyboard = [
        [InlineKeyboardButton("\U0001f4ca Ещё опросы", callback_data="poll_list")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="\u2705 Спасибо за участие в опросе!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Начислить баллы
    await update_user_score(query.from_user.id, 2)
    await increment_stat(query.from_user.id, "polls_answered")

    return MAIN_MENU
