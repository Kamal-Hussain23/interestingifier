"""Gemini service helpers for the three-step pipeline.

Each helper is a clean, typed seam for one Gemini capability. The calls are
not implemented yet — Cycle 2 fills them in. Until then they raise
NotImplementedError with a message that says exactly what the student needs to
add. Business logic stays logging-free; the @logged decorator handles that.
"""

from logging_config import logged


@logged
def transcribe_audio(audio: bytes, mime_type: str) -> str:
    """Turn recorded speech into text (Gemini Speech-to-Text).

    TODO(Cycle 2, milestone 1 "Capture the Boring"): send `audio` to Gemini,
    using `mime_type` for the request, and return the transcript text.
    """
    raise NotImplementedError(
        "Transcription is not implemented yet — fill in the Gemini "
        "Speech-to-Text call here (Cycle 2, milestone 1)."
    )


@logged
def rewrite_story(transcript: str) -> str:
    """Rewrite a boring transcript as an over-the-top story (Gemini generative text).

    TODO(Cycle 2, milestone 2 "The Vibrant Transformation"): send `transcript`
    to Gemini with an over-the-top prompt and return the absurd story.
    """
    raise NotImplementedError(
        "Rewriting is not implemented yet — fill in the Gemini generative-text "
        "call here (Cycle 2, milestone 2)."
    )


@logged
def narrate_story(story: str) -> bytes:
    """Narrate a story aloud as audio (Gemini Text-to-Speech).

    TODO(Cycle 2, milestone 3 "Vocalizing the Absurd"): send `story` to Gemini
    Text-to-Speech and return the audio bytes. The TTS config must explicitly
    request a funny, energetic Aussie accent (MISSION.md's signature voice) —
    not a plain, accent-free read-out.
    """
    raise NotImplementedError(
        "Narration is not implemented yet — fill in the Gemini Text-to-Speech "
        "call here (Cycle 2, milestone 3), explicitly requesting a funny "
        "energetic Aussie accent."
    )
