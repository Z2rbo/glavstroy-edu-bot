import aiosqlite
import os
import json
from config import DB_PATH


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                score INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0,
                quests_completed INTEGER DEFAULT 0,
                polls_answered INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                last_active TEXT,
                registered_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                questions TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quiz_id INTEGER,
                score INTEGER,
                total INTEGER,
                completed_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                steps TEXT NOT NULL,
                reward_points INTEGER DEFAULT 10,
                created_by INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS quest_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quest_id INTEGER,
                current_step INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            );

            CREATE TABLE IF NOT EXISTS poll_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                poll_id TEXT,
                answer TEXT,
                answered_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge_id TEXT,
                badge_name TEXT,
                earned_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        await db.commit()


async def get_or_create_user(user_id: int, username: str = None,
                              first_name: str = None, last_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, last_name)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
        else:
            await db.execute(
                "UPDATE users SET last_active = datetime('now') WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
        return dict(user)


async def update_user_score(user_id: int, points: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET score = score + ? WHERE user_id = ?",
            (points, user_id)
        )
        await db.commit()


async def increment_stat(user_id: int, field: str):
    allowed = ["quizzes_completed", "quests_completed", "polls_answered"]
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {field} = {field} + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(await cursor.fetchone()) if await cursor.fetchone() is None else None


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_leaderboard(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users ORDER BY score DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# --- Quizzes ---

async def get_all_quizzes():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM quizzes ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_quiz(quiz_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_quiz(title: str, description: str, questions: list, created_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO quizzes (title, description, questions, created_by) VALUES (?, ?, ?, ?)",
            (title, description, json.dumps(questions, ensure_ascii=False), created_by)
        )
        await db.commit()
        return cursor.lastrowid


async def save_quiz_result(user_id: int, quiz_id: int, score: int, total: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO quiz_results (user_id, quiz_id, score, total) VALUES (?, ?, ?, ?)",
            (user_id, quiz_id, score, total)
        )
        await db.commit()


async def get_user_quiz_results(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT qr.*, q.title FROM quiz_results qr
               JOIN quizzes q ON qr.quiz_id = q.id
               WHERE qr.user_id = ? ORDER BY qr.completed_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# --- Quests ---

async def get_all_quests():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM quests ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_quest(quest_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_quest(title: str, description: str, steps: list,
                     reward_points: int = 10, created_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO quests (title, description, steps, reward_points, created_by) VALUES (?, ?, ?, ?, ?)",
            (title, description, json.dumps(steps, ensure_ascii=False), reward_points, created_by)
        )
        await db.commit()
        return cursor.lastrowid


async def get_quest_progress(user_id: int, quest_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM quest_progress WHERE user_id = ? AND quest_id = ? AND completed = 0",
            (user_id, quest_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def start_quest(user_id: int, quest_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO quest_progress (user_id, quest_id, current_step) VALUES (?, ?, 0)",
            (user_id, quest_id)
        )
        await db.commit()


async def advance_quest(user_id: int, quest_id: int, new_step: int, completed: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        if completed:
            await db.execute(
                """UPDATE quest_progress SET current_step = ?, completed = 1,
                   completed_at = datetime('now')
                   WHERE user_id = ? AND quest_id = ? AND completed = 0""",
                (new_step, user_id, quest_id)
            )
        else:
            await db.execute(
                "UPDATE quest_progress SET current_step = ? WHERE user_id = ? AND quest_id = ? AND completed = 0",
                (new_step, user_id, quest_id)
            )
        await db.commit()


# --- Achievements ---

async def grant_achievement(user_id: int, badge_id: str, badge_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM achievements WHERE user_id = ? AND badge_id = ?",
            (user_id, badge_id)
        )
        if await cursor.fetchone():
            return False
        await db.execute(
            "INSERT INTO achievements (user_id, badge_id, badge_name) VALUES (?, ?, ?)",
            (user_id, badge_id, badge_name)
        )
        await db.commit()
        return True


async def get_user_achievements(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# --- Seed data ---

async def seed_default_data():
    from data.content import DEFAULT_QUIZZES, DEFAULT_QUESTS
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM quizzes")
        count = (await cursor.fetchone())[0]
        if count == 0:
            for q in DEFAULT_QUIZZES:
                await db.execute(
                    "INSERT INTO quizzes (title, description, questions) VALUES (?, ?, ?)",
                    (q["title"], q["description"],
                     json.dumps(q["questions"], ensure_ascii=False))
                )
            for quest in DEFAULT_QUESTS:
                await db.execute(
                    "INSERT INTO quests (title, description, steps, reward_points) VALUES (?, ?, ?, ?)",
                    (quest["title"], quest["description"],
                     json.dumps(quest["steps"], ensure_ascii=False), quest["reward_points"])
                )
            await db.commit()
