"""Gemini service helpers for the three-step pipeline.

Cycle 2 filled in each helper with a real Gemini call: `transcribe_audio`
("Capture the Boring"), `rewrite_story` ("The Vibrant Transformation"), and
`narrate_story` ("Vocalizing the Absurd"). Business logic stays logging-free;
the @logged decorator handles that.
"""

import io
import random
import wave
from collections.abc import Callable

from google import genai
from google.genai import types

import config
from logging_config import logged
from models import Absurdity

TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"

REWRITE_MODEL = "gemini-3.1-flash-lite"

REWRITE_PROMPTS = {
    Absurdity.SLIGHTLY_WEIRD: (
        "Rewrite the user's boring anecdote as a funny story that adds a touch "
        "of playful exaggeration. Keep it grounded and believable — just a "
        "little bit weird. Return only the rewritten story with no commentary."
    ),
    Absurdity.UNHINGED: (
        "Rewrite the user's boring anecdote as an over-the-top, hilarious, "
        "theatrical story. Amplify every detail to absurd proportions. "
        "Use dramatic flair, vivid imagery, and comedic exaggeration. "
        "Return only the rewritten story with no commentary."
    ),
    Absurdity.TOTAL_FEVER_DREAM: (
        "Rewrite the user's boring anecdote as an unhinged fever dream. "
        "Abandon all logic: the world descends into glorious, cosmic chaos. "
        "Every detail twists into surreal, hallucinatory absurdity. "
        "Return only the rewritten story with no commentary."
    ),
}

HEADLINE_MODEL = "gemini-3.1-flash-lite"

HEADLINE_PROMPT = (
    "Invent a sensational, all-caps clickbait headline for the following story. "
    "One short punchy line, no commentary, no quotes, no punctuation gimmicks. "
    "Return only the headline."
)

TTS_MODEL = "gemini-3.1-flash-tts-preview"

# Dramatic-angle instructions for a "More Drama!" re-roll: each click picks a
# random twist so consecutive spins on the same anecdote genuinely differ.
DRAMA_TWISTS: list[str] = [
    "Retell it as a locked-room courtroom drama, in the kitsch style of a soap opera.",
    "Make it feel like a high-octane action-movie trailer.",
    "Tell it as a villain's last confession, full of dramatic irony.",
    "Frame it as a nature documentary's most tense predator-and-prey moment.",
    "Narrate it as a ghost story that turns out not to be so spooky after all.",
    "Reimagine it as a chaotic heist that somehow still succeeds.",
]


def pick_drama_twist(pick: Callable[[list[str]], str] = random.choice) -> str:
    """Return one random dramatic twist from DRAMA_TWISTS.

    The random source is injectable so tests can assert a deterministic choice.
    """
    return pick(DRAMA_TWISTS)


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
def rewrite_story(
    transcript: str,
    absurdity: Absurdity = Absurdity.UNHINGED,
    twist: str | None = None,
) -> str:
    """Rewrite a boring transcript as a story, at the chosen absurdity level.

    When a dramatic twist is given, it is injected between the level prompt and
    the transcript so a "More Drama!" re-roll reads as a fresh angle. Without a
    twist the request is exactly [prompt, transcript] — unchanged behaviour.
    """
    client = build_client(config.get_gemini_api_key())
    contents: list[str] = [REWRITE_PROMPTS[absurdity]]
    if twist:
        contents.append(twist)
    contents.append(transcript)
    response = client.models.generate_content(
        model=REWRITE_MODEL,
        contents=contents,
    )
    if response.text is None:
        raise RuntimeError("Gemini returned an empty story response.")
    return response.text


@logged
def generate_headline(story: str) -> str:
    """Generate a sensational clickbait headline for a story (Gemini generative text)."""
    client = build_client(config.get_gemini_api_key())
    response = client.models.generate_content(
        model=HEADLINE_MODEL,
        contents=[HEADLINE_PROMPT, story],
    )
    if response.text is None:
        raise RuntimeError("Gemini returned an empty headline response.")
    return response.text.upper()


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
