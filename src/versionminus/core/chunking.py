"""Chunking strategies and helpers for embeddings.

This module centralizes the chunking logic used by the embeddings pipeline so
that different boundary policies can be selected dynamically (manually or via
chunk-policy detection agents).

Policies are implemented with a common packer that respects token budgets while
preserving semantic boundaries (paragraphs, sentences, code blocks, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, List, Optional

import re

from versionminus.core.config import Settings, get_settings


class ChunkBoundaryPolicy(str, Enum):
    """Available chunk boundary strategies."""

    PARAGRAPH_SENTENCE = "paragraph_sentence"
    SENTENCE_FIRST = "sentence_first"
    CODE_BLOCKS = "code_blocks"
    HEADINGS_LISTS = "headings_lists"
    MINIMAL_WORDS = "minimal_words"


DEFAULT_POLICY = ChunkBoundaryPolicy.PARAGRAPH_SENTENCE


@dataclass
class Chunk:
    """Returned chunk data with ordering metadata."""

    text: str
    index: int
    total: int
    policy: ChunkBoundaryPolicy


class TokenCounter:
    """Helper that encapsulates tokenizer selection and fallbacks."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._encoder = None

    @property
    def encoder(self):  # pragma: no cover - optional dependency loading path
        if self._encoder is not None:
            return self._encoder
        try:
            import tiktoken  # type: ignore

            model_name = self.settings.rag_embedding_model or "text-embedding-3-small"
            try:
                self._encoder = tiktoken.encoding_for_model(model_name)
            except Exception:
                self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoder = None
        return self._encoder

    def count(self, text: str) -> int:
        if not text:
            return 0
        encoder = self.encoder
        if encoder is None:
            return len(text.split())
        try:
            return len(encoder.encode(text))  # type: ignore[operator]
        except Exception:
            return len(text.split())

    def tail(self, text: str, tokens: int) -> str:
        if tokens <= 0 or not text:
            return ""
        encoder = self.encoder
        if encoder is None:
            words = text.split()
            return " ".join(words[-tokens:]) if words else ""
        try:
            encoded = encoder.encode(text)
            slice_tokens = encoded[-tokens:]
            return encoder.decode(slice_tokens) if slice_tokens else ""
        except Exception:
            words = text.split()
            return " ".join(words[-tokens:]) if words else ""


PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\(\[\"'])")
FENCE_SPLIT = re.compile(r"(^```[\s\S]*?^```)|(^~~~[\s\S]*?^~~~)", re.MULTILINE)
HEADING_LINE = re.compile(r"^#{1,6}\s")
LIST_LINE = re.compile(r"^(?:[-*+]\s|\d+\.\s)")


UnitBuilder = Callable[[str], Iterable[str]]


def _split_paragraph_sentence(text: str) -> Iterable[str]:
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT.split(text) if p.strip()]
    if not paragraphs:
        yield from _split_sentences(text)
        return
    for para in paragraphs:
        sentences = list(_split_sentences(para))
        if sentences:
            for sentence in sentences:
                yield sentence
        else:
            yield para


def _split_sentences(text: str) -> Iterable[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = [p.strip() for p in SENTENCE_SPLIT.split(stripped) if p.strip()]
    if parts:
        for part in parts:
            yield part
    else:
        yield stripped


def _split_code_blocks(text: str) -> Iterable[str]:
    if not text.strip():
        return []
    last = 0
    for match in FENCE_SPLIT.finditer(text):
        prefix = text[last : match.start()]
        if prefix.strip():
            yield from _split_paragraph_sentence(prefix)
        block = match.group(0)
        if block:
            yield block.strip()
        last = match.end()
    suffix = text[last:]
    if suffix.strip():
        yield from _split_paragraph_sentence(suffix)


def _split_headings_lists(text: str) -> Iterable[str]:
    lines = text.splitlines()
    if not lines:
        return []
    bucket: list[str] = []
    current_header: Optional[str] = None
    for line in lines:
        stripped = line.rstrip()
        if HEADING_LINE.match(stripped):
            if bucket:
                yield "\n".join(bucket).strip()
                bucket = []
            current_header = stripped
            bucket.append(stripped)
        elif LIST_LINE.match(stripped):
            if current_header is None:
                current_header = "list"
            bucket.append(stripped)
        else:
            bucket.append(stripped)
    if bucket:
        yield "\n".join(bucket).strip()


def _split_words(text: str, max_tokens: int, counter: TokenCounter) -> Iterable[str]:
    words = text.split()
    if not words:
        return []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        piece = " ".join(words[start:end])
        yield piece
        if end >= len(words):
            break
        overlap = min(max(int((end - start) * 0.1), 20), max_tokens)
        start = max(0, end - overlap)


def _build_units(text: str, policy: ChunkBoundaryPolicy) -> Iterable[str]:
    if policy == ChunkBoundaryPolicy.PARAGRAPH_SENTENCE:
        return _split_paragraph_sentence(text)
    if policy == ChunkBoundaryPolicy.SENTENCE_FIRST:
        return _split_sentences(text)
    if policy == ChunkBoundaryPolicy.CODE_BLOCKS:
        return _split_code_blocks(text)
    if policy == ChunkBoundaryPolicy.HEADINGS_LISTS:
        return _split_headings_lists(text)
    # Minimal fallback: simple word-level chunking units using paragraphs
    return [seg.strip() for seg in PARAGRAPH_SPLIT.split(text) if seg.strip()]


def _pack_units(units: Iterable[str], counter: TokenCounter, target: int) -> List[str]:
    chunks: List[str] = []
    buffer: list[str] = []
    buffer_tokens = 0

    def flush():
        nonlocal buffer, buffer_tokens
        if buffer:
            chunks.append(" ".join(buffer).strip())
            buffer = []
            buffer_tokens = 0

    for unit in units:
        if not unit.strip():
            continue
        utoks = counter.count(unit)
        if utoks > target * 1.2:  # huge unit, break down
            for sub in _split_words(unit, target, counter):
                stoks = counter.count(sub)
                if buffer_tokens and buffer_tokens + stoks > target:
                    flush()
                buffer.append(sub)
                buffer_tokens += stoks
                if buffer_tokens >= target:
                    flush()
            continue
        if buffer_tokens and buffer_tokens + utoks > target:
            flush()
        buffer.append(unit)
        buffer_tokens += utoks
        if buffer_tokens >= target:
            flush()

    flush()
    return [c for c in chunks if c.strip()]


def _apply_overlap(chunks: List[str], counter: TokenCounter, max_overlap: int) -> List[str]:
    if max_overlap <= 0 or len(chunks) <= 1:
        return chunks
    overlapped: List[str] = []
    prev = None
    for chunk in chunks:
        if prev is None:
            overlapped.append(chunk)
            prev = chunk
            continue
        prev_tokens = counter.count(prev)
        overlap_tokens = min(max(int(prev_tokens * 0.1), 20), max_overlap)
        tail = counter.tail(prev, overlap_tokens)
        combined = (tail + " " + chunk).strip() if tail else chunk
        overlapped.append(combined)
        prev = chunk
    return overlapped


def chunk_text(
    text: str,
    policy: ChunkBoundaryPolicy | str | None = None,
    settings: Optional[Settings] = None,
    max_tokens: Optional[int] = None,
    overlap_tokens: Optional[int] = None,
) -> List[Chunk]:
    """Chunk ``text`` according to ``policy``.

    Parameters
    ----------
    text: str
        Original text to chunk.
    policy: ChunkBoundaryPolicy | None
        Desired boundary policy; falls back to default if ``None``.
    settings: Settings | None
        Settings to consult for embedding defaults and tokenizer selection.
    max_tokens: int | None
        Target tokens per chunk; defaults to Settings.rag_embedding_model_output or
        MAX_CHUNK_TOKENS constant (800) when not provided.
    overlap_tokens: int | None
        Max overlap tokens between chunks. Defaults to CHUNK_OVERLAP (50).
    """

    if not text or not text.strip():
        return []

    settings = settings or get_settings()
    if isinstance(policy, ChunkBoundaryPolicy):
        resolved_policy = policy
    elif policy is None:
        raw_default = settings.chunk_boundary_policy_default or DEFAULT_POLICY.value
        try:
            resolved_policy = ChunkBoundaryPolicy(raw_default)
        except ValueError:
            resolved_policy = DEFAULT_POLICY
    else:
        try:
            resolved_policy = ChunkBoundaryPolicy(str(policy))
        except ValueError:
            resolved_policy = DEFAULT_POLICY

    target = max_tokens or getattr(settings, "chunk_target_tokens", None) or settings.rag_embedding_model_output or 800
    overlap = overlap_tokens or settings.chunk_overlap_tokens or 50  # type: ignore[attr-defined]

    counter = TokenCounter(settings)
    units = _build_units(text, resolved_policy)
    raw_chunks = _pack_units(units, counter, target)
    if not raw_chunks:
        raw_chunks = [text.strip()]
    overlapped = _apply_overlap(raw_chunks, counter, overlap)
    total = len(overlapped)
    return [
        Chunk(text=chunk, index=idx, total=total, policy=resolved_policy)
        for idx, chunk in enumerate(overlapped)
    ]


__all__ = [
    "ChunkBoundaryPolicy",
    "Chunk",
    "chunk_text",
]
