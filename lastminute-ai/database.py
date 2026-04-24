"""
database.py — SQLite metadata store for sessions and documents
"""

import aiosqlite
import os

DB_PATH = "./lastminute.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                created_at  TEXT DEFAULT (datetime('now')),
                label       TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL,
                filename    TEXT NOT NULL,
                file_type   TEXT NOT NULL,
                page_count  INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                uploaded_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qa_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                question    TEXT NOT NULL,
                answer      TEXT NOT NULL,
                sources     TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS practice_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                question    TEXT NOT NULL,
                student_ans TEXT,
                score       INTEGER,
                feedback    TEXT,
                topic       TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
