import asyncio
import os

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import MenuButtonCommands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в .env")


async def main():
    session = AiohttpSession(timeout=60)
    bot = Bot(token=TOKEN, session=session)

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonCommands()
        )

        print("✅ Web App / Play-кнопка убрана.")
        print("✅ Установлено стандартное меню команд.")

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())