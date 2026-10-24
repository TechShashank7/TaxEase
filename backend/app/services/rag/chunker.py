"""
chunker.py
──────────
Section-aware hierarchical chunking for the Income Tax Act PDF.

Chunking strategy:
  1. The text of each PDF page is first split into logical blocks using
     section boundary detection (chapter headings and section headers).
  2. Each block is further split if it exceeds MAX_TOKENS_PER_CHUNK.
  3. Overlap between sub-chunks preserves context across token boundaries.

The chunker does NOT embed or index — it only produces clean text chunks
with attached metadata. Embedding is Sprint 2.

Key design decisions:
  - A "section boundary" is any line matching a section-start pattern.
  - Chapter headings reset the current chapter context.
  - Sub-section splitting uses a sliding window with CHUNK_OVERLAP_TOKENS.
  - tiktoken (cl100k_base encoder) is used for token counting because it
    gives stable, model-agnostic token estimates.
"""

import re
import logging
from typing import Iterator

import tiktoken

from app.services.rag.metadata_extractor import (
    extract_chapter,
    extract_section_number,
    extract_subsection,
    build_chunk_metadata,
)

logger = logging.getLogger(__name__)

# ── Tokenizer ────────────────────────────────────────────────────────────────
# cl100k_base is used for token counting only — not for any model call.
_ENCODER = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def _token_split(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """
    Splits a text string into sub-strings of at most max_tokens tokens.
    Adjacent sub-strings share overlap_tokens tokens for context continuity.

    Uses a word-boundary split strategy to avoid breaking mid-word,
    then greedily fills up to max_tokens tokens per window.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        # Greedy fill
        end = start
        current_tokens = 0
        while end < len(words):
            word_tokens = _count_tokens(words[end] + " ")
            if current_tokens + word_tokens > max_tokens:
                break
            current_tokens += word_tokens
            end += 1

        chunk_text = " ".join(words[start:end]).strip()
        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(words):
            break

        # Overlap: step back by overlap_tokens worth of words
        overlap_word_count = 0
        overlap_tokens_counted = 0
        while overlap_word_count < (end - start) and overlap_tokens_counted < overlap_tokens:
            overlap_word_count += 1
            overlap_tokens_counted += _count_tokens(words[end - overlap_word_count] + " ")

        start = end - overlap_word_count

    return chunks


# ── Section boundary detection ────────────────────────────────────────────────

# A line is treated as a "section boundary" if it looks like a numbered section
# header at the start of a logical line (possibly with some leading whitespace).
_RE_BOUNDARY_CHAPTER = re.compile(
    r"^\s*CHAPTER\s+[IVXLCDM]",
    re.IGNORECASE | re.MULTILINE,
)

_RE_BOUNDARY_SECTION = re.compile(
    r"^\s*(\d{1,3}[A-Z]{0,4}[a-z]?)\.\s+[A-Z]",
    re.MULTILINE,
)

# A paragraph boundary is a blank line (2+ newlines).
_RE_BLANK_LINE = re.compile(r"\n{2,}")


def _split_into_blocks(page_text: str) -> list[str]:
    """
    Splits a page's text into logical blocks at chapter/section boundaries.

    A "block" is the text between two consecutive boundaries.
    Blocks that are pure whitespace are discarded.
    """
    # Find all boundary positions
    boundaries: list[int] = [0]

    for m in _RE_BOUNDARY_CHAPTER.finditer(page_text):
        boundaries.append(m.start())
    for m in _RE_BOUNDARY_SECTION.finditer(page_text):
        boundaries.append(m.start())

    boundaries = sorted(set(boundaries))
    boundaries.append(len(page_text))

    blocks: list[str] = []
    for i in range(len(boundaries) - 1):
        block = page_text[boundaries[i] : boundaries[i + 1]].strip()
        if block:
            blocks.append(block)

    # If no boundaries were detected (plain prose page), treat entire
    # page as a single block.
    if not blocks:
        stripped = page_text.strip()
        if stripped:
            blocks = [stripped]

    return blocks


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_page(
    page_text: str,
    page_number: int,
    source_document: str,
    start_chunk_index: int,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
    current_chapter_code: str = "",
    current_chapter_title: str = "",
) -> tuple[list[dict], int, str, str]:
    """
    Processes a single PDF page into one or more metadata-rich chunks.

    Args:
        page_text          : Raw text extracted from the page.
        page_number        : 1-based PDF page number.
        source_document    : Filename of the source PDF.
        start_chunk_index  : Global chunk index to begin numbering from.
        max_tokens         : Max tokens per chunk (default 400).
        overlap_tokens     : Overlap between token-split sub-chunks (default 50).
        current_chapter_code  : Chapter carried over from the previous page.
        current_chapter_title : Chapter title carried over from the previous page.

    Returns:
        (chunks, next_chunk_index, updated_chapter_code, updated_chapter_title)
        where `chunks` is a list of metadata dicts ready for embedding.
    """
    chunks: list[dict] = []
    chunk_index = start_chunk_index

    blocks = _split_into_blocks(page_text)

    for block in blocks:
        # Update chapter context if this block contains a chapter heading.
        detected_chapter, detected_title = extract_chapter(block)
        if detected_chapter:
            current_chapter_code = detected_chapter
            current_chapter_title = detected_title

        # Detect section number for the block.
        section_number = extract_section_number(block)
        subsection = extract_subsection(block)

        token_count = _count_tokens(block)

        if token_count <= max_tokens:
            # Block fits in a single chunk.
            meta = build_chunk_metadata(
                text=block,
                page_number=page_number,
                source_document=source_document,
                chunk_index=chunk_index,
                chapter_code=current_chapter_code,
                chapter_title=current_chapter_title,
                section_number=section_number,
                subsection=subsection,
            )
            chunks.append(meta)
            chunk_index += 1
        else:
            # Block is too large — split into token-bounded sub-chunks.
            sub_chunks = _token_split(block, max_tokens, overlap_tokens)
            logger.debug(
                f"Page {page_number}: block with {token_count} tokens split into "
                f"{len(sub_chunks)} sub-chunks."
            )
            for sub_text in sub_chunks:
                meta = build_chunk_metadata(
                    text=sub_text,
                    page_number=page_number,
                    source_document=source_document,
                    chunk_index=chunk_index,
                    chapter_code=current_chapter_code,
                    chapter_title=current_chapter_title,
                    section_number=section_number,
                    subsection=subsection,
                )
                chunks.append(meta)
                chunk_index += 1

    return chunks, chunk_index, current_chapter_code, current_chapter_title


def chunk_document(
    pages: list[tuple[int, str]],
    source_document: str,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
) -> list[dict]:
    """
    Processes all pages of a document and returns the full list of chunks.

    Args:
        pages           : List of (page_number, page_text) tuples.
        source_document : Filename of the source PDF.
        max_tokens      : Max tokens per chunk.
        overlap_tokens  : Overlap between sub-chunks.

    Returns:
        List of metadata dicts — one per chunk — ready for embedding.
    """
    all_chunks: list[dict] = []
    chunk_index = 0
    chapter_code = ""
    chapter_title = ""

    for page_number, page_text in pages:
        if not page_text.strip():
            logger.debug(f"Page {page_number}: empty — skipped.")
            continue

        page_chunks, chunk_index, chapter_code, chapter_title = chunk_page(
            page_text=page_text,
            page_number=page_number,
            source_document=source_document,
            start_chunk_index=chunk_index,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            current_chapter_code=chapter_code,
            current_chapter_title=chapter_title,
        )
        all_chunks.extend(page_chunks)

    logger.info(
        f"Chunking complete: {len(pages)} pages → {len(all_chunks)} chunks."
    )
    return all_chunks
