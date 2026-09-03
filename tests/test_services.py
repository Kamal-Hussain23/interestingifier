"""Tests for the Gemini service stubs in services.py."""

import logging

import pytest

from services import narrate_story, rewrite_story, transcribe_audio


def test_transcribe_audio_is_not_implemented() -> None:
    """The transcribe stub raises NotImplementedError until Cycle 2 fills it in."""
    with pytest.raises(NotImplementedError, match="Cycle 2"):
        transcribe_audio(b"fake-audio-bytes", "audio/webm")


def test_rewrite_story_is_not_implemented() -> None:
    """The rewrite stub raises NotImplementedError until Cycle 2 fills it in."""
    with pytest.raises(NotImplementedError, match="Cycle 2"):
        rewrite_story("I missed the bus this morning.")


def test_narrate_story_is_not_implemented() -> None:
    """The narrate stub raises NotImplementedError until Cycle 2 fills it in."""
    with pytest.raises(NotImplementedError, match="Cycle 2"):
        narrate_story("THE BUS FEARED HIM.")


def test_services_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    """The @logged decorator reports service calls without mixing in business logic."""
    caplog.set_level(logging.INFO, logger="services")
    with pytest.raises(NotImplementedError):
        rewrite_story("test story")
    assert any("rewrite_story" in record.message for record in caplog.records)
