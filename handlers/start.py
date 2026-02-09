"""Стартовое меню и основная навигация."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MAIN_MENU, PROFILE_VIEW, LEADERBOARD, FACT_OF_DAY, CAREER_TEST
from database import get_or_create_user


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4da Узнать о строительстве", callback_data="education")],
        [InlineKeyboardButton("\U0001f3af Пройти викторину", callback_data="quiz_list")],
        [InlineKeyboardButton("\U0001f5fa Пройти квест", callback_data="quest_list")],
        [InlineKeyboardButton("\U0001f4ca Опросы", callback_data="poll_list")],
        [InlineKeyboardButton("\U0001f3af Тест: Какая профессия тебе подходит?", callback_data="career_test")],
        [
            InlineKeyboardButton("\U0001f4a1 Факт дня", callback_data="fact_of_day"),
            InlineKeyboardButton("\U0001f3c6 Рейтинг", callback_data="leaderboard"),
        ],
        [InlineKeyboardButton("\U0001f464 Мой профиль", callback_data="profile")],
    ])


WELCOME_TEXT = (
    "\U0001f3d7 <b>Привет! Я — бот Главстрой Санкт-Петербург!</b>\n\n"
    "Я помогу тебе узнать всё о строительной отрасли "
    "в игровом формате:\n\n"
    "  \U0001f4da <b>Образование</b> — узнай, как строят дома, "
    "какие профессии существуют и какие технологии используются\n"
    "  \U0001f3af <b>Викторины</b> — проверь свои знания и заработай баллы\n"
    "  \U0001f5fa <b>Квесты</b> — пройди увлекательные задания\n"
    "  \U0001f4ca <b>Опросы</b> — поделись своим мнением\n"
    "  \U0001f3af <b>Профориентация</b> — узнай, какая профессия тебе подходит\n\n"
    "<i>Комплексные решения для развития города</i>\n\n"
    "Выбери действие:"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    context.user_data.clear()
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    return MAIN_MENU


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("quiz_state", None)
    context.user_data.pop("quest_state", None)
    context.user_data.pop("career_state", None)
    await query.edit_message_text(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    return MAIN_MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001f4d6 <b>Команды бота:</b>\n\n"
        "/start — Главное меню\n"
        "/help — Помощь\n"
        "/profile — Мой профиль\n"
        "/quiz — Список викторин\n"
        "/quest — Список квестов\n"
        "/fact — Факт дня\n"
        "/career — Тест на профессию\n\n"
        "<i>Образовательный бот от Главстрой СПб</i>",
        parse_mode="HTML",
    )
    return MAIN_MENU
