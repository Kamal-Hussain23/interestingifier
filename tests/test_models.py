"""Tests for the JSON contract and DB row models in models.py."""

from dataclasses import asdict

from models import ErrorResponse, Story, StoryResponse, Transcript, TranscriptResponse


def test_transcript_response_serialises() -> None:
    """TranscriptResponse serialises to the /api/transcribe success shape."""
    assert asdict(TranscriptResponse(transcript="I missed the bus.")) == {
        "transcript": "I missed the bus."
    }


def test_story_response_serialises() -> None:
    """StoryResponse serialises to the /api/rewrite success shape."""
    assert asdict(StoryResponse(story="THE BUS FEARED HIM.")) == {"story": "THE BUS FEARED HIM."}


def test_error_response_serialises() -> None:
    """ErrorResponse serialises to the shared error shape."""
    assert asdict(ErrorResponse(code="missing_audio", message="No audio uploaded.")) == {
        "code": "missing_audio",
        "message": "No audio uploaded.",
    }


def test_transcript_row_serialises() -> None:
    """Transcript serialises to the stored transcripts-table shape."""
    assert asdict(
        Transcript(id=1, raw_text="I missed the bus.", created_at="2026-08-14 10:00:00")
    ) == {
        "id": 1,
        "raw_text": "I missed the bus.",
        "created_at": "2026-08-14 10:00:00",
    }


def test_story_row_serialises() -> None:
    """Story serialises to the stored stories-table shape."""
    assert asdict(
        Story(
            id=1,
            transcript_id=2,
            story_text="THE BUS FEARED HIM.",
            created_at="2026-08-14 10:00:00",
        )
    ) == {
        "id": 1,
        "transcript_id": 2,
        "story_text": "THE BUS FEARED HIM.",
        "created_at": "2026-08-14 10:00:00",
    }
