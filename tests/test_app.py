"""Smoke and contract tests for the Flask application in app.py."""

from http import HTTPStatus
from io import BytesIO
from pathlib import Path

from werkzeug.test import TestResponse

from app import create_app

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


def test_transcribe_stub_returns_501(tmp_path: Path) -> None:
    """POST /api/transcribe with audio hits the not-implemented stub."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post(
        "/api/transcribe",
        data={"audio": (BytesIO(b"fake-audio-bytes"), "story.webm")},
        content_type="multipart/form-data",
    )

    assert response.status_code == HTTPStatus.NOT_IMPLEMENTED
    assert error_code(response) == NOT_IMPLEMENTED_CODE


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


def test_rewrite_stub_returns_501(tmp_path: Path) -> None:
    """POST /api/rewrite with a valid transcript hits the not-implemented stub."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post("/api/rewrite", json={"transcript": "I missed the bus."})

    assert response.status_code == HTTPStatus.NOT_IMPLEMENTED
    assert error_code(response) == NOT_IMPLEMENTED_CODE


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
