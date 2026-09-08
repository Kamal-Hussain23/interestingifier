"""Tests for the Gemini service helpers in services.py."""

import base64
import logging
from typing import Any

import pytest

import config
import services


class _FakeResponse:
    def __init__(self, text: str | None = None, audio_b64: str | None = None) -> None:
        self.text = text
        self._audio_b64 = audio_b64

    @property
    def candidates(self) -> list[Any]:
        if self._audio_b64:

            class _Part:
                def __init__(self, data: str) -> None:
                    self.inline_data = type("obj", (object,), {"data": data})()

            class _Content:
                def __init__(self, parts: list[Any]) -> None:
                    self.parts = parts

            class _Candidate:
                def __init__(self, content: Any) -> None:
                    self.content = content

            return [_Candidate(_Content([_Part(self._audio_b64)]))]
        return []


class _FakeModels:
    def __init__(self, transcript: str, story: str, audio_b64: str) -> None:
        self._transcript = transcript
        self._story = story
        self._audio_b64 = audio_b64

    def generate_content(self, **kwargs: Any) -> _FakeResponse:
        # Check generation_config for TTS (handle both dict and object, param name is "config")
        gen_config = kwargs.get("config") or kwargs.get("generation_config")
        if gen_config:
            # Handle both dict and GenerateContentConfig object
            modalities = getattr(gen_config, "response_modalities", None)
            if modalities is None and hasattr(gen_config, "get"):
                modalities = gen_config.get("response_modalities")
            if modalities == ["AUDIO"]:
                return _FakeResponse(audio_b64=self._audio_b64)
        # Check model for transcription vs rewrite
        model = kwargs.get("model", "")
        if "transcribe" in str(model).lower():
            return _FakeResponse(text=self._transcript)
        # Default to rewrite
        return _FakeResponse(text=self._story)


class _FakeClient:
    def __init__(self, transcript: str, story: str, audio_b64: str) -> None:
        self.models = _FakeModels(transcript, story, audio_b64)


def _monkeypatch_gemini(
    monkeypatch: pytest.MonkeyPatch,
    transcript: str,
    story: str,
    audio_b64: str,
) -> None:
    """Monkeypatch both config.get_gemini_api_key and services.build_client."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(config, "get_gemini_api_key", lambda: "fake-key")
    fake_client = _FakeClient(transcript, story, audio_b64)
    monkeypatch.setattr(services, "build_client", lambda api_key: fake_client)


def test_transcribe_audio_returns_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    """transcribe_audio calls Gemini and returns the transcript text."""
    _monkeypatch_gemini(monkeypatch, "I missed the bus.", "", "")

    result = services.transcribe_audio(b"audio-bytes", "audio/webm")

    assert result == "I missed the bus."


def test_rewrite_story_returns_story(monkeypatch: pytest.MonkeyPatch) -> None:
    """rewrite_story calls Gemini and returns the absurd story text."""
    _monkeypatch_gemini(monkeypatch, "", "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY.", "")

    result = services.rewrite_story("I missed the bus.")

    assert result == "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY."


def test_narrate_story_returns_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    """narrate_story calls Gemini TTS and returns audio bytes."""
    audio_b64 = base64.b64encode(b"fake-audio-bytes").decode()
    _monkeypatch_gemini(monkeypatch, "", "", audio_b64)

    result = services.narrate_story("THE BUS FEARED HIM.")

    assert result == b"fake-audio-bytes"


def test_services_are_logged(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The @logged decorator reports service calls without mixing in business logic."""
    _monkeypatch_gemini(monkeypatch, "", "", base64.b64encode(b"x").decode())
    caplog.set_level(logging.INFO, logger="services")
    services.narrate_story("test story")
    assert any("narrate_story" in record.message for record in caplog.records)
