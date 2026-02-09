"""Система квестов — выбор, прохождение по шагам, подсказки."""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MAIN_MENU, QUEST_SELECT, QUEST_PLAY
from database import (
    get_all_quests, get_quest, get_quest_progress,
    start_quest, advance_quest, update_user_score,
    increment_stat, grant_achievement,
)


async def quest_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    quests = await get_all_quests()
    if not quests:
        text = "\U0001f5fa <b>Квесты</b>\n\nПока нет доступных квестов."
        kb = [[InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")]]
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return QUEST_SELECT

    keyboard = []
    for q in quests:
        steps = json.loads(q["steps"])
        keyboard.append([
            InlineKeyboardButton(
                f"{q['title']} ({len(steps)} этапов, +{q['reward_points']} баллов)",
                callback_data=f"quest_begin:{q['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")])

    text = (
        "\U0001f5fa <b>Квесты</b>\n\n"
        "Выбери квест и пройди все этапы!\n"
        "Отвечай на вопросы текстом, чтобы продвигаться дальше.\n\n"
        "\U0001f4a1 <i>Если застрянешь — используй подсказку!</i>"
    )
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return QUEST_SELECT


async def quest_begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quest_id = int(query.data.split(":")[1])
    quest = await get_quest(quest_id)
    if not quest:
        await query.edit_message_text("Квест не найден.")
        return MAIN_MENU

    steps = json.loads(quest["steps"])
    user_id = query.from_user.id

    # Проверяем, есть ли уже прогресс
    progress = await get_quest_progress(user_id, quest_id)
    current_step = 0
    if not progress:
        await start_quest(user_id, quest_id)
    else:
        current_step = progress["current_step"]

    context.user_data["quest_state"] = {
        "quest_id": quest_id,
        "title": quest["title"],
        "steps": steps,
        "current_step": current_step,
        "reward_points": quest["reward_points"],
    }

    return await _show_quest_step(query, context)


async def _show_quest_step(query_or_message, context: ContextTypes.DEFAULT_TYPE, is_message=False):
    state = context.user_data["quest_state"]
    idx = state["current_step"]
    step = state["steps"][idx]

    progress = f"Этап {idx + 1}/{len(state['steps'])}"
    progress_bar = "\u2588" * (idx + 1) + "\u2591" * (len(state["steps"]) - idx - 1)

    text = (
        f"\U0001f5fa <b>{state['title']}</b>\n"
        f"<i>{progress}</i> {progress_bar}\n\n"
        f"{step['text']}"
    )

    keyboard = [
        [InlineKeyboardButton("\U0001f4a1 Подсказка", callback_data="quest_hint")],
        [InlineKeyboardButton("\u274c Выйти из квеста", callback_data="quest_list")],
    ]

    if is_message:
        await query_or_message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await query_or_message.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return QUEST_PLAY


async def quest_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    state = context.user_data.get("quest_state")
    if not state:
        await query.answer()
        return MAIN_MENU

    step = state["steps"][state["current_step"]]
    hint = step.get("hint", "Подсказок нет для этого этапа.")

    await query.answer(hint, show_alert=True)
    return QUEST_PLAY


async def quest_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ответа в квесте."""
    state = context.user_data.get("quest_state")
    if not state:
        return MAIN_MENU

    user_answer = update.message.text.strip().lower()
    step = state["steps"][state["current_step"]]
    correct_answer = step["answer"].strip().lower()

    user_id = update.effective_user.id

    if user_answer == correct_answer:
        state["current_step"] += 1

        if state["current_step"] >= len(state["steps"]):
            # Квест завершён!
            await advance_quest(user_id, state["quest_id"], state["current_step"], completed=True)
            await update_user_score(user_id, state["reward_points"])
            await increment_stat(user_id, "quests_completed")

            new_achievements = []
            if await grant_achievement(user_id, "first_quest", "\U0001f5fa Первый квест"):
                new_achievements.append("\U0001f5fa Первый квест")

            text = (
                f"\U0001f389 <b>Квест «{state['title']}» пройден!</b>\n\n"
                f"\u2705 Все этапы завершены!\n"
                f"\U0001f4b0 Награда: <b>+{state['reward_points']} баллов</b>\n"
            )
            if new_achievements:
                text += "\n\U0001f3c6 <b>Новые достижения:</b>\n"
                for ach in new_achievements:
                    text += f"  {ach}\n"

            keyboard = [
                [InlineKeyboardButton("\U0001f5fa Другие квесты", callback_data="quest_list")],
                [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
            ]
            context.user_data.pop("quest_state", None)

            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
            )
            return MAIN_MENU
        else:
            await advance_quest(user_id, state["quest_id"], state["current_step"])

            await update.message.reply_text(
                "\u2705 <b>Правильно! Молодец!</b>\n\nПереходим к следующему этапу...",
                parse_mode="HTML",
            )
            return await _show_quest_step(update.message, context, is_message=True)
    else:
        keyboard = [
            [InlineKeyboardButton("\U0001f4a1 Подсказка", callback_data="quest_hint")],
            [InlineKeyboardButton("\u274c Выйти из квеста", callback_data="quest_list")],
        ]
        await update.message.reply_text(
            "\u274c <b>Неправильно!</b> Попробуй ещё раз.\n\n"
            "<i>Если затрудняешься — нажми «Подсказка»</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return QUEST_PLAY
