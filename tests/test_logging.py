"""Tests for the @logged decorator in logging_config.py."""

import contextlib
import logging

import pytest

from logging_config import logged


def test_logged_logs_entry_and_exit(caplog: pytest.LogCaptureFixture) -> None:
    """A decorated function logs its entry and exit and still works."""

    @logged
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    with caplog.at_level(logging.INFO):
        result = say_hello("Boris")

    assert result == "Hello, Boris!"
    assert "Entering say_hello" in caplog.text
    assert "Exiting say_hello" in caplog.text


def test_logged_logs_errors(caplog: pytest.LogCaptureFixture) -> None:
    """A decorated function that raises logs the error before re-raising."""

    @logged
    def explode() -> None:
        raise ValueError("boom")

    with caplog.at_level(logging.INFO), contextlib.suppress(ValueError):
        explode()

    assert "Error in explode" in caplog.text
    assert "boom" in caplog.text
