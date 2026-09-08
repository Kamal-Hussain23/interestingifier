"""Smoke and contract tests for the Flask application in app.py."""

import wave
from http import HTTPStatus
from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.test import TestResponse

from app import create_app, parse_drama_flag
from db import get_connection, save_transcript
from models import Absurdity

NOT_IMPLEMENTED_CODE = "not_implemented"


def error_code(client_response: TestResponse) -> str:
    """Pull the error code out of the shared error body."""
    return str(client_response.get_json()["error"]["code"])


def mini_wav() -> bytes:
    """Build a tiny but valid WAV file to stand in for narrated audio."""
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x00\x00")
    return buffer.getvalue()


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
        lambda transcript, absurdity=None, twist=None: "THE BUS FEARED HIM.",
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
        lambda transcript, absurdity=None, twist=None: "THE TOAST WAS INNOCENT.",
    )

    client.post("/api/rewrite", json={"transcript": "I burnt the toast."})

    connection = get_connection(db_file)
    rows = connection.execute("SELECT story_text FROM stories").fetchall()
    connection.close()

    assert len(rows) == 1
    assert rows[0]["story_text"] == "THE TOAST WAS INNOCENT."


def test_rewrite_accepts_absurdity_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/rewrite routes the absurdity level to the service and persists it."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I missed the bus.", db_path=db_file)
    captured: dict[str, object] = {}

    def fake_rewrite(
        transcript: str, absurdity: Absurdity | None = None, twist: str | None = None
    ) -> str:
        captured["transcript"] = transcript
        captured["absurdity"] = absurdity
        return "THE BUS FEARED HIM."

    monkeypatch.setattr("app.services.rewrite_story", fake_rewrite)

    response = client.post(
        "/api/rewrite",
        json={"transcript": "I missed the bus.", "absurdity": "total_fever_dream"},
    )

    assert response.status_code == HTTPStatus.OK
    assert captured["transcript"] == "I missed the bus."
    assert captured["absurdity"] is Absurdity.TOTAL_FEVER_DREAM
    connection = get_connection(db_file)
    rows = connection.execute("SELECT absurdity FROM stories").fetchall()
    connection.close()
    assert [row["absurdity"] for row in rows] == ["total_fever_dream"]


def test_rewrite_defaults_to_unhinged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/rewrite without absurdity uses the Unhinged default."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I burnt the toast.", db_path=db_file)
    captured: dict[str, object] = {}

    def fake_rewrite(
        transcript: str, absurdity: Absurdity | None = None, twist: str | None = None
    ) -> str:
        captured["absurdity"] = absurdity
        return "THE TOAST WAS INNOCENT."

    monkeypatch.setattr("app.services.rewrite_story", fake_rewrite)

    client.post("/api/rewrite", json={"transcript": "I burnt the toast."})

    assert captured["absurdity"] is Absurdity.UNHINGED


def test_rewrite_rejects_unknown_absurdity(tmp_path: Path) -> None:
    """POST /api/rewrite with an unknown absurdity token is a structured 400."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()

    response = client.post(
        "/api/rewrite",
        json={"transcript": "I missed the bus.", "absurdity": "chaotic"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "invalid_absurdity"
    assert "slightly_weird" in response.get_json()["error"]["message"]


def test_parse_drama_flag_is_lenient() -> None:
    """parse_drama_flag is True only for explicit truthy drama values."""
    assert parse_drama_flag({}) is False
    assert parse_drama_flag({"drama": True}) is True
    assert parse_drama_flag({"drama": "true"}) is True
    assert parse_drama_flag({"drama": "TRUE"}) is True
    assert parse_drama_flag({"drama": False}) is False
    assert parse_drama_flag({"drama": "nonsense"}) is False


def test_rewrite_with_drama_flag_threads_a_twist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /api/rewrite with drama true picks a twist and sends it to the service."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I missed the bus.", db_path=db_file)
    captured: dict[str, object] = {}

    def fake_rewrite(
        transcript: str, absurdity: Absurdity | None = None, twist: str | None = None
    ) -> str:
        captured["twist"] = twist
        return "THE BUS FEARED HIM."

    monkeypatch.setattr("app.services.pick_drama_twist", lambda: "A heist twist.")
    monkeypatch.setattr("app.services.rewrite_story", fake_rewrite)

    response = client.post(
        "/api/rewrite",
        json={"transcript": "I missed the bus.", "drama": True},
    )

    assert response.status_code == HTTPStatus.OK
    assert captured["twist"] == "A heist twist."
    connection = get_connection(db_file)
    rows = connection.execute("SELECT story_text FROM stories").fetchall()
    connection.close()
    assert len(rows) == 1


def test_rewrite_without_drama_flag_uses_no_twist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without the drama flag, rewrite_story receives twist=None."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I burnt the toast.", db_path=db_file)
    captured: dict[str, object] = {}

    def fake_rewrite(
        transcript: str, absurdity: Absurdity | None = None, twist: str | None = None
    ) -> str:
        captured["twist"] = twist
        return "THE TOAST WAS INNOCENT."

    monkeypatch.setattr("app.services.rewrite_story", fake_rewrite)

    client.post("/api/rewrite", json={"transcript": "I burnt the toast."})

    assert captured["twist"] is None


def test_rewrite_drama_rolls_save_new_story_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each More Drama! re-roll saves a brand-new story row on the same transcript."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    save_transcript("I missed the bus.", db_path=db_file)
    turns = iter(["STORY ONE.", "STORY TWO."])

    def fake_rewrite(
        transcript: str, absurdity: Absurdity | None = None, twist: str | None = None
    ) -> str:
        return next(turns)

    monkeypatch.setattr("app.services.pick_drama_twist", lambda: "A twist.")
    monkeypatch.setattr("app.services.rewrite_story", fake_rewrite)

    client.post("/api/rewrite", json={"transcript": "I missed the bus.", "drama": True})
    client.post("/api/rewrite", json={"transcript": "I missed the bus.", "drama": True})

    connection = get_connection(db_file)
    rows = connection.execute(
        "SELECT id, story_text, transcript_id FROM stories ORDER BY id"
    ).fetchall()
    connection.close()
    assert [row["story_text"] for row in rows] == ["STORY ONE.", "STORY TWO."]
    assert len({row["transcript_id"] for row in rows}) == 1


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


def test_narrate_success_returns_audio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/narrate with a valid story returns a playable WAV."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()
    wav_bytes = mini_wav()
    monkeypatch.setattr(
        "app.services.narrate_story",
        lambda story: wav_bytes,
    )

    response = client.post("/api/narrate", json={"story": "THE BUS FEARED HIM."})

    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "audio/wav"
    assert response.data.startswith(b"RIFF")
    assert response.data == wav_bytes


def test_narrate_failure_returns_502(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Gemini failure during narration is a structured 502, not a crash."""
    app = create_app(db_path=tmp_path / "test.db")
    client = app.test_client()
    monkeypatch.setattr(
        "app.services.narrate_story",
        lambda story: (_ for _ in ()).throw(RuntimeError("Gemini exploded.")),
    )

    response = client.post("/api/narrate", json={"story": "THE BUS FEARED HIM."})

    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert error_code(response) == "narration_failed"


def test_rewrite_no_transcript_returns_400(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A rewrite with no transcript saved cannot link a story and is a 400."""
    db_file = tmp_path / "test.db"
    app = create_app(db_path=db_file)
    client = app.test_client()
    monkeypatch.setattr(
        "app.services.rewrite_story", lambda transcript, absurdity=None, twist=None: "A STORY."
    )

    response = client.post("/api/rewrite", json={"transcript": "I missed the bus."})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_code(response) == "no_transcript"
