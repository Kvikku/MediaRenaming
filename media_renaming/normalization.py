"""Name normalization helpers."""

from __future__ import annotations

import re

from .constants import (
    AUDIO_CHANNEL_RE,
    BRACKET_RE,
    FRAMERATE_RE,
    MULTISPACE_RE,
    NORMALIZED_TOKEN_SET,
    RESOLUTION_RE,
    SEPARATOR_RE,
    TRAILING_GROUP_RE,
    YEAR_RE,
)


def normalize_token(token: str) -> str:
    """Normalize tokens for reliable metadata filtering."""
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def smart_title(words: list[str]) -> str:
    """Apply simple title casing while preserving acronyms and numbers."""
    title_words = []
    for word in words:
        if not word:
            continue
        if any(char.isdigit() for char in word):
            title_words.append(word)
            continue
        if word.isupper() and len(word) <= 4:
            title_words.append(word)
            continue
        title_words.append(word[:1].upper() + word[1:].lower())
    return " ".join(title_words)


def normalize_name(stem: str) -> str:
    """Strip metadata and format the cleaned title with an optional year."""
    cleaned = BRACKET_RE.sub(" ", stem)
    cleaned = TRAILING_GROUP_RE.sub("", cleaned)
    cleaned = SEPARATOR_RE.sub(" ", cleaned)
    cleaned = MULTISPACE_RE.sub(" ", cleaned).strip()

    words = []
    year = None
    for raw in cleaned.split(" "):
        token = raw.strip("-_")
        if not token:
            continue
        normalized = normalize_token(token)
        if YEAR_RE.match(token) and year is None:
            year = token
            continue
        if RESOLUTION_RE.match(normalized) or FRAMERATE_RE.match(normalized):
            continue
        if AUDIO_CHANNEL_RE.match(token):
            continue
        if normalized in NORMALIZED_TOKEN_SET:
            continue
        words.append(token)

    title = smart_title(words)
    if not title:
        title = "Unknown Title"

    if year:
        return f"{title} ({year})"
    return title
