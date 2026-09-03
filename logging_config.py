"""Logging setup and the @logged decorator.

Logging stays out of the business logic: functions just do their job and the
@logged decorator reports what happened, when it happened, and how long it took.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def setup_logging() -> None:
    """Configure console logging so log messages are easy to read."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def logged(func: Callable[P, T]) -> Callable[P, T]:
    """Log when func starts, when it finishes, and how long it took.

    If func raises, the error is logged and then re-raised unchanged.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger = logging.getLogger(func.__module__)
        logger.info("Entering %s", func.__name__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.exception("Error in %s", func.__name__)
            raise
        duration = time.perf_counter() - start
        logger.info("Exiting %s (%.3fs)", func.__name__, duration)
        return result

    return wrapper
