"""SQLite connection manager with WAL configuration for SENTIENT_OS v2."""

import os
from pathlib import Path
from typing import Optional
import aiosqlite

from src.infrastructure.logger import get_logger
from .models import SCHEMA_SQL

logger = get_logger("database")


class DatabaseManager:
    """Manages async SQLite connections and schema initialization."""

    def __init__(self, db_path: str = "data/sentient.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> aiosqlite.Connection:
        """Establish database connection with mandatory performance and safety PRAGMAs."""
        if self._conn is not None:
            return self._conn

        # Ensure directory exists if not memory database
        if self.db_path != ":memory:":
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

        # Apply mandatory PRAGMAs
        if self.db_path != ":memory:":
            await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA busy_timeout=5000;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA cache_size=-64000;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")

        # Initialize schema
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.commit()

        logger.info(f"Connected to database at {self.db_path} with WAL configuration")
        return self._conn

    async def close(self) -> None:
        """Close connection cleanly."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn


async def init_database(db_path: str = "data/sentient.db") -> DatabaseManager:
    """Helper factory to initialize and connect database."""
    manager = DatabaseManager(db_path)
    await manager.connect()
    return manager
