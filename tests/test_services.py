"""Tests for the Gemini service helpers in services.py."""

import logging

import pytest

import services


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, transcript: str, story: str) -> None:
        self._transcript = transcript
        self._story = story

    def generate_content(self, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(self._story if "story" in str(kwargs).lower() else self._transcript)


class _FakeClient:
    def __init__(self, transcript: str, story: str) -> None:
        self.models = _FakeModels(transcript, story)


def test_transcribe_audio_returns_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    """transcribe_audio calls Gemini and returns the transcript text."""
    fake_client = _FakeClient("I missed the bus.", "")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(services, "build_client", lambda api_key: fake_client)

    result = services.transcribe_audio(b"audio-bytes", "audio/webm")

    assert result == "I missed the bus."


def test_rewrite_story_returns_story(monkeypatch: pytest.MonkeyPatch) -> None:
    """rewrite_story calls Gemini and returns the absurd story text."""
    fake_client = _FakeClient("", "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY.")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(services, "build_client", lambda api_key: fake_client)

    result = services.rewrite_story("I missed the bus.")

    assert result == "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY."


def test_narrate_story_is_not_implemented() -> None:
    """The narrate stub raises NotImplementedError until Cycle 2 fills it in."""
    with pytest.raises(NotImplementedError, match="Cycle 2"):
        services.narrate_story("THE BUS FEARED HIM.")


def test_services_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    """The @logged decorator reports service calls without mixing in business logic."""
    caplog.set_level(logging.INFO, logger="services")
    with pytest.raises(NotImplementedError):
        services.narrate_story("test story")
    assert any("narrate_story" in record.message for record in caplog.records)
