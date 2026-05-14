"""SQLite helpers for storing Telegram users and request counters."""

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Small async wrapper around SQLite user counters."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def init(self) -> None:
        """Create the users table if it does not exist yet."""
        # Create the parent directory when DATABASE_PATH points to a nested file.
        db_parent = Path(self.db_path).parent
        if db_parent != Path("."):
            db_parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    requests_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            await db.commit()
        logger.info("Database initialized: %s", self.db_path)

    async def add_user(self, user_id: int) -> None:
        """Register a user with zero requests if the user is new."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, requests_count) VALUES (?, 0)",
                (user_id,),
            )
            await db.commit()

    async def get_requests_count(self, user_id: int) -> int:
        """Return how many successful generations the user has made."""
        await self.add_user(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT requests_count FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def increment_requests_count(self, user_id: int) -> int:
        """Increment the request counter and return its new value."""
        await self.add_user(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET requests_count = requests_count + 1 WHERE user_id = ?",
                (user_id,),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT requests_count FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
        new_count = int(row[0]) if row else 0
        logger.info("User %s request counter incremented to %s", user_id, new_count)
        return new_count
