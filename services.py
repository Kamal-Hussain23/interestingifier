"""Gemini service helpers for the three-step pipeline.

Cycle 2 fills in each helper with a real Gemini call. `transcribe_audio`
("Capture the Boring") is done; `rewrite_story` and `narrate_story` are the next
two milestones and still raise NotImplementedError. Business logic stays
logging-free; the @logged decorator handles that.
"""

import base64

from google import genai
from google.genai import types

import config
from logging_config import logged

TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"

TRANSCRIPTION_PROMPT = (
    "Transcribe the user's spoken anecdote exactly as they said it. "
    "Return only the plain transcript text with no commentary."
)

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


@logged
def transcribe_audio(audio: bytes, mime_type: str) -> str:
    """Turn recorded speech into text (Gemini Speech-to-Text)."""
    client = build_client(config.get_gemini_api_key())
    response = client.models.generate_content(
        model=TRANSCRIPTION_MODEL,
        contents=[
            TRANSCRIPTION_PROMPT,
            types.Part.from_bytes(data=audio, mime_type=mime_type),
        ],
    )
    if response.text is None:
        raise RuntimeError("Gemini returned an empty transcription response.")
    return response.text


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
    """Narrate a story aloud as audio (Gemini Text-to-Speech)."""
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
    # Extract audio bytes from response
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        raise RuntimeError("Gemini returned an empty TTS response.")
    part = response.candidates[0].content.parts[0]
    if part.inline_data is None or part.inline_data.data is None:
        raise RuntimeError("Gemini returned an empty TTS response (no inline data).")
    audio_b64 = part.inline_data.data
    return base64.b64decode(audio_b64)
