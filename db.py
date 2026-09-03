"""SQLite persistence for Interestingifier.

This module owns the database: where it lives, how to connect, and the schema.
Later steps add save/fetch functions on top of these foundations.
"""

import sqlite3
from pathlib import Path

from logging_config import logged
from models import Story, Transcript

DB_PATH = Path("interestingifier.db")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection to the SQLite database at db_path.

    Rows come back as sqlite3.Row so columns can be read by name
    (row["raw_text"]) instead of by index — easier to read and to keep correct.
    """
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path = DB_PATH) -> None:
    """Create the database tables if they do not already exist.

    Safe to call on every startup — it does nothing to existing data.
    """
    connection = get_connection(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript_id INTEGER NOT NULL REFERENCES transcripts(id),
                story_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


@logged
def save_transcript(raw_text: str, db_path: Path = DB_PATH) -> Transcript:
    """Save a transcript and return the stored row, id and created_at included."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            "INSERT INTO transcripts (raw_text) VALUES (?)",
            (raw_text,),
        )
        connection.commit()
        assert cursor.lastrowid is not None
        transcript_id = int(cursor.lastrowid)
        row = connection.execute(
            "SELECT id, raw_text, created_at FROM transcripts WHERE id = ?",
            (transcript_id,),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return Transcript(id=row["id"], raw_text=row["raw_text"], created_at=row["created_at"])


@logged
def fetch_latest_transcript_id(db_path: Path = DB_PATH) -> int | None:
    """Return the ID of the most recently saved transcript, or None if none exist."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT id FROM transcripts ORDER BY id DESC LIMIT 1").fetchone()
    finally:
        connection.close()
    return int(row["id"]) if row else None


@logged
def fetch_transcript(transcript_id: int, db_path: Path = DB_PATH) -> Transcript | None:
    """Return the transcript with the given id, or None if it does not exist."""
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT id, raw_text, created_at FROM transcripts WHERE id = ?",
            (transcript_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return Transcript(id=row["id"], raw_text=row["raw_text"], created_at=row["created_at"])


@logged
def save_story(transcript_id: int, story_text: str, db_path: Path = DB_PATH) -> Story:
    """Save a story linked to an existing transcript and return the stored row.

    Raises sqlite3.IntegrityError if transcript_id does not exist (the schema's
    foreign key), so a story can never dangle without its transcript.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            "INSERT INTO stories (transcript_id, story_text) VALUES (?, ?)",
            (transcript_id, story_text),
        )
        connection.commit()
        assert cursor.lastrowid is not None
        story_id = int(cursor.lastrowid)
        row = connection.execute(
            "SELECT id, transcript_id, story_text, created_at FROM stories WHERE id = ?",
            (story_id,),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return Story(
        id=row["id"],
        transcript_id=row["transcript_id"],
        story_text=row["story_text"],
        created_at=row["created_at"],
    )


@logged
def fetch_story(story_id: int, db_path: Path = DB_PATH) -> Story | None:
    """Return the story with the given id, or None if it does not exist."""
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT id, transcript_id, story_text, created_at FROM stories WHERE id = ?",
            (story_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return Story(
        id=row["id"],
        transcript_id=row["transcript_id"],
        story_text=row["story_text"],
        created_at=row["created_at"],
    )


@logged
def list_stories(db_path: Path = DB_PATH) -> list[Story]:
    """Return every saved story, newest first, ready for the history area."""
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            "SELECT id, transcript_id, story_text, created_at FROM stories ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()
    return [
        Story(
            id=row["id"],
            transcript_id=row["transcript_id"],
            story_text=row["story_text"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
