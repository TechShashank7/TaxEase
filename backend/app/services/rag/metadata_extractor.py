"""
metadata_extractor.py
─────────────────────
Extracts structured metadata from raw text extracted from the Income Tax Act PDF.

Metadata extracted per chunk:
  - section_number  : e.g. "80C", "10", "24", "80CCD", "10(13A)"
  - chapter         : Roman numeral + letter suffix, e.g. "VI-A", "IV"
  - chapter_title   : Full chapter heading text
  - subsection      : e.g. "(1)", "(1A)", "(2B)"
  - page_number     : Integer page number from pdfplumber
  - source_document : Filename of the source PDF
  - chunk_index     : Sequential 0-based index within the document
  - text            : The chunk text itself

Design principles:
  - All regex patterns are compiled once at module load.
  - Extraction is heuristic — failures are logged, never raised.
  - All fields have safe defaults (empty string / 0) so downstream
    consumers never encounter KeyErrors.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Compiled regex patterns ───────────────────────────────────────────────────

# Chapter heading:  "CHAPTER VI-A", "CHAPTER XII-B", "CHAPTER I"
# Allows for optional trailing whitespace and colon
_RE_CHAPTER = re.compile(
    r"CHAPTER\s+([IVXLCDM]+-?[A-Z]*)",
    re.IGNORECASE,
)

# Chapter title: line immediately after a CHAPTER heading that is all-caps
# and not itself a section or clause. Used as a secondary fallback.
_RE_CHAPTER_TITLE = re.compile(
    r"^([A-Z][A-Z\s,\-\(\)\.]{10,})$",
    re.MULTILINE,
)

# Section header patterns — ordered from most-specific to least-specific
# Group 1 always captures the section number string.
#
# Pattern A: "80CCD."  "10AA."  "24."  (section at start of line)
_RE_SECTION_START = re.compile(
    r"^\s*(\d{1,3}[A-Z]{0,4}[a-z]?)\.\s",
    re.MULTILINE,
)

# Pattern B: Section with embedded clause in heading notation — "10(13A)"
_RE_SECTION_EMBEDDED_CLAUSE = re.compile(
    r"[Ss]ection\s+(\d{1,3}[A-Z]{0,4})\(([0-9A-Za-z]+[A-Z]?)\)",
)

# Pattern C: Inline reference "under section 80C" — used only for enrichment,
# not for the primary section_number of a chunk.
_RE_SECTION_REF = re.compile(
    r"[Ss]ection\s+(\d{1,3}[A-Z]{0,4}[a-z]?)",
)

# Subsection: "(1)", "(1A)", "(2B)", "(ia)", etc. at start of logical line.
_RE_SUBSECTION = re.compile(
    r"^\s*\(([0-9]{1,3}[A-Za-z]{0,3})\)\s",
    re.MULTILINE,
)

# Clause: "(a)", "(b)", "(ii)" etc. — subordinate to subsections.
_RE_CLAUSE = re.compile(
    r"^\s*\(([a-z]{1,3}|[ivx]{1,6})\)\s",
    re.MULTILINE,
)

# Known section registry — canonical section numbers that appear in the Act.
# Used to validate extracted section numbers and catch regex false positives.
KNOWN_SECTIONS = {
    # Part of common deductions covered by rules engine (from rules.json)
    "10", "10A", "10AA", "10B", "10C",
    "16", "17", "22", "23", "24",
    "28", "29", "30", "31", "32", "33", "35", "36", "37", "38",
    "40", "40A", "41", "43", "43A", "43B",
    "44", "44A", "44AB", "44AD", "44ADA", "44AE",
    "45", "46", "47", "48", "49", "50", "50A", "50B", "50C",
    "54", "54B", "54D", "54E", "54EA", "54EB", "54EC", "54EE", "54F", "54G", "54GA", "54H",
    "56", "57", "58", "59",
    "60", "61", "62", "63", "64",
    "68", "69", "69A", "69B", "69C", "69D",
    "70", "71", "72", "72A", "73", "74", "74A", "75",
    "80", "80A", "80B", "80C", "80CCA", "80CCB", "80CCC", "80CCD", "80CCE", "80CCF", "80CCG",
    "80D", "80DD", "80DDB", "80E", "80EE", "80EEA", "80EEB",
    "80G", "80GG", "80GGA", "80GGB", "80GGC",
    "80IA", "80IAB", "80IAC", "80IB", "80IBA", "80IC", "80ID", "80IE",
    "80JJA", "80JJAA", "80LA", "80P", "80PA", "80QQB", "80RRB",
    "80TTA", "80TTB", "80U",
    "87", "87A",
    "89", "90", "90A", "91",
    "111", "111A", "112", "112A", "115", "115A", "115B", "115BA", "115BAA", "115BAB",
    "115BAC", "115BAD", "115BAE", "115BB", "115BBA", "115BBB", "115BBC", "115BBD", "115BBDA",
    "115BBE", "115BBF", "115BBG", "115BBH", "115BBJ",
    "115JB", "115JC", "115JD", "115O", "115P", "115Q", "115R", "115S", "115T",
    "139", "139A", "139AA", "140", "140A", "142", "142A", "143", "144",
    "145", "145A", "145B",
    "148", "148A", "149", "150", "151",
    "153", "153A", "153B", "153C", "153D",
    "154", "155", "156", "158",
    "192", "192A", "193", "194", "194A", "194B", "194BA", "194BB",
    "194C", "194D", "194DA", "194E", "194EE", "194F", "194G", "194H",
    "194I", "194IA", "194IB", "194IC", "194J", "194K", "194LA",
    "194LB", "194LBA", "194LBB", "194LBC", "194LC", "194LD", "194LDA",
    "194M", "194N", "194O", "194P", "194Q", "194R", "194S",
    "195", "196", "196A", "196B", "196C", "196D",
    "197", "197A", "198", "199",
    "200", "200A", "201",
    "203", "203A", "204", "205", "206", "206A", "206AA", "206AB", "206B", "206C", "206CA", "206CB", "206CC", "206CCA", "206CD",
}


def extract_chapter(text: str) -> tuple[str, str]:
    """
    Returns (chapter_code, chapter_title) from the text block.
    Returns ("", "") if no chapter heading is found.

    chapter_code  : e.g. "VI-A", "XII", "I"
    chapter_title : The descriptive heading text following CHAPTER ...
    """
    match = _RE_CHAPTER.search(text)
    if not match:
        return ("", "")

    chapter_code = match.group(1).upper()

    # Attempt to extract title: take text on the same line after the match
    # or the next non-empty line (commonly all-caps in legislative PDFs).
    post_match = text[match.end():].lstrip()
    first_line = post_match.split("\n")[0].strip()
    if first_line and len(first_line) > 4:
        # Remove trailing punctuation artefacts
        chapter_title = re.sub(r"[\.\:\-]+$", "", first_line).strip()
    else:
        # Try the next non-blank line
        lines = [ln.strip() for ln in post_match.split("\n") if ln.strip()]
        chapter_title = lines[0] if lines else ""

    return (chapter_code, chapter_title)


def extract_section_number(text: str) -> str:
    """
    Extracts the primary section number from a chunk of text.

    Strategy (in order of priority):
      1. Line-start pattern: "80C. Deduction in respect of..."
      2. Embedded clause: "section 10(13A)"
      3. Inline reference: "under section 80D"
      4. Returns "" if nothing is detected.

    The extracted number is validated against KNOWN_SECTIONS.
    Numbers not in the registry are still returned but flagged in the log.
    """
    # Strategy 1: line-start section number
    match = _RE_SECTION_START.search(text)
    if match:
        candidate = match.group(1).upper()
        if candidate not in KNOWN_SECTIONS:
            logger.debug(f"Section '{candidate}' not in known registry — including anyway.")
        return candidate

    # Strategy 2: "section 10(13A)" style
    match = _RE_SECTION_EMBEDDED_CLAUSE.search(text)
    if match:
        base = match.group(1).upper()
        clause = match.group(2)
        return f"{base}({clause})"

    # Strategy 3: inline reference "section 80C"
    match = _RE_SECTION_REF.search(text)
    if match:
        candidate = match.group(1).upper()
        return candidate

    return ""


def extract_subsection(text: str) -> str:
    """
    Extracts the first subsection marker from the chunk text.
    Returns e.g. "(1)", "(2A)", "" if none found.
    """
    match = _RE_SUBSECTION.search(text)
    if match:
        return f"({match.group(1)})"
    return ""


def build_chunk_metadata(
    *,
    text: str,
    page_number: int,
    source_document: str,
    chunk_index: int,
    chapter_code: str = "",
    chapter_title: str = "",
    section_number: str = "",
    subsection: str = "",
) -> dict:
    """
    Assembles the canonical metadata dict for a single chunk.
    All fields that are guaranteed by the Sprint 1 spec are present.

    Fields:
        section_number   : e.g. "80C"
        chapter          : e.g. "VI-A"
        chapter_title    : e.g. "Deductions to be Made in Computing Total Income"
        subsection       : e.g. "(1)"
        page_number      : int
        source_document  : filename of the PDF
        chunk_index      : 0-based sequential index
        text             : the chunk content

    If section/chapter/subsection are not provided, they are extracted
    from the text automatically.
    """
    # Auto-extract if not explicitly provided
    if not chapter_code:
        chapter_code, chapter_title = extract_chapter(text)
    if not section_number:
        section_number = extract_section_number(text)
    if not subsection:
        subsection = extract_subsection(text)

    return {
        "section_number": section_number,
        "chapter": chapter_code,
        "chapter_title": chapter_title,
        "subsection": subsection,
        "page_number": page_number,
        "source_document": source_document,
        "chunk_index": chunk_index,
        "text": text,
    }


def validate_metadata(meta: dict) -> tuple[bool, list[str]]:
    """
    Validates a metadata dict for completeness.
    Returns (is_valid, list_of_warnings).
    A chunk is considered valid even with warnings — warnings are for logging.
    """
    warnings = []
    if not meta.get("text", "").strip():
        warnings.append("Empty text field")
    if not meta.get("section_number"):
        warnings.append("section_number not detected")
    if not meta.get("chapter"):
        warnings.append("chapter not detected")
    if meta.get("page_number", 0) <= 0:
        warnings.append("page_number is 0 or missing")
    if not meta.get("source_document"):
        warnings.append("source_document not set")

    is_valid = len(warnings) == 0
    return (is_valid, warnings)
