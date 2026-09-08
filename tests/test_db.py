"""Tests for the SQLite schema, database init, and save/fetch functions in db.py."""

import sqlite3
from pathlib import Path

import pytest

from db import (
    DB_PATH,
    fetch_story,
    fetch_transcript,
    get_connection,
    init_db,
    list_stories,
    save_story,
    save_transcript,
)
from models import Story, Transcript

EXPECTED_TABLES = {"transcripts", "stories", "metadata"}
MIN_TABLE_COUNT = 3


def test_init_db_creates_all_tables(tmp_path: Path) -> None:
    """init_db() must create transcripts, stories, and metadata."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    connection = get_connection(db_file)
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    connection.close()

    assert tables >= EXPECTED_TABLES


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    """Calling init_db() twice must not raise and must keep the tables."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    init_db(db_file)

    connection = get_connection(db_file)
    table_count = connection.execute(
        "SELECT count(*) FROM sqlite_master WHERE type = 'table'"
    ).fetchone()[0]
    connection.close()

    assert table_count >= MIN_TABLE_COUNT


def test_transcripts_table_has_expected_columns(tmp_path: Path) -> None:
    """The transcripts table needs the columns the app will use later."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    connection = get_connection(db_file)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(transcripts)")}
    connection.close()

    assert {"id", "raw_text", "created_at"} <= columns


def test_stories_table_links_to_transcripts(tmp_path: Path) -> None:
    """The stories table must reference transcripts and hold story text."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    connection = get_connection(db_file)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(stories)")}
    connection.close()

    assert {"id", "transcript_id", "story_text", "created_at", "absurdity"} <= columns
    assert "headline" in columns


def test_init_db_upgrades_old_stories_schema(tmp_path: Path) -> None:
    """init_db adds the absurdity column to an old-schema DB without data loss.

    Existing rows get the 'unhinged' default, and the upgrade is idempotent.
    """
    db_file = tmp_path / "interestingifier.db"
    connection = sqlite3.connect(db_file)
    connection.executescript(
        """
        CREATE TABLE transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript_id INTEGER NOT NULL REFERENCES transcripts(id),
            story_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO transcripts (raw_text) VALUES ('I missed the bus.');
        INSERT INTO stories (transcript_id, story_text) VALUES (1, 'THE BUS FEARED HIM.');
        """
    )
    connection.commit()
    connection.close()

    init_db(db_file)
    init_db(db_file)

    connection = get_connection(db_file)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(stories)")}
    value = connection.execute("SELECT absurdity FROM stories WHERE id = 1").fetchone()["absurdity"]
    headline_value = connection.execute("SELECT headline FROM stories WHERE id = 1").fetchone()[
        "headline"
    ]
    connection.close()

    assert "absurdity" in columns
    assert value == "unhinged"
    assert "headline" in columns
    assert headline_value == ""


def test_default_db_path_is_interestingifier_db() -> None:
    """The default database file name is interestingifier.db."""
    assert DB_PATH.name == "interestingifier.db"


def test_save_transcript_returns_stored_row(tmp_path: Path) -> None:
    """save_transcript returns a Transcript with DB-populated id and created_at."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    transcript = save_transcript("I missed the bus.", db_path=db_file)

    assert isinstance(transcript, Transcript)
    assert transcript.raw_text == "I missed the bus."
    assert transcript.id > 0
    assert transcript.created_at


def test_fetch_transcript_returns_saved_transcript(tmp_path: Path) -> None:
    """fetch_transcript returns the transcript that was saved before."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    saved = save_transcript("I burnt the toast.", db_path=db_file)

    fetched = fetch_transcript(saved.id, db_path=db_file)

    assert fetched == saved


def test_fetch_transcript_missing_returns_none(tmp_path: Path) -> None:
    """fetch_transcript returns None for an id that does not exist."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    assert fetch_transcript(999999, db_path=db_file) is None


def test_save_transcript_persists_across_connections(tmp_path: Path) -> None:
    """A fresh connection can read back what save_transcript wrote."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    saved = save_transcript("I got locked out.", db_path=db_file)

    connection = get_connection(db_file)
    stored = connection.execute(
        "SELECT raw_text FROM transcripts WHERE id = ?", (saved.id,)
    ).fetchone()
    connection.close()

    assert stored is not None
    assert stored["raw_text"] == "I got locked out."


def test_save_story_returns_stored_row(tmp_path: Path) -> None:
    """save_story returns a Story with DB-populated id and created_at."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I missed the bus.", db_path=db_file)

    story = save_story(transcript.id, "THE BUS FEARED HIM.", db_path=db_file)

    assert isinstance(story, Story)
    assert story.transcript_id == transcript.id
    assert story.story_text == "THE BUS FEARED HIM."
    assert story.id > 0
    assert story.created_at


def test_save_story_persists_absurdity(tmp_path: Path) -> None:
    """save_story stores the chosen absurdity and fetch/list return it."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I missed the bus.", db_path=db_file)

    saved = save_story(
        transcript.id, "THE BUS FEARED HIM.", absurdity="total_fever_dream", db_path=db_file
    )

    assert saved.absurdity == "total_fever_dream"
    assert fetch_story(saved.id, db_path=db_file) == saved
    assert list_stories(db_path=db_file) == [saved]


def test_save_story_defaults_to_unhinged(tmp_path: Path) -> None:
    """save_story without an absurdity stores 'unhinged'."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I missed the bus.", db_path=db_file)

    saved = save_story(transcript.id, "THE BUS FEARED HIM.", db_path=db_file)

    assert saved.absurdity == "unhinged"
    assert fetch_story(saved.id, db_path=db_file) == saved


def test_save_story_persists_headline(tmp_path: Path) -> None:
    """save_story stores a headline and fetch/list return it."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I missed the bus.", db_path=db_file)

    saved = save_story(
        transcript.id, "THE BUS FEARED HIM.", headline="BUSES TREMBLE!", db_path=db_file
    )

    assert saved.headline == "BUSES TREMBLE!"
    assert fetch_story(saved.id, db_path=db_file) == saved
    assert list_stories(db_path=db_file) == [saved]


def test_save_story_defaults_headline_to_empty(tmp_path: Path) -> None:
    """save_story without a headline stores an empty one."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I missed the bus.", db_path=db_file)

    saved = save_story(transcript.id, "THE BUS FEARED HIM.", db_path=db_file)

    assert saved.headline == ""
    assert fetch_story(saved.id, db_path=db_file) == saved


def test_fetch_story_returns_saved_story(tmp_path: Path) -> None:
    """fetch_story returns the story that was saved before."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    transcript = save_transcript("I burnt the toast.", db_path=db_file)
    saved = save_story(transcript.id, "THE TOAST WAS INNOCENT.", db_path=db_file)

    fetched = fetch_story(saved.id, db_path=db_file)

    assert fetched == saved


def test_fetch_story_missing_returns_none(tmp_path: Path) -> None:
    """fetch_story returns None for an id that does not exist."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    assert fetch_story(999999, db_path=db_file) is None


def test_save_story_rejects_missing_transcript(tmp_path: Path) -> None:
    """save_story must not save a story for a transcript that does not exist."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    with pytest.raises(sqlite3.IntegrityError):
        save_story(999999, "A DANGLING STORY.", db_path=db_file)


def test_list_stories_empty_returns_empty_list(tmp_path: Path) -> None:
    """list_stories returns an empty list when nothing has been saved."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    assert list_stories(db_path=db_file) == []


def test_list_stories_returns_stories_newest_first(tmp_path: Path) -> None:
    """list_stories returns every story, most recently saved first."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)
    first_transcript = save_transcript("First anecdote.", db_path=db_file)
    second_transcript = save_transcript("Second anecdote.", db_path=db_file)
    first_story = save_story(first_transcript.id, "FIRST STORY.", db_path=db_file)
    second_story = save_story(second_transcript.id, "SECOND STORY.", db_path=db_file)

    stories = list_stories(db_path=db_file)

    assert stories == [second_story, first_story]


def test_save_and_fetch_round_trip(tmp_path: Path) -> None:
    """A transcript and story survive a full save-then-fetch round trip."""
    db_file = tmp_path / "interestingifier.db"
    init_db(db_file)

    transcript = save_transcript("I got locked out of my flat.", db_path=db_file)
    story = save_story(transcript.id, "THE DOOR DECLARED WAR.", db_path=db_file)

    fetched_transcript = fetch_transcript(transcript.id, db_path=db_file)
    fetched_story = fetch_story(story.id, db_path=db_file)

    assert fetched_transcript == transcript
    assert fetched_story == story
