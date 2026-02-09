"""Система викторин — выбор, прохождение, результаты."""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MAIN_MENU, QUIZ_SELECT, QUIZ_PLAY
from database import (
    get_all_quizzes, get_quiz, save_quiz_result,
    update_user_score, increment_stat, grant_achievement,
)


async def quiz_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    quizzes = await get_all_quizzes()
    if not quizzes:
        text = "\U0001f3af <b>Викторины</b>\n\nПока нет доступных викторин."
        kb = [[InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")]]
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return QUIZ_SELECT

    keyboard = []
    for q in quizzes:
        questions = json.loads(q["questions"])
        keyboard.append([
            InlineKeyboardButton(
                f"{q['title']} ({len(questions)} вопросов)",
                callback_data=f"quiz_start:{q['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f Назад", callback_data="back_to_menu")])

    text = (
        "\U0001f3af <b>Викторины</b>\n\n"
        "Выбери викторину и проверь свои знания!\n"
        "За правильные ответы начисляются баллы \U0001f4b0"
    )
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return QUIZ_SELECT


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.split(":")[1])
    quiz = await get_quiz(quiz_id)
    if not quiz:
        await query.edit_message_text("Викторина не найдена.")
        return MAIN_MENU

    questions = json.loads(quiz["questions"])
    context.user_data["quiz_state"] = {
        "quiz_id": quiz_id,
        "title": quiz["title"],
        "questions": questions,
        "current": 0,
        "score": 0,
        "total": len(questions),
    }

    return await _show_question(query, context)


async def _show_question(query, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data["quiz_state"]
    idx = state["current"]
    q = state["questions"][idx]

    keyboard = []
    for i, option in enumerate(q["options"]):
        emoji = ["A", "B", "C", "D"][i] if i < 4 else str(i + 1)
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji}) {option}",
                callback_data=f"quiz_answer:{i}"
            )
        ])

    progress_bar = _progress_bar(idx, state["total"])
    text = (
        f"\U0001f3af <b>{state['title']}</b>\n\n"
        f"<b>Вопрос {idx + 1}/{state['total']}</b>\n"
        f"{progress_bar}\n\n"
        f"{q['text']}"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return QUIZ_PLAY


def _progress_bar(current: int, total: int) -> str:
    filled = int((current / total) * 10)
    return "\u2588" * filled + "\u2591" * (10 - filled)


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    state = context.user_data.get("quiz_state")
    if not state:
        return MAIN_MENU

    answer_idx = int(query.data.split(":")[1])
    q = state["questions"][state["current"]]
    correct = q["correct"]
    is_correct = answer_idx == correct

    if is_correct:
        state["score"] += 1
        result_text = "\u2705 <b>Правильно!</b>"
    else:
        correct_text = q["options"][correct]
        result_text = f"\u274c <b>Неправильно!</b>\nПравильный ответ: <b>{correct_text}</b>"

    explanation = q.get("explanation", "")
    if explanation:
        result_text += f"\n\n\U0001f4a1 {explanation}"

    state["current"] += 1

    if state["current"] < state["total"]:
        keyboard = [[InlineKeyboardButton("Следующий вопрос \u27a1\ufe0f", callback_data="quiz_next")]]
        await query.edit_message_text(
            result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
        return QUIZ_PLAY
    else:
        return await _show_results(query, context)


async def quiz_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await _show_question(query, context)


async def _show_results(query, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data["quiz_state"]
    score = state["score"]
    total = state["total"]
    percentage = int((score / total) * 100) if total > 0 else 0
    user_id = query.from_user.id

    # Начисляем баллы
    points = score * 5
    await update_user_score(user_id, points)
    await save_quiz_result(user_id, state["quiz_id"], score, total)
    await increment_stat(user_id, "quizzes_completed")

    # Достижения
    new_achievements = []
    if await grant_achievement(user_id, "first_quiz", "\U0001f3c5 Первая викторина"):
        new_achievements.append("\U0001f3c5 Первая викторина")

    if percentage == 100:
        if await grant_achievement(user_id, "perfect_score", "\U0001f4af Идеальный результат"):
            new_achievements.append("\U0001f4af Идеальный результат")

    # Оценка
    if percentage >= 80:
        emoji = "\U0001f929"
        comment = "Отличный результат!"
    elif percentage >= 60:
        emoji = "\U0001f60a"
        comment = "Хороший результат!"
    elif percentage >= 40:
        emoji = "\U0001f914"
        comment = "Неплохо, но можно лучше!"
    else:
        emoji = "\U0001f4aa"
        comment = "Попробуй ещё раз!"

    text = (
        f"\U0001f3c1 <b>Результаты: {state['title']}</b>\n\n"
        f"{emoji} {comment}\n\n"
        f"Правильных ответов: <b>{score}/{total}</b> ({percentage}%)\n"
        f"Баллы: <b>+{points}</b> \U0001f4b0\n"
    )

    if new_achievements:
        text += "\n\U0001f3c6 <b>Новые достижения:</b>\n"
        for ach in new_achievements:
            text += f"  {ach}\n"

    keyboard = [
        [InlineKeyboardButton("\U0001f504 Пройти ещё раз", callback_data=f"quiz_start:{state['quiz_id']}")],
        [InlineKeyboardButton("\U0001f4cb Все викторины", callback_data="quiz_list")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]

    context.user_data.pop("quiz_state", None)

    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
    )
    return MAIN_MENU
