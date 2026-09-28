"""Splitting long courses into chunks that fit in one LLM call.

Why: a full semester of slides can be hundreds of pages. Sending everything in
one request is slow, expensive, can exceed the model's context window, and
the model tends to skip what is in the middle of a very long input
("lost in the middle"). So long courses are cut into chunks and processed in a
map -> reduce way (see ``generator.py``).

Token counts are *estimated* (about 4 characters per token for English /
French text). It is not exact, but it is free and good enough to decide
whether to chunk. We keep a safety margin in the budgets for that reason.
"""

from __future__ import annotations

import re

CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate (no API call)."""
    return len(text) // CHARS_PER_TOKEN + 1


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Cut a paragraph that is bigger than a whole chunk, on sentence ends if possible."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces, current = [], ""
    for sentence in sentences:
        # A single giant "sentence" (e.g. a table dump): hard cut.
        while len(sentence) > max_chars:
            pieces.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        if current and len(current) + len(sentence) + 1 > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_tokens: int = 8000, overlap_tokens: int = 200) -> list[str]:
    """Split ``text`` into chunks of at most ~``max_tokens``.

    Chunks are built from whole paragraphs so a definition is not cut in half.
    The last paragraph(s) of a chunk are repeated at the start of the next one
    (``overlap_tokens``) so context at the boundary is not lost.
    """
    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    if len(text) <= max_chars:
        return [text]

    paragraphs: list[str] = []
    for paragraph in text.split("\n\n"):
        if len(paragraph) > max_chars:
            paragraphs.extend(_split_long_paragraph(paragraph, max_chars))
        elif paragraph.strip():
            paragraphs.append(paragraph)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if current and current_len + len(paragraph) + 2 > max_chars:
            chunks.append("\n\n".join(current))
            # Start the next chunk with the tail of the previous one.
            tail: list[str] = []
            tail_len = 0
            for previous in reversed(current):
                if tail_len + len(previous) > overlap_chars:
                    break
                tail.insert(0, previous)
                tail_len += len(previous) + 2
            current, current_len = tail, tail_len
        current.append(paragraph)
        current_len += len(paragraph) + 2

    if current:
        chunks.append("\n\n".join(current))
    return chunks
