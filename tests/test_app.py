"""Smoke and contract tests for the Flask application in app.py."""

from http import HTTPStatus
from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.test import TestResponse

from app import create_app
from db import get_connection, save_transcript

NOT_IMPLEMENTED_CODE = "not_implemented"


def error_code(client_response: TestResponse) -> str:
    """Pull the error code out of the shared error body."""
    return str(client_response.get_json()["error"]["code"])


def test_index_returns_html(tmp_path: Path) -> None:
    """GET / serves the frontend placeholder as HTML."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert response.content_type.startswith("text/html")


def test_health_returns_ok(tmp_path: Path) -> None:
    """GET /api/health returns the health-check JSON."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"status": "ok"}


def test_transcribe_rejects_missing_audio(tmp_path: Path) -> None:
    """POST /api/transcribe without an audio file is a 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/transcribe", data={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "missing_audio"


def test_transcribe_success_returns_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /api/transcribe with audio transcribes and returns the transcript."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()
    monkeypatch.setattr(
        "app.services.transcribe_audio",
        lambda audio, mime_type: "I missed the bus.",
    )

    response = client.post(
        "/api/transcribe",
        data={"audio": (BytesIO(b"fake-audio-bytes"), "story.webm")},
        content_type="multipart/form-data",
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"transcript": "I missed the bus."}


def test_transcribe_persists_transcript(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful transcribe saves the transcript to SQLite."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    monkeypatch.setattr(
        "app.services.transcribe_audio",
        lambda audio, mime_type: "I burnt the toast.",
    )

    client.post(
        "/api/transcribe",
        data={"audio": (BytesIO(b"fake-audio-bytes"), "story.webm")},
        content_type="multipart/form-data",
    )

    connection = get_connection(db_file)
    rows = connection.execute("SELECT raw_text FROM transcripts").fetchall()
    connection.close()

    assert len(rows) == 1
    assert rows[0]["raw_text"] == "I burnt the toast."


def test_rewrite_rejects_missing_transcript(tmp_path: Path) -> None:
    """POST /api/rewrite without a transcript is a 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/rewrite", json={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "missing_transcript"


def test_rewrite_rejects_blank_transcript(tmp_path: Path) -> None:
    """POST /api/rewrite with a blank transcript is a 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/rewrite", json={"transcript": "   "})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "missing_transcript"


def test_rewrite_success_returns_story(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/rewrite with transcript returns the story and saves it."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I missed the bus.", db_path=db_file)
    monkeypatch.setattr(
        "app.services.rewrite_story",
        lambda transcript: "THE BUS FEARED HIM.",
    )

    response = client.post("/api/rewrite", json={"transcript": "I missed the bus."})

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"story": "THE BUS FEARED HIM."}


def test_rewrite_persists_story(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful rewrite saves the story linked to the transcript."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I burnt the toast.", db_path=db_file)
    monkeypatch.setattr(
        "app.services.rewrite_story",
        lambda transcript: "THE TOAST WAS INNOCENT.",
    )

    client.post("/api/rewrite", json={"transcript": "I burnt the toast."})

    connection = get_connection(db_file)
    rows = connection.execute("SELECT story_text FROM stories").fetchall()
    connection.close()

    assert len(rows) == 1
    assert rows[0]["story_text"] == "THE TOAST WAS INNOCENT."


def test_narrate_rejects_missing_story(tmp_path: Path) -> None:
    """POST /api/narrate without a story is a 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/narrate", json={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "missing_story"


def test_narrate_rejects_blank_story(tmp_path: Path) -> None:
    """POST /api/narrate with a blank story is a 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/narrate", json={"story": "  "})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "missing_story"


def test_narrate_stub_returns_501(tmp_path: Path) -> None:
    """POST /api/narrate with a valid story hits the not-implemented stub."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/narrate", json={"story": "THE BUS FEARED HIM."})

    assert response.status_code == HTTPStatus.NOT_IMPLEMENTED
    assert error_code(response) == NOT_IMPLEMENTED_CODE
