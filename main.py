"""Entry point for the marketplace description Telegram bot."""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from database.db import Database
from handlers.user import router as user_router
from services.ai import AIService


DEFAULT_DATABASE_PATH = "bot.db"
DEFAULT_OPENAI_MODEL = "gpt-5.1"


def setup_logging() -> None:
    """Configure application logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_required_env(name: str) -> str:
    """Read a required environment variable or raise a clear startup error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


async def main() -> None:
    """Initialize dependencies and start long polling."""
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)

    bot_token = get_required_env("BOT_TOKEN")
    openai_api_key = get_required_env("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    database_path = os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)

    db = Database(database_path)
    await db.init()

    ai_service = AIService(api_key=openai_api_key, model=openai_model)

    # Do not set a parse mode globally: AI text can contain characters
    # that Telegram would otherwise interpret as markup.
    bot = Bot(token=bot_token)
    dp = Dispatcher(db=db, ai_service=ai_service)
    dp.include_router(user_router)

    logger.info("Bot started with OpenAI model: %s", openai_model)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped")
