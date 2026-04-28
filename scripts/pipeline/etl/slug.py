"""Slug helpers — produce stable URL-safe IDs.

Players and teams need slugs that survive Arabic/Latin transliteration. We
prefer the English label for the slug since URLs are typically Latin, but
we keep the Arabic label as a separate field for display.
"""

from __future__ import annotations

import re
from slugify import slugify


_NON_ASCII = re.compile(r"[^\x00-\x7f]")


def to_slug(text: str) -> str:
    """Slugify a name. Strips diacritics, lowercases, hyphenates."""
    cleaned = slugify(text, lowercase=True, separator="-")
    if not cleaned:
        # Pure-Arabic input would produce empty after stripping. Fall back to
        # transliteration via simple replacement, otherwise hash.
        cleaned = _NON_ASCII.sub("", text).strip().lower()
        cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned or "unknown"
