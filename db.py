"""Chinook music store SQLite database setup."""

from pathlib import Path
import sqlite3

import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from seed_mini_db import DB_PATH, build_mini_chinook

CHINOOK_SQL_URL = (
    "https://raw.githubusercontent.com/lerocha/chinook-database/master/"
    "ChinookDatabase/DataSources/Chinook_Sqlite.sql"
)
LOCAL_SQL = Path(__file__).resolve().parent / "data" / "Chinook_Sqlite.sql"

_engine = None
_db = None


def _load_sql_script() -> str | None:
    if LOCAL_SQL.exists():
        return LOCAL_SQL.read_text(encoding="utf-8")
    try:
        response = requests.get(CHINOOK_SQL_URL, timeout=60)
        response.raise_for_status()
        LOCAL_SQL.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_SQL.write_text(response.text, encoding="utf-8")
        return response.text
    except Exception:
        return None


def get_engine_for_chinook_db():
    """
    Prefer full Chinook SQL (local cache or download).
    Fall back to a bundled mini Chinook DB if the network is unavailable.
    """
    sql_script = _load_sql_script()
    if sql_script:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.executescript(sql_script)
        return create_engine(
            "sqlite://",
            creator=lambda: connection,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

    # Offline fallback
    if not DB_PATH.exists():
        build_mini_chinook()
    return create_engine(
        f"sqlite:///{DB_PATH.as_posix()}",
        connect_args={"check_same_thread": False},
    )


def get_db() -> SQLDatabase:
    """Return a shared LangChain SQLDatabase instance."""
    global _engine, _db
    if _db is None:
        _engine = get_engine_for_chinook_db()
        _db = SQLDatabase(_engine)
    return _db


def run_query(sql: str) -> str:
    """Run a SQL query and return the LangChain SQLDatabase result string."""
    return get_db().run(sql)
