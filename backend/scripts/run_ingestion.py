#!/usr/bin/env python3
"""
run_ingestion.py
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Sprint 1 CLI â€” PDF ingestion, chunking, and metadata validation.

This is an ADMIN-ONLY tool. It is NOT exposed as a web endpoint.
Run it once to prepare the Income Tax Act for embedding (Sprint 2).

Usage:
    python scripts/run_ingestion.py [PDF_PATH] [OPTIONS]

    PDF_PATH     Path to the Income Tax Act PDF.
                 Defaults to backend/data/income_tax_act.pdf

Options:
    --max-tokens INT     Max tokens per chunk (default: 400)
    --overlap INT        Overlap tokens between sub-chunks (default: 50)
    --output DIR         Directory to save chunks JSON (default: backend/data)
    --sample INT         Number of sample chunks to print (default: 5)
    --verbose            Enable DEBUG logging

Output files:
    data/chunks.json          All chunks with full metadata (Sprint 2 input)
    data/ingestion_log.json   Ingestion statistics and error report

Responsibility:
    Rules Engine  â†’ eligibility/recommendations (UNCHANGED, not called here)
    This script   â†’ PDF â†’ chunks with metadata (Sprint 1 only)
    Sprint 2      â†’ chunks â†’ embeddings â†’ Qdrant index
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# â”€â”€ Path bootstrap â€” allow running from project root or scripts/ dir â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import settings
from app.services.rag.pdf_ingestion import extract_pdf, get_text_pages
from app.services.rag.chunker import chunk_document
from app.services.rag.metadata_extractor import validate_metadata


# â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy internal debug output from pdfminer/pdfplumber even when
    # --verbose is passed. Our own loggers still use the configured level.
    for noisy_lib in ("pdfminer", "pdfplumber", "PIL", "pypdfium2"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


# â”€â”€ Argument parsing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _parse_args() -> argparse.Namespace:
    default_pdf = _BACKEND_DIR / settings.PDF_DATA_DIR / "income_tax_act.pdf"
    default_output = _BACKEND_DIR / settings.PDF_DATA_DIR

    parser = argparse.ArgumentParser(
        description="TaxEase Sprint 1 â€” Income Tax Act PDF Ingestion CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=str(default_pdf),
        help=f"Path to Income Tax Act PDF (default: {default_pdf})",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=settings.MAX_TOKENS_PER_CHUNK,
        help=f"Max tokens per chunk (default: {settings.MAX_TOKENS_PER_CHUNK})",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=settings.CHUNK_OVERLAP_TOKENS,
        help=f"Overlap tokens between sub-chunks (default: {settings.CHUNK_OVERLAP_TOKENS})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(default_output),
        help=f"Output directory (default: {default_output})",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="Number of sample chunks to print to console (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return parser.parse_args()


# â”€â”€ Statistics helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _collect_section_stats(chunks: list[dict]) -> dict:
    """Returns per-section chunk counts and coverage info."""
    section_counts: dict[str, int] = {}
    missing_section = 0
    missing_chapter = 0
    missing_page = 0

    for c in chunks:
        sec = c.get("section_number", "")
        if sec:
            section_counts[sec] = section_counts.get(sec, 0) + 1
        else:
            missing_section += 1

        if not c.get("chapter"):
            missing_chapter += 1
        if not c.get("page_number"):
            missing_page += 1

    return {
        "unique_sections_detected": len(section_counts),
        "chunks_without_section": missing_section,
        "chunks_without_chapter": missing_chapter,
        "chunks_without_page_number": missing_page,
        "top_sections_by_chunk_count": dict(
            sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        ),
    }


def _print_sample_chunks(chunks: list[dict], n: int) -> None:
    """Prints n evenly-spaced sample chunks with their metadata."""
    total = len(chunks)
    if total == 0:
        print("  No chunks produced.")
        return

    step = max(1, total // n)
    indices = list(range(0, total, step))[:n]

    for idx in indices:
        c = chunks[idx]
        print(f"\n  â”€â”€ Chunk #{c['chunk_index']} â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"     section_number  : {c['section_number'] or '(not detected)'}")
        print(f"     chapter         : {c['chapter'] or '(not detected)'}")
        print(f"     chapter_title   : {c['chapter_title'] or '(not detected)'}")
        print(f"     subsection      : {c['subsection'] or '(none)'}")
        print(f"     page_number     : {c['page_number']}")
        print(f"     source_document : {c['source_document']}")
        print(f"     chunk_index     : {c['chunk_index']}")
        print(f"     text preview    : {c['text'][:200].replace(chr(10), ' ')}...")


# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main() -> int:
    args = _parse_args()
    _setup_logging(args.verbose)
    logger = logging.getLogger("run_ingestion")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_ts = datetime.now(timezone.utc).isoformat()

    print("\n" + "=" * 70)
    print("  TaxEase â€” Sprint 1: PDF Ingestion & Chunking")
    print("=" * 70)
    print(f"  PDF            : {args.pdf_path}")
    print(f"  Max tokens     : {args.max_tokens}")
    print(f"  Overlap tokens : {args.overlap}")
    print(f"  Output dir     : {output_dir}")
    print(f"  Started at     : {run_ts}")
    print("=" * 70 + "\n")

    # â”€â”€ Step 1: PDF extraction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("Step 1 â€” Extracting text from PDF...")
    try:
        ingestion_result = extract_pdf(args.pdf_path)
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("\nPlace the Income Tax Act PDF at:")
        print(f"  {args.pdf_path}")
        print("Then re-run this script.")
        return 1
    except Exception as e:
        print(f"\n[ERROR] PDF extraction failed: {e}")
        logger.exception("PDF extraction failed")
        return 1

    print(f"  [OK] Total pages       : {ingestion_result.total_pages}")
    print(f"  [OK] Pages extracted   : {ingestion_result.pages_extracted}")
    print(f"  [OK] Pages failed      : {ingestion_result.pages_failed}")
    print(f"  [OK] Pages empty/image : {ingestion_result.pages_empty}")

    if ingestion_result.pages_extracted == 0:
        print("\n[ERROR] No text extracted. The PDF may be scanned/image-only.")
        print("Consider using an OCR-processed version of the Income Tax Act.")
        return 1

    # Collect failed pages for the log
    failed_pages = [
        pr.page_number
        for pr in ingestion_result.page_results
        if not pr.extraction_ok
    ]
    empty_pages = [
        pr.page_number
        for pr in ingestion_result.page_results
        if pr.extraction_ok and not pr.text.strip()
    ]

    # â”€â”€ Step 2: Chunking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\nStep 2 â€” Section-aware chunking...")
    text_pages = get_text_pages(ingestion_result)

    chunks = chunk_document(
        pages=text_pages,
        source_document=ingestion_result.source_document,
        max_tokens=args.max_tokens,
        overlap_tokens=args.overlap,
    )

    print(f"  [OK] Chunks produced   : {len(chunks)}")

    # â”€â”€ Step 3: Metadata validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\nStep 3 â€” Validating chunk metadata...")
    chunks_with_warnings: list[dict] = []
    valid_count = 0

    for chunk in chunks:
        is_valid, warnings = validate_metadata(chunk)
        if is_valid:
            valid_count += 1
        else:
            chunks_with_warnings.append(
                {"chunk_index": chunk["chunk_index"], "warnings": warnings}
            )

    print(f"  [OK] Chunks fully valid     : {valid_count}")
    print(f"  [!] Chunks with warnings  : {len(chunks_with_warnings)}")

    # â”€â”€ Step 4: Section statistics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\nStep 4 â€” Section coverage analysis...")
    section_stats = _collect_section_stats(chunks)
    print(f"  [OK] Unique sections detected      : {section_stats['unique_sections_detected']}")
    print(f"  [!] Chunks without section_number : {section_stats['chunks_without_section']}")
    print(f"  [!] Chunks without chapter        : {section_stats['chunks_without_chapter']}")

    if section_stats["top_sections_by_chunk_count"]:
        print("\n  Top sections by chunk count:")
        for sec, cnt in list(section_stats["top_sections_by_chunk_count"].items())[:10]:
            print(f"    Section {sec:>10s} : {cnt} chunks")

    # â”€â”€ Step 5: Save chunks JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    chunks_path = output_dir / "chunks.json"
    print(f"\nStep 5 â€” Saving chunks to {chunks_path} ...")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"  âœ“ Saved {len(chunks)} chunks ({chunks_path.stat().st_size / 1024:.1f} KB)")

    # â”€â”€ Step 6: Save ingestion log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    log_path = output_dir / "ingestion_log.json"
    ingestion_log = {
        "run_timestamp": run_ts,
        "source_pdf": args.pdf_path,
        "source_document": ingestion_result.source_document,
        "ingestion_config": {
            "max_tokens_per_chunk": args.max_tokens,
            "chunk_overlap_tokens": args.overlap,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "qdrant_collection": settings.QDRANT_COLLECTION,
        },
        "extraction_summary": {
            "total_pages": ingestion_result.total_pages,
            "pages_extracted": ingestion_result.pages_extracted,
            "pages_failed": ingestion_result.pages_failed,
            "pages_empty": ingestion_result.pages_empty,
            "failed_page_numbers": failed_pages,
            "empty_page_numbers": empty_pages[:50],  # cap to 50 for log readability
        },
        "chunking_summary": {
            "total_chunks": len(chunks),
            "chunks_fully_valid": valid_count,
            "chunks_with_warnings": len(chunks_with_warnings),
            "warning_details": chunks_with_warnings[:100],  # cap to 100 for log
        },
        "section_coverage": section_stats,
        "sprint_status": "Sprint 1 complete â€” ready for Sprint 2 (embedding + indexing)",
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(ingestion_log, f, ensure_ascii=False, indent=2)
    print(f"  âœ“ Ingestion log saved to {log_path}")

    # â”€â”€ Step 7: Sample chunks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if args.sample > 0:
        print(f"\nStep 7 â€” Sample chunks (n={args.sample}):")
        _print_sample_chunks(chunks, args.sample)

    # â”€â”€ Final summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n" + "=" * 70)
    print("  Sprint 1 Complete")
    print("=" * 70)
    print(f"  Pages extracted   : {ingestion_result.pages_extracted} / {ingestion_result.total_pages}")
    print(f"  Sections detected : {section_stats['unique_sections_detected']}")
    print(f"  Chunks created    : {len(chunks)}")
    print(f"  Chunks valid      : {valid_count}")
    print(f"  Output            : {chunks_path}")
    print(f"  Log               : {log_path}")
    print("\n  Next step: Sprint 2 â€” embed chunks using")
    print(f"  model={settings.EMBEDDING_MODEL}, dim={settings.EMBEDDING_DIMENSION}")
    print("  then index into Qdrant collection:", settings.QDRANT_COLLECTION)
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
