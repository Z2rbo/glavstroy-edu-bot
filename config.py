import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Состояния для ConversationHandler
(
    MAIN_MENU,
    EDUCATION_TOPIC,
    EDUCATION_DETAIL,
    QUIZ_SELECT,
    QUIZ_PLAY,
    QUEST_SELECT,
    QUEST_PLAY,
    POLL_SELECT,
    POLL_ANSWER,
    ADMIN_MENU,
    ADMIN_ADD_QUIZ_TITLE,
    ADMIN_ADD_QUIZ_QUESTION,
    ADMIN_ADD_QUIZ_ANSWERS,
    ADMIN_ADD_QUIZ_CORRECT,
    ADMIN_ADD_QUIZ_MORE,
    ADMIN_ADD_QUEST_TITLE,
    ADMIN_ADD_QUEST_STEP_TEXT,
    ADMIN_ADD_QUEST_STEP_ANSWER,
    ADMIN_ADD_QUEST_MORE,
    PROFILE_VIEW,
    LEADERBOARD,
    FACT_OF_DAY,
    CAREER_TEST,
    CAREER_TEST_PLAY,
) = range(24)
