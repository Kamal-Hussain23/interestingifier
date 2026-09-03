"""Interestingifier Flask application.

Serves the frontend and the three Gemini pipeline endpoints. The endpoints have
real, structured request/response contracts; the Gemini calls themselves are
TODO stubs in services.py that Cycle 2 fills in (until then they return 501).
"""

import os
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path

from flask import Flask, Response, jsonify, request

import services
from db import DB_PATH, init_db
from logging_config import logged, setup_logging
from models import ErrorResponse, StoryResponse, TranscriptResponse

HOST = "0.0.0.0"
PORT = 3000

# Placeholder content type for narrated audio. Confirm (and possibly change)
# this when the Gemini Text-to-Speech call lands in Cycle 2, milestone 3.
NARRATION_CONTENT_TYPE = "audio/webm"


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
    return jsonify(asdict(TranscriptResponse(transcript=transcript)))


@logged
def rewrite() -> Response:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response(
            "missing_transcript",
            "Send a JSON body with a 'transcript' field.",
            HTTPStatus.BAD_REQUEST,
        )
    transcript = str(data.get("transcript", "")).strip()
    if not transcript:
        return error_response(
            "missing_transcript",
            "The 'transcript' field must be a non-empty string.",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        story = services.rewrite_story(transcript)
    except NotImplementedError as exc:
        return error_response("not_implemented", str(exc), HTTPStatus.NOT_IMPLEMENTED)
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
    return Response(audio, mimetype=NARRATION_CONTENT_TYPE)


def create_app(db_path: Path = DB_PATH) -> Flask:
    """Build the Flask app and make sure the database schema exists."""
    init_db(db_path)
    app = Flask(__name__, static_folder="frontend/static")

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
