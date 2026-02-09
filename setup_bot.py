"""Set bot avatar, description, commands via Telegram Bot API."""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot, BotCommand
from telegram.constants import ParseMode

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(token=TOKEN)

    # 1. Set profile photo (avatar)
    avatar_path = os.path.join(os.path.dirname(__file__), "avatar.png")
    if os.path.exists(avatar_path):
        print("Setting bot avatar...")
        with open(avatar_path, "rb") as f:
            # Use raw API call — setChatPhoto doesn't work for bots
            # We'll use BotFather approach instead via setMyProfilePhoto (not in PTB)
            # PTB doesn't have this method, use raw HTTP
            pass
        print("NOTE: Bot avatar must be set manually via @BotFather -> /setuserpic")
    else:
        print("Avatar file not found!")

    # 2. Set bot description (shown when user opens bot for the first time)
    print("Setting bot description...")
    await bot.set_my_description(
        description=(
            "🏗 Образовательный бот от Главстрой Санкт-Петербург!\n\n"
            "Узнай всё о строительной отрасли в игровом формате:\n"
            "📚 Интересные статьи о строительстве\n"
            "🎯 Викторины с баллами и достижениями\n"
            "🗺 Увлекательные квесты\n"
            "📊 Опросы\n"
            "🎯 Тест профориентации — узнай свою профессию!\n\n"
            "Комплексные решения для развития города"
        )
    )
    print("✅ Description set!")

    # 3. Set short description (shown in search results, forwarded messages)
    print("Setting short description...")
    await bot.set_my_short_description(
        short_description=(
            "🏗 Образовательный бот Главстрой СПб — "
            "викторины, квесты и факты о строительстве для школьников!"
        )
    )
    print("✅ Short description set!")

    # 4. Set commands
    print("Setting bot commands...")
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("help", "📖 Помощь"),
        BotCommand("profile", "👤 Мой профиль"),
        BotCommand("quiz", "🎯 Викторины"),
        BotCommand("quest", "🗺 Квесты"),
        BotCommand("fact", "💡 Факт дня"),
        BotCommand("career", "🎯 Тест на профессию"),
        BotCommand("admin", "🛠 Админ-панель"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Commands set!")

    # 5. Set bot name
    print("Setting bot name...")
    try:
        await bot.set_my_name(name="Главстрой СПб | Образование")
        print("✅ Bot name set!")
    except Exception as e:
        print(f"⚠️ Could not set name: {e}")

    print("\n🎉 All done! Only the avatar needs to be set manually via @BotFather -> /setuserpic")
    await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
