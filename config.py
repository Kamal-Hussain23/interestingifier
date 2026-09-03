"""Configuration helpers for Interestingifier.

Owns how we read secrets from the environment — a single, safe seam for the
Gemini API key so the rest of the app never touches os.environ directly.
"""

import os

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"


def get_gemini_api_key() -> str:
    """Return the Gemini API key from the environment.

    Raises a clear RuntimeError if the key is missing or blank, so callers get
    an obvious message instead of a confusing downstream failure. The app can
    boot without a key — this only raises when a Gemini service is used.
    """
    key = os.environ.get(GEMINI_API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"Missing environment variable {GEMINI_API_KEY_ENV} — set it before "
            "using the Gemini services."
        )
    return key
