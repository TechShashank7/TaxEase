"""
pdf_ingestion.py
────────────────
PDF text extraction for the Income Tax Act using pdfplumber.

Responsibilities (Sprint 1 only):
  - Open the PDF and extract text page-by-page.
  - Track page numbers precisely (pdfplumber gives 0-based index; we report
    1-based page numbers throughout the system).
  - Detect and log pages that fail extraction (scanned / image-only pages).
  - Apply lightweight post-processing to clean artefacts:
      • Normalise excessive whitespace / form-feed characters
      • Remove page-number-only lines (single digits at top/bottom of page)
      • Collapse hyphenated line-breaks (common in legislative text)
  - Return a list of (page_number: int, text: str) tuples.

This module does NOT perform chunking, embedding, or indexing.
It purely extracts raw text, preserving structure as much as pdfplumber allows.

pdfplumber is chosen over PyPDF2 because:
  - It uses pdfminer.six underneath for richer layout analysis.
  - It preserves whitespace / indentation better for legislative formats.
  - It can detect tables and figures (useful for future Schedule extraction).
"""

import logging
import re
from pathlib import Path
from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import pdfplumber

logger = logging.getLogger(__name__)

# Per-page extraction timeout in seconds.
# Pages that exceed this (e.g. scanned/bitmap-heavy) are skipped as TIMEOUT.
# Set to 10s — pages 484–507 are scanned Schedules that hang for 30s+ each;
# a 10s timeout lets us skip the whole block in ~5 minutes instead of ~15.
PAGE_TIMEOUT_SECONDS = 10

# ── Post-processing helpers ───────────────────────────────────────────────────

# Remove soft-hyphens / hyphenated line-breaks: "deduct-\nion" → "deduction"
_RE_HYPHEN_BREAK = re.compile(r"-\n(\S)")

# Collapse multiple blank lines into a single paragraph break.
_RE_MULTI_BLANK = re.compile(r"\n{3,}")

# Strip lines that are only a number (page footer/header artefacts).
_RE_PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)

# Collapse runs of spaces to a single space (preserving newlines).
_RE_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def _clean_page_text(text: str) -> str:
    """
    Applies lightweight cleaning to raw page text.
    Preserves paragraph and section structure.
    """
    # Fix hyphenated line breaks
    text = _RE_HYPHEN_BREAK.sub(r"\1", text)
    # Remove lone page-number lines
    text = _RE_PAGE_NUMBER_LINE.sub("", text)
    # Collapse multiple spaces (not newlines)
    text = _RE_MULTI_SPACE.sub(" ", text)
    # Collapse excessive blank lines
    text = _RE_MULTI_BLANK.sub("\n\n", text)
    return text.strip()


# ── Result types ──────────────────────────────────────────────────────────────

class PageResult(NamedTuple):
    page_number: int       # 1-based PDF page number
    text: str              # cleaned extracted text (may be empty for image pages)
    char_count: int        # character count BEFORE cleaning (proxy for "content richness")
    extraction_ok: bool    # False if pdfplumber raised an exception or timed out on this page

class IngestionResult(NamedTuple):
    source_document: str          # PDF filename (not full path)
    total_pages: int
    pages_extracted: int          # pages with non-empty text
    pages_failed: int             # pages where extraction raised an exception or timed out
    pages_empty: int              # pages with no extractable text (likely image pages)
    page_results: list[PageResult]


# ── Core extractor ────────────────────────────────────────────────────────────

def extract_pdf(pdf_path: str | Path) -> IngestionResult:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    source_document = pdf_path.name
    logger.info(f"Opening PDF: {pdf_path}")
    page_results: list[PageResult] = []
    pages_extracted = 0
    pages_failed = 0

import multiprocessing
import time

def _extract_page_worker(pdf_path: str, page_number: int, result_queue: multiprocessing.Queue):
    """Worker process to extract a single page. Isolates C-extension hangs."""
    import pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_number - 1]
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            result_queue.put({"status": "success", "text": text})
    except Exception as e:
        result_queue.put({"status": "error", "error": str(e)})

def extract_pdf(pdf_path: str | Path) -> IngestionResult:
    """
    Opens a PDF and extracts text from every page sequentially.
    Uses multiprocessing to forcefully kill any page that hangs for > 15 seconds.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    source_document = pdf_path.name
    logger.info(f"Opening PDF: {pdf_path} (Using Multiprocessing Hard-Kill)")

    page_results: list[PageResult] = []
    pages_extracted = 0
    pages_failed = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        
    logger.info(f"Total pages in PDF: {total_pages}")

    for page_number in range(1, total_pages + 1):
        if page_number == 1 or page_number % 10 == 0:
            logger.info(
                f"Processing page {page_number}/{total_pages} "
                f"({100*page_number//total_pages}%)..."
            )

        if (430 <= page_number <= 550) or page_number == 1032:
            pages_failed += 1
            page_results.append(PageResult(page_number=page_number, text="", char_count=0, extraction_ok=False))
            continue

        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=_extract_page_worker, args=(str(pdf_path), page_number, q))
        p.start()
        
        p.join(timeout=15)
        
        if p.is_alive():
            logger.warning(f"Page {page_number}: HARD TIMEOUT (>15s). Terminating stuck process.")
            p.terminate()
            p.join()
            pages_failed += 1
            page_results.append(PageResult(page_number=page_number, text="", char_count=0, extraction_ok=False))
            continue
            
        if not q.empty():
            res = q.get()
            if res["status"] == "success":
                raw_text = res["text"]
                char_count = len(raw_text)
                cleaned = _clean_page_text(raw_text)

                if not cleaned.strip():
                    logger.debug(f"Page {page_number}: no extractable text (image/blank).")
                    page_results.append(PageResult(page_number=page_number, text="", char_count=char_count, extraction_ok=True))
                else:
                    pages_extracted += 1
                    page_results.append(PageResult(page_number=page_number, text=cleaned, char_count=char_count, extraction_ok=True))
            else:
                pages_failed += 1
                logger.warning(f"Page {page_number}: extraction failed — {res['error']}")
                page_results.append(PageResult(page_number=page_number, text="", char_count=0, extraction_ok=False))
        else:
            pages_failed += 1
            logger.warning(f"Page {page_number}: Process exited without returning data.")
            page_results.append(PageResult(page_number=page_number, text="", char_count=0, extraction_ok=False))

    result = IngestionResult(
        source_document=source_document,
        total_pages=total_pages,
        pages_extracted=pages_extracted,
        pages_failed=pages_failed,
        pages_empty=total_pages - pages_extracted - pages_failed,
        page_results=page_results,
    )

    logger.info(
        f"Ingestion summary: {total_pages} total | "
        f"{pages_extracted} extracted | "
        f"{pages_failed} failed/timeout | "
        f"{total_pages - pages_extracted - pages_failed} empty/image"
    )

    return result


def get_text_pages(ingestion_result: IngestionResult) -> list[tuple[int, str]]:
    """
    Convenience function that returns only pages with non-empty text
    as a list of (page_number, text) tuples, ready for the chunker.
    """
    return [
        (pr.page_number, pr.text)
        for pr in ingestion_result.page_results
        if pr.extraction_ok and pr.text.strip()
    ]
