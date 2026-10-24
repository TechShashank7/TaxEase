import re
import json
import logging
from typing import Dict, Any, Optional, Tuple
from .models import NLIRelation, NLIResult

try:
    from google import genai
except ImportError:
    genai = None

from app.core.config import settings

logger = logging.getLogger(__name__)

class NLICrossEncoderGate:
    """
    Ingestion-time & query-time Cross-Encoder NLI Gate (M_NLI).
    Evaluates pairs of passages to compute [P_ent, P_neu, P_con].
    """
    def __init__(self, tau: float = 0.85):
        self.tau = tau  # Contradiction threshold (default 0.85 from paper Section 3.2)
        self.client = None
        self._cache: Dict[Tuple[int, int], NLIResult] = {}

        if settings.GEMINI_API_KEY and genai:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def evaluate_pair(
        self,
        chunk_a_id: int,
        chunk_a_text: str,
        chunk_b_id: int,
        chunk_b_text: str
    ) -> NLIResult:
        """
        Evaluates the logical relationship between Chunk A (Premise) and Chunk B (Hypothesis).
        Returns NLIResult with P_con, P_ent, P_neu.
        """
        pair_key = (min(chunk_a_id, chunk_b_id), max(chunk_a_id, chunk_b_id))
        if pair_key in self._cache:
            return self._cache[pair_key]

        # 1. Fast deterministic heuristic check for obvious statutory contradictions
        fast_result = self._check_statutory_contradiction_heuristics(chunk_a_text, chunk_b_text)
        if fast_result:
            self._cache[pair_key] = fast_result
            return fast_result

        # 2. Cross-Encoder NLI model evaluation via Gemini
        if self.client:
            try:
                prompt = f"""
You are an expert Natural Language Inference (NLI) Cross-Encoder evaluator analyzing statutory provisions from the Income Tax Act.

Premise [Chunk {chunk_a_id}]:
"{chunk_a_text[:800]}"

Hypothesis [Chunk {chunk_b_id}]:
"{chunk_b_text[:800]}"

Task:
Determine whether the Premise and Hypothesis logically Contradict each other, Entail each other, or are Neutral.
A Contradiction occurs when both passages cannot simultaneously hold true for the same taxpayer scenario (e.g. differing deduction limits for the same section, one passage allowing a deduction while the other disallows it, or conflicting tax rates).

Respond ONLY with a valid JSON object in this exact schema:
{{
  "relation": "Contradiction" | "Entailment" | "Neutral",
  "p_con": <float between 0.0 and 1.0>,
  "p_ent": <float between 0.0 and 1.0>,
  "p_neu": <float between 0.0 and 1.0>,
  "explanation": "<brief rationale>"
}}
"""
                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                raw_text = resp.text.strip()
                # Clean json fences if present
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)

                data = json.loads(raw_text)
                result = NLIResult(
                    relation=NLIRelation(data["relation"]),
                    p_con=float(data["p_con"]),
                    p_ent=float(data.get("p_ent", 0.0)),
                    p_neu=float(data.get("p_neu", 0.0)),
                    explanation=data.get("explanation", "")
                )
                self._cache[pair_key] = result
                return result
            except Exception as e:
                logger.warning(f"NLI evaluation fallback for ({chunk_a_id}, {chunk_b_id}): {e}")

        # Default Neutral fallback
        fallback = NLIResult(
            relation=NLIRelation.NEUTRAL,
            p_con=0.0,
            p_ent=0.0,
            p_neu=1.0,
            explanation="Default neutral comparison"
        )
        self._cache[pair_key] = fallback
        return fallback

    def _check_statutory_contradiction_heuristics(self, text_a: str, text_b: str) -> Optional[NLIResult]:
        """
        Fast heuristic scan for mutually exclusive numerical caps or explicit allowance/disallowance.
        """
        lower_a = text_a.lower()
        lower_b = text_b.lower()

        # Check for standard deduction conflict (50,000 vs 75,000)
        has_50k = "50,000" in text_a or "fifty thousand" in lower_a
        has_75k = "75,000" in text_b or "seventy-five thousand" in lower_b
        has_std = "standard deduction" in lower_a or "standard deduction" in lower_b
        if has_std and ((has_50k and ("75,000" in text_b or "seventy-five" in lower_b)) or 
                        (has_75k and ("50,000" in text_a or "fifty thousand" in lower_a))):
            return NLIResult(
                relation=NLIRelation.CONTRADICTION,
                p_con=0.98,
                p_ent=0.0,
                p_neu=0.02,
                explanation="Contradictory standard deduction amounts (₹50,000 pre-amendment vs ₹75,000 post-amendment)."
            )

        # Check for Chapter VI-A allowance vs Section 115BAC disallowance
        disallow_a = "no deduction shall be allowed" in lower_a or "without any deduction" in lower_a
        disallow_b = "no deduction shall be allowed" in lower_b or "without any deduction" in lower_b
        allow_a = "shall be allowed as a deduction" in lower_a or "deduction in respect of" in lower_a
        allow_b = "shall be allowed as a deduction" in lower_b or "deduction in respect of" in lower_b

        if (disallow_a and allow_b) or (disallow_b and allow_a):
            # Check if both refer to same section or Chapter VI-A
            if ("chapter vi-a" in lower_a and "chapter vi-a" in lower_b) or ("80c" in lower_a and "80c" in lower_b):
                return NLIResult(
                    relation=NLIRelation.CONTRADICTION,
                    p_con=0.95,
                    p_ent=0.0,
                    p_neu=0.05,
                    explanation="Mutually exclusive allowance vs statutory disallowance under special regime."
                )

        return None

nli_gate = NLICrossEncoderGate()
