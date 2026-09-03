"""Typed JSON contracts for the API.

Small frozen dataclasses so request/response shapes are explicit contracts
rather than ad-hoc dicts — see TECH.md ("contracts and strict models over
custom logic").
"""

from dataclasses import dataclass


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
