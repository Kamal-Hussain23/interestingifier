"""Tests for the Gemini API-key helper in config.py."""

import pytest

from config import GEMINI_API_KEY_ENV, get_gemini_api_key


def test_get_gemini_api_key_returns_env_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """The key is returned as-is when GEMINI_API_KEY is set."""
    monkeypatch.setenv(GEMINI_API_KEY_ENV, "secret-key-123")
    assert get_gemini_api_key() == "secret-key-123"


def test_get_gemini_api_key_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing key raises a clear RuntimeError instead of returning None."""
    monkeypatch.delenv(GEMINI_API_KEY_ENV, raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        get_gemini_api_key()


def test_get_gemini_api_key_raises_when_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    """A whitespace-only key counts as missing."""
    monkeypatch.setenv(GEMINI_API_KEY_ENV, "   ")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        get_gemini_api_key()
