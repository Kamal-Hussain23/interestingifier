"""Typed JSON contracts for the API.

Small frozen dataclasses so request/response shapes are explicit contracts
rather than ad-hoc dicts — see TECH.md ("contracts and strict models over
custom logic").
"""

import enum
from dataclasses import dataclass


class Absurdity(enum.Enum):
    """Levels of absurdity for the story rewrite, as stable wire tokens."""

    SLIGHTLY_WEIRD = "slightly_weird"
    UNHINGED = "unhinged"
    TOTAL_FEVER_DREAM = "total_fever_dream"

    @classmethod
    def from_token(cls, token: str) -> "Absurdity":
        """Parse a wire token, or raise a descriptive ValueError.

        The single validation point for absorbing an `absurdity` value from the
        API — no ad-hoc string matching or regex elsewhere.
        """
        allowed = ", ".join(level.value for level in cls)
        try:
            return cls(token)
        except ValueError as exc:
            raise ValueError(
                f"Unknown absurdity level {token!r}; expected one of {allowed}."
            ) from exc


@dataclass(frozen=True)
class TranscriptResponse:
    """Success body of POST /api/transcribe."""

    transcript: str


@dataclass(frozen=True)
class StoryResponse:
    """Success body of POST /api/rewrite."""

    story: str


@dataclass(frozen=True)
class ErrorResponse:
    """Shared error body for every failure path."""

    code: str
    message: str


@dataclass(frozen=True)
class Transcript:
    """A row from the transcripts table."""

    id: int
    raw_text: str
    created_at: str


@dataclass(frozen=True)
class Story:
    """A row from the stories table."""

    id: int
    transcript_id: int
    story_text: str
    created_at: str
    absurdity: str = "unhinged"
