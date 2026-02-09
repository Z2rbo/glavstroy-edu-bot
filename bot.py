"""
Образовательный Telegram-бот «Главстрой Санкт-Петербург»
Конструктор викторин, опросов и квестов для школьников.

Запуск: python bot.py
"""

import logging
import sys

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    MAIN_MENU, EDUCATION_TOPIC, EDUCATION_DETAIL,
    QUIZ_SELECT, QUIZ_PLAY,
    QUEST_SELECT, QUEST_PLAY,
    POLL_SELECT, POLL_ANSWER,
    ADMIN_MENU,
    ADMIN_ADD_QUIZ_TITLE, ADMIN_ADD_QUIZ_QUESTION,
    ADMIN_ADD_QUIZ_ANSWERS, ADMIN_ADD_QUIZ_CORRECT, ADMIN_ADD_QUIZ_MORE,
    ADMIN_ADD_QUEST_TITLE, ADMIN_ADD_QUEST_STEP_TEXT,
    ADMIN_ADD_QUEST_STEP_ANSWER, ADMIN_ADD_QUEST_MORE,
    PROFILE_VIEW, LEADERBOARD, FACT_OF_DAY,
    CAREER_TEST, CAREER_TEST_PLAY,
)
from database import init_db, seed_default_data

from handlers.start import start, back_to_menu, help_command
from handlers.education import education_menu, topic_sections, section_detail
from handlers.quiz import quiz_list, quiz_start, quiz_answer, quiz_next
from handlers.quest import quest_list, quest_begin, quest_hint, quest_answer
from handlers.polls import poll_list, poll_send
from handlers.profile import (
    profile, leaderboard, fact_of_day,
    career_test_start, career_next_question, career_answer,
)
from handlers.admin import (
    admin_menu, admin_add_quiz_start, admin_quiz_title,
    admin_quiz_question, admin_quiz_answers, admin_quiz_correct,
    admin_quiz_more, admin_quiz_save,
    admin_add_quest_start, admin_quest_title,
    admin_quest_step_text, admin_quest_step_answer,
    admin_quest_more, admin_quest_save,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_conversation_handler() -> ConversationHandler:
    """Создаёт основной ConversationHandler со всеми состояниями."""

    # Общие callback-кнопки навигации, доступные из любого состояния
    back_to_menu_handler = CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$")

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            # ── Главное меню ──
            MAIN_MENU: [
                CallbackQueryHandler(education_menu, pattern="^education$"),
                CallbackQueryHandler(quiz_list, pattern="^quiz_list$"),
                CallbackQueryHandler(quiz_start, pattern=r"^quiz_start:\d+$"),
                CallbackQueryHandler(quest_list, pattern="^quest_list$"),
                CallbackQueryHandler(quest_begin, pattern=r"^quest_begin:\d+$"),
                CallbackQueryHandler(poll_list, pattern="^poll_list$"),
                CallbackQueryHandler(profile, pattern="^profile$"),
                CallbackQueryHandler(leaderboard, pattern="^leaderboard$"),
                CallbackQueryHandler(fact_of_day, pattern="^fact_of_day$"),
                CallbackQueryHandler(career_test_start, pattern="^career_test$"),
                CallbackQueryHandler(admin_menu, pattern="^admin_menu$"),
                back_to_menu_handler,
            ],

            # ── Образование ──
            EDUCATION_TOPIC: [
                CallbackQueryHandler(topic_sections, pattern=r"^edu_topic:"),
                CallbackQueryHandler(education_menu, pattern="^education$"),
                back_to_menu_handler,
            ],
            EDUCATION_DETAIL: [
                CallbackQueryHandler(section_detail, pattern=r"^edu_section:"),
                CallbackQueryHandler(topic_sections, pattern=r"^edu_topic:"),
                CallbackQueryHandler(education_menu, pattern="^education$"),
                back_to_menu_handler,
            ],

            # ── Викторины ──
            QUIZ_SELECT: [
                CallbackQueryHandler(quiz_start, pattern=r"^quiz_start:\d+$"),
                CallbackQueryHandler(quiz_list, pattern="^quiz_list$"),
                back_to_menu_handler,
            ],
            QUIZ_PLAY: [
                CallbackQueryHandler(quiz_answer, pattern=r"^quiz_answer:\d+$"),
                CallbackQueryHandler(quiz_next, pattern="^quiz_next$"),
                CallbackQueryHandler(quiz_start, pattern=r"^quiz_start:\d+$"),
                CallbackQueryHandler(quiz_list, pattern="^quiz_list$"),
                back_to_menu_handler,
            ],

            # ── Квесты ──
            QUEST_SELECT: [
                CallbackQueryHandler(quest_begin, pattern=r"^quest_begin:\d+$"),
                CallbackQueryHandler(quest_list, pattern="^quest_list$"),
                back_to_menu_handler,
            ],
            QUEST_PLAY: [
                CallbackQueryHandler(quest_hint, pattern="^quest_hint$"),
                CallbackQueryHandler(quest_list, pattern="^quest_list$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, quest_answer),
                back_to_menu_handler,
            ],

            # ── Опросы ──
            POLL_SELECT: [
                CallbackQueryHandler(poll_send, pattern=r"^poll_send:\d+$"),
                CallbackQueryHandler(poll_list, pattern="^poll_list$"),
                back_to_menu_handler,
            ],
            POLL_ANSWER: [
                CallbackQueryHandler(poll_list, pattern="^poll_list$"),
                back_to_menu_handler,
            ],

            # ── Профиль ──
            PROFILE_VIEW: [
                CallbackQueryHandler(leaderboard, pattern="^leaderboard$"),
                CallbackQueryHandler(profile, pattern="^profile$"),
                back_to_menu_handler,
            ],
            LEADERBOARD: [
                CallbackQueryHandler(profile, pattern="^profile$"),
                back_to_menu_handler,
            ],

            # ── Факт дня ──
            FACT_OF_DAY: [
                CallbackQueryHandler(fact_of_day, pattern="^fact_of_day$"),
                back_to_menu_handler,
            ],

            # ── Профориентация ──
            CAREER_TEST: [
                CallbackQueryHandler(career_next_question, pattern="^career_next$"),
                CallbackQueryHandler(career_test_start, pattern="^career_test$"),
                back_to_menu_handler,
            ],
            CAREER_TEST_PLAY: [
                CallbackQueryHandler(career_answer, pattern=r"^career_ans:\d+$"),
                CallbackQueryHandler(career_test_start, pattern="^career_test$"),
                back_to_menu_handler,
            ],

            # ── Админка ──
            ADMIN_MENU: [
                CallbackQueryHandler(admin_add_quiz_start, pattern="^admin_add_quiz$"),
                CallbackQueryHandler(admin_add_quest_start, pattern="^admin_add_quest$"),
                CallbackQueryHandler(admin_menu, pattern="^admin_menu$"),
                back_to_menu_handler,
            ],
            ADMIN_ADD_QUIZ_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quiz_title),
            ],
            ADMIN_ADD_QUIZ_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quiz_question),
            ],
            ADMIN_ADD_QUIZ_ANSWERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quiz_answers),
            ],
            ADMIN_ADD_QUIZ_CORRECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quiz_correct),
            ],
            ADMIN_ADD_QUIZ_MORE: [
                CallbackQueryHandler(admin_quiz_more, pattern="^admin_quiz_more$"),
                CallbackQueryHandler(admin_quiz_save, pattern="^admin_quiz_save$"),
            ],
            ADMIN_ADD_QUEST_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quest_title),
            ],
            ADMIN_ADD_QUEST_STEP_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quest_step_text),
            ],
            ADMIN_ADD_QUEST_STEP_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_quest_step_answer),
            ],
            ADMIN_ADD_QUEST_MORE: [
                CallbackQueryHandler(admin_quest_more, pattern="^admin_quest_more$"),
                CallbackQueryHandler(admin_quest_save, pattern="^admin_quest_save$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CommandHandler("profile", lambda u, c: profile(u, c)),
            CommandHandler("quiz", lambda u, c: quiz_list(u, c)),
            CommandHandler("quest", lambda u, c: quest_list(u, c)),
            CommandHandler("fact", lambda u, c: fact_of_day(u, c)),
            CommandHandler("career", lambda u, c: career_test_start(u, c)),
            CommandHandler("admin", lambda u, c: admin_menu(u, c)),
        ],
        per_message=False,
    )


async def post_init(application):
    """Инициализация БД и загрузка данных при старте."""
    logger.info("Инициализация базы данных...")
    await init_db()
    await seed_default_data()
    logger.info("База данных готова. Бот запущен!")

    # Установка команд бота
    from telegram import BotCommand
    commands = [
        BotCommand("start", "Главное меню"),
        BotCommand("help", "Помощь"),
        BotCommand("profile", "Мой профиль"),
        BotCommand("quiz", "Викторины"),
        BotCommand("quest", "Квесты"),
        BotCommand("fact", "Факт дня"),
        BotCommand("career", "Тест на профессию"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    if not BOT_TOKEN:
        print("ОШИБКА: Не задан BOT_TOKEN!")
        print("Создайте файл .env с содержимым:")
        print("  BOT_TOKEN=ваш_токен_от_BotFather")
        sys.exit(1)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    conv_handler = build_conversation_handler()
    application.add_handler(conv_handler)

    logger.info("Запуск бота в режиме Long Polling...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
