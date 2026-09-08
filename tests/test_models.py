"""Tests for the JSON contract and DB row models in models.py."""

from dataclasses import asdict

import pytest

from models import Absurdity, ErrorResponse, Story, StoryResponse, Transcript, TranscriptResponse


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
    """Story serialises to the stored stories-table shape, absurdity included."""
    assert asdict(
        Story(
            id=1,
            transcript_id=2,
            story_text="THE BUS FEARED HIM.",
            created_at="2026-08-14 10:00:00",
            absurdity="total_fever_dream",
        )
    ) == {
        "id": 1,
        "transcript_id": 2,
        "story_text": "THE BUS FEARED HIM.",
        "created_at": "2026-08-14 10:00:00",
        "absurdity": "total_fever_dream",
    }


def test_absurdity_tokens_are_exact() -> None:
    """Absurdity wire tokens match the /api/rewrite contract values."""
    assert Absurdity.SLIGHTLY_WEIRD.value == "slightly_weird"
    assert Absurdity.UNHINGED.value == "unhinged"
    assert Absurdity.TOTAL_FEVER_DREAM.value == "total_fever_dream"


def test_absurdity_from_token_parses_each_level() -> None:
    """from_token turns each wire token into its Absurdity member."""
    assert Absurdity.from_token("slightly_weird") is Absurdity.SLIGHTLY_WEIRD
    assert Absurdity.from_token("unhinged") is Absurdity.UNHINGED
    assert Absurdity.from_token("total_fever_dream") is Absurdity.TOTAL_FEVER_DREAM


def test_absurdity_from_token_rejects_unknown_with_allowed_list() -> None:
    """from_token raises a descriptive error listing the allowed tokens."""
    with pytest.raises(ValueError, match="slightly_weird"):
        Absurdity.from_token("chaotic")
