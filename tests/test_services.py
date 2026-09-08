"""Tests for the Gemini service helpers in services.py."""

import io
import logging
import wave
from typing import Any

import pytest

import config
import services

TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1
TTS_SAMPLE_WIDTH = 2


class _FakeResponse:
    def __init__(self, text: str | None = None, audio_bytes: bytes | None = None) -> None:
        self.text = text
        self._audio_bytes = audio_bytes

    @property
    def candidates(self) -> list[Any]:
        if self._audio_bytes:
            audio = self._audio_bytes

            class _InlineData:
                data: bytes = audio
                mime_type: str = "audio/l16; rate=24000; channels=1"

            class _Part:
                inline_data = _InlineData()

            class _Content:
                parts: list[Any] = [_Part()]

            class _Candidate:
                content: Any = _Content()

            return [_Candidate()]
        return []


class _FakeModels:
    def __init__(self, transcript: str, story: str, audio_bytes: bytes) -> None:
        self._transcript = transcript
        self._story = story
        self._audio_bytes = audio_bytes
        self.last_kwargs: dict[str, Any] = {}

    def generate_content(self, **kwargs: Any) -> _FakeResponse:
        self.last_kwargs = kwargs
        # Check generation_config for TTS (handle both dict and object, param name is "config")
        gen_config = kwargs.get("config") or kwargs.get("generation_config")
        if gen_config:
            # Handle both dict and GenerateContentConfig object
            modalities = getattr(gen_config, "response_modalities", None)
            if modalities is None and hasattr(gen_config, "get"):
                modalities = gen_config.get("response_modalities")
            if modalities == ["AUDIO"]:
                return _FakeResponse(audio_bytes=self._audio_bytes)
        # Check model for transcription vs rewrite
        model = kwargs.get("model", "")
        if "transcribe" in str(model).lower():
            return _FakeResponse(text=self._transcript)
        # Default to rewrite
        return _FakeResponse(text=self._story)


class _FakeClient:
    def __init__(self, transcript: str, story: str, audio_bytes: bytes) -> None:
        self.models = _FakeModels(transcript, story, audio_bytes)


def _monkeypatch_gemini(
    monkeypatch: pytest.MonkeyPatch,
    transcript: str,
    story: str,
    audio_bytes: bytes,
) -> _FakeClient:
    """Monkeypatch both config.get_gemini_api_key and services.build_client."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(config, "get_gemini_api_key", lambda: "fake-key")
    fake_client = _FakeClient(transcript, story, audio_bytes)
    monkeypatch.setattr(services, "build_client", lambda api_key: fake_client)
    return fake_client


def test_transcribe_audio_returns_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    """transcribe_audio calls Gemini and returns the transcript text."""
    _monkeypatch_gemini(monkeypatch, "I missed the bus.", "", b"")

    result = services.transcribe_audio(b"audio-bytes", "audio/webm")

    assert result == "I missed the bus."


def test_rewrite_story_returns_story(monkeypatch: pytest.MonkeyPatch) -> None:
    """rewrite_story calls Gemini and returns the absurd story text."""
    _monkeypatch_gemini(monkeypatch, "", "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY.", b"")

    result = services.rewrite_story("I missed the bus.")

    assert result == "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY."


def test_narrate_story_returns_playable_wav(monkeypatch: pytest.MonkeyPatch) -> None:
    """narrate_story wraps the Gemini PCM bytes in a playable WAV container."""
    _monkeypatch_gemini(monkeypatch, "", "", b"fake-audio-bytes")

    result = services.narrate_story("THE BUS FEARED HIM.")

    assert result.startswith(b"RIFF")
    assert b"WAVE" in result
    with wave.open(io.BytesIO(result), "rb") as audio:
        assert audio.getframerate() == TTS_SAMPLE_RATE
        assert audio.getnchannels() == TTS_CHANNELS
        assert audio.getsampwidth() == TTS_SAMPLE_WIDTH
        assert audio.readframes(audio.getnframes()) == b"fake-audio-bytes"


def test_narrate_story_sends_tts_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """narrate_story uses the TTS model and explicitly requests an Aussie-accented AUDIO voice."""
    fake_client = _monkeypatch_gemini(monkeypatch, "", "", b"x")

    services.narrate_story("THE BUS FEARED HIM.")

    kwargs = fake_client.models.last_kwargs
    assert kwargs["model"] == services.TTS_MODEL == "gemini-3.1-flash-tts-preview"
    assert kwargs["contents"] == [services.TTS_PROMPT, "THE BUS FEARED HIM."]
    assert "Aussie" in services.TTS_PROMPT

    gen_config = kwargs["config"]
    assert gen_config.response_modalities == ["AUDIO"]
    voice = gen_config.speech_config.voice_config.prebuilt_voice_config
    assert voice.voice_name == "Aoede"


def test_audio_format_from_mime_parses_rate_and_channels() -> None:
    """_audio_format_from_mime pulls rate and channels out of the TTS mime type."""
    assert services._audio_format_from_mime("audio/l16; rate=24000; channels=1") == (24000, 1)


def test_audio_format_from_mime_has_sane_defaults() -> None:
    """_audio_format_from_mime falls back to Gemini TTS defaults when unparseable."""
    assert services._audio_format_from_mime("") == (24000, 1)
    assert services._audio_format_from_mime("audio/l16") == (24000, 1)


def test_services_are_logged(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The @logged decorator reports service calls without mixing in business logic."""
    _monkeypatch_gemini(monkeypatch, "", "", b"x")
    caplog.set_level(logging.INFO, logger="services")
    services.narrate_story("test story")
    assert any("narrate_story" in record.message for record in caplog.records)
