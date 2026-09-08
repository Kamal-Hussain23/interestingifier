"""Tests for the Gemini service helpers in services.py."""

import io
import logging
import wave
from typing import Any

import pytest
from google.genai import types

import config
import services
from models import Absurdity

TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1
TTS_SAMPLE_WIDTH = 2


TTS_MIME = "audio/l16; rate=24000; channels=1"


class _Transcription:
    """Minimum stand-in for the SDK's AudioTranscription payload."""

    def __init__(self, text: str | None) -> None:
        self.text = text


class _InlineData:
    def __init__(self, data: bytes, mime_type: str) -> None:
        self.data = data
        self.mime_type = mime_type


class _Part:
    def __init__(
        self,
        text: str | None = None,
        audio_transcription: _Transcription | None = None,
        inline_data: _InlineData | None = None,
    ) -> None:
        self.text = text
        self.audio_transcription = audio_transcription
        self.inline_data = inline_data


class _Content:
    def __init__(self, parts: list[_Part]) -> None:
        self.parts = parts


class _Candidate:
    def __init__(self, content: _Content) -> None:
        self.content = content


class _FakeResponse:
    def __init__(
        self,
        text: str | None = None,
        audio_transcription: str | None = None,
        audio_bytes: bytes | None = None,
    ) -> None:
        self.text = text
        self.parts: list[_Part] = []
        self.candidates: list[_Candidate] = []
        if audio_bytes is not None:
            part = _Part(inline_data=_InlineData(audio_bytes, TTS_MIME))
        elif audio_transcription is not None:
            part = _Part(audio_transcription=_Transcription(audio_transcription))
        else:
            part = _Part(text=text)
        self.parts = [part]
        self.candidates = [_Candidate(_Content([part]))]


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
            return _FakeResponse(audio_transcription=self._transcript)
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


def test_transcribe_audio_sends_transcription_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """transcribe_audio drives the transcribe model with AudioTranscriptionConfig."""
    fake_client = _monkeypatch_gemini(monkeypatch, "I missed the bus.", "", b"")
    audio = b"audio-bytes"

    services.transcribe_audio(audio, "audio/webm")

    kwargs = fake_client.models.last_kwargs
    assert kwargs["model"] == services.TRANSCRIPTION_MODEL == "gemini-3.5-transcribe"
    assert kwargs["contents"] == [types.Part.from_bytes(data=audio, mime_type="audio/webm")]
    config = kwargs["config"]
    assert config.audio_transcription_config == types.AudioTranscriptionConfig()


def test_transcribe_audio_raises_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """transcribe_audio raises when Gemini returns no transcript text."""
    _monkeypatch_gemini(monkeypatch, "", "", b"")

    with pytest.raises(RuntimeError, match="empty transcription"):
        services.transcribe_audio(b"audio-bytes", "audio/webm")


def test_rewrite_story_returns_story(monkeypatch: pytest.MonkeyPatch) -> None:
    """rewrite_story calls Gemini and returns the absurd story text."""
    _monkeypatch_gemini(monkeypatch, "", "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY.", b"")

    result = services.rewrite_story("I missed the bus.")

    assert result == "THE BUS FEARED HIM. IT TREMBLED BEFORE HIS GLORY."


def _rewrite_prompt_used(monkeypatch: pytest.MonkeyPatch, level: Absurdity | None) -> str:
    """Rewrite a transcript and return the first contents element sent to Gemini."""
    fake_client = _monkeypatch_gemini(monkeypatch, "", "A STORY.", b"")
    if level is None:
        services.rewrite_story("I missed the bus.")
    else:
        services.rewrite_story("I missed the bus.", absurdity=level)
    return str(fake_client.models.last_kwargs["contents"][0])


def test_rewrite_story_defaults_to_unhinged_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a level, rewrite_story sends the Unhinged prompt (backward compatible)."""
    prompt = _rewrite_prompt_used(monkeypatch, None)

    assert prompt == services.REWRITE_PROMPTS[Absurdity.UNHINGED]


def test_rewrite_story_sends_slightly_weird_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Slightly Weird level uses its own, gentler prompt."""
    prompt = _rewrite_prompt_used(monkeypatch, Absurdity.SLIGHTLY_WEIRD)

    assert prompt == services.REWRITE_PROMPTS[Absurdity.SLIGHTLY_WEIRD]


def test_rewrite_story_sends_total_fever_dream_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Total Fever Dream level uses its own, wildest prompt."""
    prompt = _rewrite_prompt_used(monkeypatch, Absurdity.TOTAL_FEVER_DREAM)

    assert prompt == services.REWRITE_PROMPTS[Absurdity.TOTAL_FEVER_DREAM]


def test_rewrite_prompts_for_each_level_are_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    """The three prompts are genuinely different texts, keyed by Absurdity."""
    prompts = {
        _rewrite_prompt_used(monkeypatch, Absurdity.SLIGHTLY_WEIRD),
        _rewrite_prompt_used(monkeypatch, Absurdity.UNHINGED),
        _rewrite_prompt_used(monkeypatch, Absurdity.TOTAL_FEVER_DREAM),
    }

    assert prompts == {
        services.REWRITE_PROMPTS[Absurdity.SLIGHTLY_WEIRD],
        services.REWRITE_PROMPTS[Absurdity.UNHINGED],
        services.REWRITE_PROMPTS[Absurdity.TOTAL_FEVER_DREAM],
    }
    assert len(prompts) == len(services.REWRITE_PROMPTS)


def test_drama_twists_is_a_non_empty_list() -> None:
    """DRAMA_TWISTS is a non-empty list of non-empty strings."""
    assert isinstance(services.DRAMA_TWISTS, list)
    assert len(services.DRAMA_TWISTS) > 0
    assert all(isinstance(twist, str) and twist.strip() for twist in services.DRAMA_TWISTS)


def test_pick_drama_twist_uses_injected_pick() -> None:
    """pick_drama_twist returns exactly what the injected picker chooses."""
    assert services.pick_drama_twist(lambda seq: seq[2]) == services.DRAMA_TWISTS[2]


def _rewrite_contents_used(monkeypatch: pytest.MonkeyPatch, twist: str | None = None) -> list[str]:
    """Rewrite a transcript and return the full contents list sent to Gemini."""
    fake_client = _monkeypatch_gemini(monkeypatch, "", "A STORY.", b"")
    if twist is None:
        services.rewrite_story("I missed the bus.")
    else:
        services.rewrite_story("I missed the bus.", twist=twist)
    return list(fake_client.models.last_kwargs["contents"])


def test_rewrite_story_threads_twist_into_contents(monkeypatch: pytest.MonkeyPatch) -> None:
    """A twist is injected between the level prompt and the transcript."""
    contents = _rewrite_contents_used(monkeypatch, twist="Locked-room courtroom drama.")

    assert contents == [
        services.REWRITE_PROMPTS[Absurdity.UNHINGED],
        "Locked-room courtroom drama.",
        "I missed the bus.",
    ]


def test_rewrite_story_without_twist_contents_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a twist, the contents stay exactly [prompt, transcript]."""
    contents = _rewrite_contents_used(monkeypatch)

    assert contents == [
        services.REWRITE_PROMPTS[Absurdity.UNHINGED],
        "I missed the bus.",
    ]


def test_generate_headline_returns_uppercase(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate_headline returns the model text uppercased."""
    _monkeypatch_gemini(monkeypatch, "", "Screaming headline!", b"")

    result = services.generate_headline("A boring story.")

    assert result == "SCREAMING HEADLINE!"


def test_generate_headline_sends_model_and_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate_headline calls Gemini with the headline model and prompt."""
    fake_client = _monkeypatch_gemini(monkeypatch, "", "BIG NEWS", b"")

    services.generate_headline("A boring story.")

    kwargs = fake_client.models.last_kwargs
    assert kwargs["model"] == services.HEADLINE_MODEL
    assert kwargs["contents"] == [services.HEADLINE_PROMPT, "A boring story."]


def test_generate_headline_raises_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate_headline raises when Gemini returns no text."""

    class _EmptyResponse:
        text: str | None = None

    class _EmptyModels:
        last_kwargs: dict[str, object] = {}

        def generate_content(self, **kw: object) -> _EmptyResponse:
            self.last_kwargs = kw
            return _EmptyResponse()

    class _EmptyClient:
        models = _EmptyModels()

    monkeypatch.setattr(config, "get_gemini_api_key", lambda: "fake")
    monkeypatch.setattr(services, "build_client", lambda api_key: _EmptyClient())

    with pytest.raises(RuntimeError, match="empty headline"):
        services.generate_headline("A story.")


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
