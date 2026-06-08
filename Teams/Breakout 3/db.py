import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "budget.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL DEFAULT (date('now')),
                amount   REAL    NOT NULL,
                category TEXT    NOT NULL,
                note     TEXT    NOT NULL DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                date   TEXT    NOT NULL DEFAULT (date('now')),
                amount REAL    NOT NULL,
                source TEXT    NOT NULL DEFAULT '',
                note   TEXT    NOT NULL DEFAULT ''
            )
        """)
