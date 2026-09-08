"""Interestingifier Flask application.

Serves the frontend and the three Gemini pipeline endpoints. Every endpoint has
a real, structured request/response contract and calls a real Gemini service
transcribe → rewrite → narrate, persisting the transcript and story to SQLite.
"""

import os
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path

from flask import Flask, Response, current_app, jsonify, request

import db
import services
from db import DB_PATH, init_db
from logging_config import logged, setup_logging
from models import Absurdity, ErrorResponse, StoryResponse, TranscriptResponse

HOST = "0.0.0.0"
PORT = 3000

# Content type for narrated audio. `narrate_story` wraps Gemini's raw L16 PCM
# in a WAV container, so this stays correct.
NARRATION_CONTENT_TYPE = "audio/wav"


def public_url(port: int = PORT) -> str:
    """Return the Codio public URL for this box, or a localhost fallback."""
    hostname = os.environ.get("CODIO_HOSTNAME")
    if hostname:
        return f"https://{hostname}-{port}.codio.io/"
    return f"http://localhost:{port}/"


def error_response(code: str, message: str, status: HTTPStatus) -> Response:
    """Return the shared structured error body with the given status."""
    response = jsonify({"error": asdict(ErrorResponse(code=code, message=message))})
    response.status_code = status
    return response


def parse_absurdity(data: dict[str, object]) -> Absurdity:
    """Resolve the optional 'absurdity' field, defaulting to Unhinged.

    Absent from the payload → the Unhinged default (today's behaviour).
    Present but unknown → Absurdity.from_token raises ValueError the route
    turns into a structured 400.
    """
    if "absurdity" not in data:
        return Absurdity.UNHINGED
    return Absurdity.from_token(str(data.get("absurdity", "")))


def parse_drama_flag(data: dict[str, object]) -> bool:
    """Resolve the optional 'drama' field for a More Drama! re-roll.

    Lenient, like parse_absurdity: only an explicitly truthy value (True or the
    string "true") enables the twist; absent, False, or junk mean a plain
    rewrite.
    """
    return str(data.get("drama", "")).lower() == "true"


@logged
def transcribe() -> Response:
    audio_file = request.files.get("audio")
    if audio_file is None or not audio_file.filename:
        return error_response(
            "missing_audio",
            "Upload an audio file in the 'audio' field.",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        transcript = services.transcribe_audio(audio_file.read(), audio_file.mimetype)
    except NotImplementedError as exc:
        return error_response("not_implemented", str(exc), HTTPStatus.NOT_IMPLEMENTED)
    except Exception as exc:
        return error_response("transcription_failed", str(exc), HTTPStatus.BAD_GATEWAY)
    db.save_transcript(transcript, db_path=current_app.config["DB_PATH"])
    return jsonify(asdict(TranscriptResponse(transcript=transcript)))


@logged
def rewrite() -> Response:
    data = request.get_json(silent=True)
    transcript = str(data.get("transcript", "")).strip() if isinstance(data, dict) else ""
    if not transcript:
        message = (
            "Send a JSON body with a 'transcript' field."
            if not isinstance(data, dict)
            else "The 'transcript' field must be a non-empty string."
        )
        return error_response("missing_transcript", message, HTTPStatus.BAD_REQUEST)
    assert isinstance(data, dict)
    try:
        absurdity = parse_absurdity(data)
    except ValueError as exc:
        return error_response("invalid_absurdity", str(exc), HTTPStatus.BAD_REQUEST)
    twist = services.pick_drama_twist() if parse_drama_flag(data) else None
    try:
        story = services.rewrite_story(transcript, absurdity=absurdity, twist=twist)
    except NotImplementedError as exc:
        return error_response("not_implemented", str(exc), HTTPStatus.NOT_IMPLEMENTED)
    except Exception as exc:
        return error_response("rewrite_failed", str(exc), HTTPStatus.BAD_GATEWAY)
    transcript_id = db.fetch_latest_transcript_id(db_path=current_app.config["DB_PATH"])
    if transcript_id is None:
        return error_response(
            "no_transcript",
            "No transcript found to link story to.",
            HTTPStatus.BAD_REQUEST,
        )
    db.save_story(
        transcript_id,
        story,
        absurdity=absurdity.value,
        db_path=current_app.config["DB_PATH"],
    )
    return jsonify(asdict(StoryResponse(story=story)))


@logged
def narrate() -> Response:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response(
            "missing_story",
            "Send a JSON body with a 'story' field.",
            HTTPStatus.BAD_REQUEST,
        )
    story = str(data.get("story", "")).strip()
    if not story:
        return error_response(
            "missing_story",
            "The 'story' field must be a non-empty string.",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        audio = services.narrate_story(story)
    except NotImplementedError as exc:
        return error_response("not_implemented", str(exc), HTTPStatus.NOT_IMPLEMENTED)
    except Exception as exc:
        return error_response("narration_failed", str(exc), HTTPStatus.BAD_GATEWAY)
    return Response(audio, mimetype=NARRATION_CONTENT_TYPE)


def create_app(db_path: Path = DB_PATH) -> Flask:
    """Build the Flask app and make sure the database schema exists."""
    init_db(db_path)
    app = Flask(__name__, static_folder="frontend/static")
    app.config["DB_PATH"] = Path(db_path)

    @app.route("/")
    @logged
    def index() -> Response:
        return app.send_static_file("index.html")

    @app.route("/api/health")
    @logged
    def health() -> Response:
        return jsonify({"status": "ok"})

    app.add_url_rule("/api/transcribe", "transcribe", transcribe, methods=["POST"])
    app.add_url_rule("/api/rewrite", "rewrite", rewrite, methods=["POST"])
    app.add_url_rule("/api/narrate", "narrate", narrate, methods=["POST"])

    return app


if __name__ == "__main__":
    setup_logging()
    app = create_app()
    print(f"Your site is live at {public_url()}")
    app.run(host=HOST, port=PORT)
