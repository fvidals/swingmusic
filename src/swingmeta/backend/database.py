import contextlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Generator
from config import settings


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """
    Returns a SQLite connection configured with WAL mode and foreign keys.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextlib.contextmanager
def swing_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for swingmusic.db
    """
    conn = get_db_connection(settings.swingmusic_db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def user_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for userdata tables (artistdata, user, playlist).
    Uses userdata.db if it exists as a separate file, or falls back to swingmusic.db
    where all tables live in modern SwingMusic.
    """
    db_path = settings.userdata_db_path if settings.userdata_db_path.exists() else settings.swingmusic_db_path
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def ensure_database_tables():
    """
    Ensures that the required tables exist in userdata / swingmusic database.
    """
    db_path = settings.userdata_db_path if settings.userdata_db_path.exists() else settings.swingmusic_db_path
    if db_path.exists():
        with user_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artistdata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itemhash VARCHAR UNIQUE,
                    itemtype VARCHAR,
                    color VARCHAR,
                    bio VARCHAR,
                    info JSON,
                    extra JSON
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_artistdata_itemhash ON artistdata (itemhash);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS playlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR,
                    last_updated INTEGER,
                    image VARCHAR,
                    userid INTEGER DEFAULT 1,
                    settings JSON,
                    trackhashes JSON,
                    extra JSON
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_playlist_name ON playlist (name);")
            conn.commit()
