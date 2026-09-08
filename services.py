"""Gemini service helpers for the three-step pipeline.

Cycle 2 filled in each helper with a real Gemini call: `transcribe_audio`
("Capture the Boring"), `rewrite_story` ("The Vibrant Transformation"), and
`narrate_story` ("Vocalizing the Absurd"). Business logic stays logging-free;
the @logged decorator handles that.
"""

import io
import wave

from google import genai
from google.genai import types

import config
from logging_config import logged

TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"

REWRITE_MODEL = "gemini-3.1-flash-lite"

REWRITE_PROMPT = (
    "Rewrite the user's boring anecdote as an over-the-top, hilarious, "
    "theatrical story. Amplify every detail to absurd proportions. "
    "Use dramatic flair, vivid imagery, and comedic exaggeration. "
    "Return only the rewritten story with no commentary."
)

TTS_MODEL = "gemini-3.1-flash-tts-preview"

TTS_PROMPT = (
    "Narrate the following story in a funny, energetic Aussie accent. "
    "Use dramatic flair and comedic timing. Return only the audio narration."
)


def build_client(api_key: str) -> genai.Client:
    """Build the Gemini client from the API key.

    Kept as its own tiny function so tests can swap in a fake without the real
    SDK or a network call.
    """
    return genai.Client(api_key=api_key)


def _audio_format_from_mime(mime_type: str) -> tuple[int, int]:
    """Return (sample_rate, channels) parsed from a Gemini TTS mime type.

    Gemini returns something like "audio/l16; rate=24000; channels=1". The
    sample rate and channel count are needed to wrap the raw PCM in a WAV
    container. Falls back to the model's usual values if the mime is missing
    or unparseable.
    """
    rate = 24000
    channels = 1
    for piece in mime_type.split(";"):
        key, _, value = piece.strip().partition("=")
        if key == "rate":
            rate = int(value)
        elif key == "channels":
            channels = int(value)
    return rate, channels


def _wrap_l16_in_wav(pcm: bytes, rate: int = 24000, channels: int = 1) -> bytes:
    """Wrap raw 16-bit linear PCM into a playable WAV (RIFF) container.

    Gemini TTS returns bare L16 PCM, which browsers cannot play directly, so
    we add the standard WAV header before sending it to the frontend.
    """
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


@logged
def transcribe_audio(audio: bytes, mime_type: str) -> str:
    """Turn recorded speech into text (Gemini Speech-to-Text)."""
    client = build_client(config.get_gemini_api_key())
    response = client.models.generate_content(
        model=TRANSCRIPTION_MODEL,
        contents=[types.Part.from_bytes(data=audio, mime_type=mime_type)],
        config=types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(),
        ),
    )
    # The transcribe model reports the transcript on each part's
    # `audio_transcription` field (not response.text).
    for part in response.parts or []:
        transcription = getattr(part, "audio_transcription", None)
        if transcription is not None:
            text = getattr(transcription, "text", None)
            if text:
                return str(text)
        if part.text:
            return part.text
    raise RuntimeError("Gemini returned an empty transcription response.")


@logged
def rewrite_story(transcript: str) -> str:
    """Rewrite a boring transcript as an over-the-top story (Gemini generative text)."""
    client = build_client(config.get_gemini_api_key())
    response = client.models.generate_content(
        model=REWRITE_MODEL,
        contents=[REWRITE_PROMPT, transcript],
    )
    if response.text is None:
        raise RuntimeError("Gemini returned an empty story response.")
    return response.text


@logged
def narrate_story(story: str) -> bytes:
    """Narrate a story aloud as audio, returned as a playable WAV (Gemini Text-to-Speech)."""
    client = build_client(config.get_gemini_api_key())
    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=[TTS_PROMPT, story],
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                )
            ),
        ),
    )
    # Extract the raw PCM bytes from the response and wrap them in a WAV header
    # so the browser can play them. The SDK already decodes the payload to bytes.
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        raise RuntimeError("Gemini returned an empty TTS response.")
    part = response.candidates[0].content.parts[0]
    if part.inline_data is None or part.inline_data.data is None:
        raise RuntimeError("Gemini returned an empty TTS response (no inline data).")
    mime_type = part.inline_data.mime_type or ""
    rate, channels = _audio_format_from_mime(mime_type)
    return _wrap_l16_in_wav(part.inline_data.data, rate, channels)
