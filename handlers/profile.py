"""Профиль пользователя, рейтинг, факт дня, тест профориентации."""

import random
from collections import Counter

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    MAIN_MENU, PROFILE_VIEW, LEADERBOARD, FACT_OF_DAY,
    CAREER_TEST, CAREER_TEST_PLAY,
)
from database import (
    get_user, get_leaderboard, get_user_achievements,
    get_user_quiz_results, update_user_score, grant_achievement,
)
from data.content import (
    DAILY_FACTS, CAREER_TEST_QUESTIONS, CAREER_RESULTS, ACHIEVEMENTS,
)


# ── Профиль ──

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        text = "Профиль не найден. Нажми /start чтобы зарегистрироваться."
        if query:
            await query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return MAIN_MENU

    achievements = await get_user_achievements(user_id)
    quiz_results = await get_user_quiz_results(user_id)

    name = user.get("first_name") or user.get("username") or "Пользователь"

    # Формируем значки достижений
    badges_text = ""
    if achievements:
        badges = [a["badge_name"] for a in achievements]
        badges_text = "  ".join(badges)
    else:
        badges_text = "<i>Пока нет достижений</i>"

    # Последние результаты викторин
    quiz_text = ""
    if quiz_results:
        for qr in quiz_results[:3]:
            quiz_text += f"  \u2022 {qr['title']}: {qr['score']}/{qr['total']}\n"
    else:
        quiz_text = "  <i>Ещё не проходил(а) викторины</i>\n"

    # Ранг по баллам
    score = user.get("score", 0)
    if score >= 100:
        rank = "\U0001f451 Мастер строитель"
    elif score >= 50:
        rank = "\U0001f3c6 Опытный строитель"
    elif score >= 20:
        rank = "\U0001f477 Ученик строителя"
    else:
        rank = "\U0001f476 Новичок"

    text = (
        f"\U0001f464 <b>Профиль: {name}</b>\n\n"
        f"\U0001f3c5 Ранг: {rank}\n"
        f"\U0001f4b0 Баллы: <b>{score}</b>\n"
        f"\U0001f3af Викторин пройдено: <b>{user.get('quizzes_completed', 0)}</b>\n"
        f"\U0001f5fa Квестов пройдено: <b>{user.get('quests_completed', 0)}</b>\n"
        f"\U0001f4ca Опросов: <b>{user.get('polls_answered', 0)}</b>\n\n"
        f"\U0001f3c6 <b>Достижения:</b>\n{badges_text}\n\n"
        f"\U0001f4cb <b>Последние викторины:</b>\n{quiz_text}"
    )

    keyboard = [
        [InlineKeyboardButton("\U0001f3c6 Рейтинг игроков", callback_data="leaderboard")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]

    if query:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return PROFILE_VIEW


# ── Рейтинг ──

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    leaders = await get_leaderboard(10)

    if not leaders:
        text = "\U0001f3c6 <b>Рейтинг</b>\n\nПока никто не набрал баллов."
    else:
        text = "\U0001f3c6 <b>Рейтинг лучших игроков</b>\n\n"
        medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
        for i, leader in enumerate(leaders):
            name = leader.get("first_name") or leader.get("username") or "Аноним"
            medal = medals[i] if i < 3 else f"  {i + 1}."
            text += f"{medal} <b>{name}</b> — {leader['score']} баллов\n"

    keyboard = [
        [InlineKeyboardButton("\U0001f464 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]

    if query:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return LEADERBOARD


# ── Факт дня ──

async def fact_of_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    fact = random.choice(DAILY_FACTS)

    text = (
        "\U0001f4a1 <b>Факт дня</b>\n\n"
        f"{fact}\n\n"
        "<i>Нажми ещё раз, чтобы узнать новый факт!</i>"
    )

    keyboard = [
        [InlineKeyboardButton("\U0001f504 Ещё факт", callback_data="fact_of_day")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]

    if query:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return FACT_OF_DAY


# ── Тест профориентации ──

async def career_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    context.user_data["career_state"] = {
        "current": 0,
        "tags": [],
    }

    text = (
        "\U0001f3af <b>Тест: Какая профессия тебе подходит?</b>\n\n"
        "Ответь на 5 вопросов, и мы подскажем, "
        "какая профессия в строительной отрасли тебе подходит!\n\n"
        "<i>Нажми «Начать», чтобы приступить.</i>"
    )
    keyboard = [[InlineKeyboardButton("\U0001f680 Начать!", callback_data="career_next")]]

    if query:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    return CAREER_TEST


async def career_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    state = context.user_data.get("career_state")
    if not state:
        return MAIN_MENU

    idx = state["current"]

    if idx >= len(CAREER_TEST_QUESTIONS):
        return await _career_results(query, context)

    q = CAREER_TEST_QUESTIONS[idx]

    keyboard = []
    for i, ans in enumerate(q["answers"]):
        keyboard.append([
            InlineKeyboardButton(
                ans["text"], callback_data=f"career_ans:{i}"
            )
        ])

    progress = f"Вопрос {idx + 1}/{len(CAREER_TEST_QUESTIONS)}"
    text = (
        f"\U0001f3af <b>Тест профориентации</b>\n"
        f"<i>{progress}</i>\n\n"
        f"<b>{q['question']}</b>"
    )
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
    )
    return CAREER_TEST_PLAY


async def career_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    state = context.user_data.get("career_state")
    if not state:
        return MAIN_MENU

    answer_idx = int(query.data.split(":")[1])
    idx = state["current"]
    q = CAREER_TEST_QUESTIONS[idx]

    tags = q["answers"][answer_idx]["tags"]
    state["tags"].extend(tags)
    state["current"] += 1

    if state["current"] >= len(CAREER_TEST_QUESTIONS):
        return await _career_results(query, context)

    # Показать следующий вопрос
    return await career_next_question(update, context)


async def _career_results(query, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data["career_state"]
    tag_counts = Counter(state["tags"])

    if not tag_counts:
        top_tag = "engineer"
    else:
        top_tag = tag_counts.most_common(1)[0][0]

    result = CAREER_RESULTS.get(top_tag, CAREER_RESULTS["engineer"])

    # Все подходящие профессии (топ-3)
    top_3 = tag_counts.most_common(3)
    alternatives = ""
    if len(top_3) > 1:
        alternatives = "\n\n<b>Также тебе могут подойти:</b>\n"
        for tag, count in top_3[1:]:
            alt = CAREER_RESULTS.get(tag)
            if alt:
                alternatives += f"  \u2022 {alt['title']}\n"

    text = (
        f"\U0001f3af <b>Результат теста профориентации</b>\n\n"
        f"Тебе подходит профессия:\n\n"
        f"<b>{result['title']}</b>\n\n"
        f"{result['description']}"
        f"{alternatives}\n\n"
        f"\U0001f4b0 <b>+5 баллов</b> за прохождение теста!"
    )

    user_id = query.from_user.id
    await update_user_score(user_id, 5)
    await grant_achievement(user_id, "career_found", "\U0001f3af Профориентация")

    keyboard = [
        [InlineKeyboardButton("\U0001f504 Пройти ещё раз", callback_data="career_test")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]
    context.user_data.pop("career_state", None)

    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
    )
    return MAIN_MENU
