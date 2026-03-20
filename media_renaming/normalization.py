"""Name normalization helpers."""

from __future__ import annotations

import re

from .constants import (
    AUDIO_CHANNEL_RE,
    BRACKET_RE,
    COMPOUND_TOKEN_RE,
    FRAMERATE_RE,
    LANGUAGE_TAG_RE,
    METADATA_PARENS_RE,
    MULTISPACE_RE,
    NORMALIZED_TOKEN_SET,
    ORPHAN_PARENS_RE,
    RELEASE_GROUP_RE,
    RESOLUTION_RE,
    SEPARATOR_RE,
    TRAILING_GROUP_RE,
    WEBSITE_RE,
    YEAR_RE,
)


def normalize_token(token: str) -> str:
    """Normalize tokens for reliable metadata filtering."""
    return re.sub(r"[^a-z0-9]+", "", token.lower())


# Articles, conjunctions, prepositions that should stay lowercase mid-title
_LOWERCASE_WORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "by", "of", "from", "with", "as", "vs",
}


def smart_title(words: list[str]) -> str:
    """Apply title casing: capitalize first/last word, lowercase articles mid-title."""
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

    # Lowercase articles/prepositions mid-title (not first or last)
    for i in range(1, len(title_words) - 1):
        if title_words[i].lower() in _LOWERCASE_WORDS:
            title_words[i] = title_words[i].lower()

    return " ".join(title_words)


def normalize_name(stem: str) -> str:
    """Strip metadata and format the cleaned title with an optional year."""
    cleaned = BRACKET_RE.sub(" ", stem)
    # Strip parenthesized metadata blocks that contain resolution (e.g. (1080p x265 ...))
    cleaned = METADATA_PARENS_RE.sub(" ", cleaned)
    cleaned = TRAILING_GROUP_RE.sub("", cleaned)
    # Strip website watermarks (e.g. www.UIndex.org, YTS.mx)
    cleaned = WEBSITE_RE.sub(" ", cleaned)
    cleaned = SEPARATOR_RE.sub(" ", cleaned)
    # Remove compound tokens after dots become spaces (e.g. DDP5 1, H 264)
    cleaned = COMPOUND_TOKEN_RE.sub(" ", cleaned)
    # Strip trailing release groups (e.g. -KyoGo, -SPARKS)
    cleaned = RELEASE_GROUP_RE.sub("", cleaned)
    # Strip language tags (e.g. GER-ENG, ENG)
    cleaned = LANGUAGE_TAG_RE.sub(" ", cleaned)
    # Clean up orphaned/empty parentheses left after token removal
    cleaned = ORPHAN_PARENS_RE.sub("", cleaned)
    cleaned = MULTISPACE_RE.sub(" ", cleaned).strip()

    words = []
    year_candidates = []
    for raw in cleaned.split(" "):
        token = raw.strip("-_")
        if not token:
            continue
        normalized = normalize_token(token)
        if YEAR_RE.match(token):
            year_candidates.append((len(words), token))
            continue
        if RESOLUTION_RE.match(normalized) or FRAMERATE_RE.match(normalized):
            continue
        if AUDIO_CHANNEL_RE.match(token):
            continue
        if normalized in NORMALIZED_TOKEN_SET:
            continue
        words.append(token)

    # Use the last year as the release year; earlier years are part of the title
    year = None
    if year_candidates:
        if words or len(year_candidates) > 1:
            # Last year found is the release year
            release_idx, release_year = year_candidates[-1]
            year = release_year
            # Re-insert earlier years into the title at their original positions
            for insert_offset, (pos, yr) in enumerate(year_candidates[:-1]):
                words.insert(pos + insert_offset, yr)
        else:
            # Single year and no title words — treat it as the title
            words.append(year_candidates[0][1])

    title = smart_title(words)
    if not title:
        title = "Unknown Title"

    if year:
        return f"{title} ({year})"
    return title
