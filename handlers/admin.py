"""Админ-панель — создание викторин и квестов через бота."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS, MAIN_MENU, ADMIN_MENU,
    ADMIN_ADD_QUIZ_TITLE, ADMIN_ADD_QUIZ_QUESTION,
    ADMIN_ADD_QUIZ_ANSWERS, ADMIN_ADD_QUIZ_CORRECT, ADMIN_ADD_QUIZ_MORE,
    ADMIN_ADD_QUEST_TITLE, ADMIN_ADD_QUEST_STEP_TEXT,
    ADMIN_ADD_QUEST_STEP_ANSWER, ADMIN_ADD_QUEST_MORE,
)
from database import add_quiz, add_quest, get_all_quizzes, get_all_quests


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Нет доступа.", show_alert=True)
        else:
            await update.message.reply_text("У вас нет доступа к админ-панели.")
        return MAIN_MENU

    query = update.callback_query
    if query:
        await query.answer()

    quizzes = await get_all_quizzes()
    quests = await get_all_quests()

    text = (
        "\U0001f6e0 <b>Админ-панель</b>\n\n"
        f"Викторин: <b>{len(quizzes)}</b>\n"
        f"Квестов: <b>{len(quests)}</b>\n\n"
        "Выберите действие:"
    )
    keyboard = [
        [InlineKeyboardButton("\u2795 Добавить викторину", callback_data="admin_add_quiz")],
        [InlineKeyboardButton("\u2795 Добавить квест", callback_data="admin_add_quest")],
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
    return ADMIN_MENU


# ── Создание викторины ──

async def admin_add_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["admin_quiz"] = {
        "questions": [],
        "current_question": {},
    }
    await query.edit_message_text(
        "\U0001f4dd <b>Создание викторины</b>\n\n"
        "Введите <b>название</b> викторины:",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_TITLE


async def admin_quiz_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data["admin_quiz"]["title"] = title

    await update.message.reply_text(
        f"Название: <b>{title}</b>\n\n"
        "Теперь введите <b>текст вопроса</b>:",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_QUESTION


async def admin_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["admin_quiz"]["current_question"] = {
        "text": text,
        "options": [],
    }

    await update.message.reply_text(
        f"Вопрос: <i>{text}</i>\n\n"
        "Теперь введите <b>варианты ответов</b>, каждый с новой строки "
        "(минимум 2, максимум 4):",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_ANSWERS


async def admin_quiz_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [line.strip() for line in update.message.text.strip().split("\n") if line.strip()]
    if len(lines) < 2:
        await update.message.reply_text("Нужно минимум 2 варианта. Попробуйте ещё раз:")
        return ADMIN_ADD_QUIZ_ANSWERS

    context.user_data["admin_quiz"]["current_question"]["options"] = lines[:4]

    options_text = "\n".join(f"  {i + 1}) {opt}" for i, opt in enumerate(lines[:4]))
    await update.message.reply_text(
        f"Варианты:\n{options_text}\n\n"
        "Введите <b>номер правильного ответа</b> (1, 2, 3 или 4):",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_CORRECT


async def admin_quiz_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        correct_idx = int(update.message.text.strip()) - 1
        options = context.user_data["admin_quiz"]["current_question"]["options"]
        if correct_idx < 0 or correct_idx >= len(options):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Неверный номер. Попробуйте ещё раз:")
        return ADMIN_ADD_QUIZ_CORRECT

    cq = context.user_data["admin_quiz"]["current_question"]
    cq["correct"] = correct_idx
    cq["explanation"] = ""

    context.user_data["admin_quiz"]["questions"].append(cq)
    context.user_data["admin_quiz"]["current_question"] = {}

    count = len(context.user_data["admin_quiz"]["questions"])

    keyboard = [
        [InlineKeyboardButton("\u2795 Добавить ещё вопрос", callback_data="admin_quiz_more")],
        [InlineKeyboardButton("\u2705 Сохранить викторину", callback_data="admin_quiz_save")],
    ]
    await update.message.reply_text(
        f"\u2705 Вопрос добавлен! Всего вопросов: <b>{count}</b>\n\n"
        "Что дальше?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_MORE


async def admin_quiz_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Введите <b>текст следующего вопроса</b>:",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUIZ_QUESTION


async def admin_quiz_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("admin_quiz", {})
    title = data.get("title", "Без названия")
    questions = data.get("questions", [])

    if not questions:
        await query.edit_message_text("Нет вопросов для сохранения.")
        return ADMIN_MENU

    quiz_id = await add_quiz(
        title=title,
        description=f"Викторина ({len(questions)} вопросов)",
        questions=questions,
        created_by=query.from_user.id,
    )

    context.user_data.pop("admin_quiz", None)

    keyboard = [
        [InlineKeyboardButton("\U0001f6e0 Админ-панель", callback_data="admin_menu")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]
    await query.edit_message_text(
        f"\u2705 <b>Викторина сохранена!</b>\n\n"
        f"Название: {title}\n"
        f"Вопросов: {len(questions)}\n"
        f"ID: {quiz_id}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ADMIN_MENU


# ── Создание квеста ──

async def admin_add_quest_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["admin_quest"] = {
        "steps": [],
        "current_step": {},
    }
    await query.edit_message_text(
        "\U0001f4dd <b>Создание квеста</b>\n\n"
        "Введите <b>название</b> квеста:",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUEST_TITLE


async def admin_quest_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data["admin_quest"]["title"] = title

    await update.message.reply_text(
        f"Название: <b>{title}</b>\n\n"
        "Теперь введите <b>текст первого этапа</b> "
        "(описание + вопрос):",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUEST_STEP_TEXT


async def admin_quest_step_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["admin_quest"]["current_step"] = {
        "text": text,
    }

    await update.message.reply_text(
        "Теперь введите <b>правильный ответ</b> на этот этап "
        "(одно слово или фраза):",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUEST_STEP_ANSWER


async def admin_quest_step_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    step = context.user_data["admin_quest"]["current_step"]
    step["answer"] = answer
    step["hint"] = ""

    context.user_data["admin_quest"]["steps"].append(step)
    context.user_data["admin_quest"]["current_step"] = {}

    count = len(context.user_data["admin_quest"]["steps"])

    keyboard = [
        [InlineKeyboardButton("\u2795 Добавить ещё этап", callback_data="admin_quest_more")],
        [InlineKeyboardButton("\u2705 Сохранить квест", callback_data="admin_quest_save")],
    ]
    await update.message.reply_text(
        f"\u2705 Этап добавлен! Всего этапов: <b>{count}</b>\n\n"
        "Что дальше?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUEST_MORE


async def admin_quest_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Введите <b>текст следующего этапа</b>:",
        parse_mode="HTML",
    )
    return ADMIN_ADD_QUEST_STEP_TEXT


async def admin_quest_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("admin_quest", {})
    title = data.get("title", "Без названия")
    steps = data.get("steps", [])

    if not steps:
        await query.edit_message_text("Нет этапов для сохранения.")
        return ADMIN_MENU

    quest_id = await add_quest(
        title=title,
        description=f"Квест ({len(steps)} этапов)",
        steps=steps,
        reward_points=len(steps) * 5,
        created_by=query.from_user.id,
    )

    context.user_data.pop("admin_quest", None)

    keyboard = [
        [InlineKeyboardButton("\U0001f6e0 Админ-панель", callback_data="admin_menu")],
        [InlineKeyboardButton("\U0001f3e0 Главное меню", callback_data="back_to_menu")],
    ]
    await query.edit_message_text(
        f"\u2705 <b>Квест сохранён!</b>\n\n"
        f"Название: {title}\n"
        f"Этапов: {len(steps)}\n"
        f"Награда: {len(steps) * 5} баллов\n"
        f"ID: {quest_id}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ADMIN_MENU
