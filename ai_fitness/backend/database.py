"""
backend/database.py
--------------------
Async MongoDB client using Motor. Python 3.9 compatible.
"""

import logging
import os
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

log = logging.getLogger("backend.database")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME",   "ai_fitness")

_client: Optional[AsyncIOMotorClient]   = None
_db:     Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
    )
    _db = _client[DB_NAME]

    try:
        await _client.admin.command("ping")
        log.info("MongoDB connected -> %s  (db: %s)", MONGO_URI, DB_NAME)
    except Exception as exc:
        log.warning("MongoDB ping failed: %s — continuing anyway (DB calls will fail)", exc)


async def close_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db     = None
        log.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "Database not initialised. "
            "Call connect_db() in the app lifespan before serving requests."
        )
    return _db


def col_performance(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db["performance_scores"]


def col_sessions(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db["workout_sessions"]


def col_diet(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db["diet_plans"]


def col_habits(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db["habit_logs"]


def col_users(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    return db["users"]
