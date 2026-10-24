import re
from typing import Dict, Any, Tuple

class TaxAuthorityResolver:
    """
    Deterministic Authority Hierarchy Omega(Ca, Cb) for statutory tax text.
    Determines which passage is the legally authoritative winner when a
    contradiction is detected by the NLI cross-encoder gate.
    """

    @staticmethod
    def resolve_winner(
        chunk_a_id: int,
        chunk_a_text: str,
        chunk_a_meta: Dict[str, Any],
        chunk_b_id: int,
        chunk_b_text: str,
        chunk_b_meta: Dict[str, Any]
    ) -> Tuple[int, str]:
        """
        Applies statutory authority heuristics:
        1. Explicit amendment year / effective date precedence.
        2. Non-obstante & Proviso dominance ('Provided that', 'Notwithstanding...').
        3. Specific section proviso over general clause.
        4. Ingestion / chapter hierarchy fallback.
        """
        # 1. Check for amendment years in text
        years_a = [int(y) for y in re.findall(r'\b(20[0-2][0-9])\b', chunk_a_text)]
        years_b = [int(y) for y in re.findall(r'\b(20[0-2][0-9])\b', chunk_b_text)]
        
        max_year_a = max(years_a) if years_a else 0
        max_year_b = max(years_b) if years_b else 0

        if max_year_a > max_year_b and max_year_a >= 2020:
            return chunk_a_id, f"Temporal Recency: Chunk {chunk_a_id} contains later amendment year ({max_year_a} > {max_year_b})"
        elif max_year_b > max_year_a and max_year_b >= 2020:
            return chunk_b_id, f"Temporal Recency: Chunk {chunk_b_id} contains later amendment year ({max_year_b} > {max_year_a})"

        # 2. Check for Provisos / Override keywords
        override_keywords = [
            "notwithstanding anything contained",
            "provided that",
            "provided further that",
            "provided also that",
            "inserted by",
            "substituted by"
        ]
        
        score_a = sum(1 for kw in override_keywords if kw in chunk_a_text.lower())
        score_b = sum(1 for kw in override_keywords if kw in chunk_b_text.lower())

        if score_a > score_b:
            return chunk_a_id, f"Statutory Proviso Dominance: Chunk {chunk_a_id} acts as a specific proviso/override"
        elif score_b > score_a:
            return chunk_b_id, f"Statutory Proviso Dominance: Chunk {chunk_b_id} acts as a specific proviso/override"

        # 3. Special Regime (Section 115BAC) Dominance
        if "115BAC" in str(chunk_a_meta.get("section_number", "")):
            return chunk_a_id, f"Regime Override: Section 115BAC (New Regime) explicitly governs"
        if "115BAC" in str(chunk_b_meta.get("section_number", "")):
            return chunk_b_id, f"Regime Override: Section 115BAC (New Regime) explicitly governs"

        # 4. Fallback: Later chunk index represents newer scheduled amendment
        if chunk_a_id > chunk_b_id:
            return chunk_a_id, f"Corpus Precedence: Chunk {chunk_a_id} supersedes earlier provision {chunk_b_id}"
        else:
            return chunk_b_id, f"Corpus Precedence: Chunk {chunk_b_id} supersedes earlier provision {chunk_a_id}"

authority_resolver = TaxAuthorityResolver()
