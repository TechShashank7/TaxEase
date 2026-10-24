import logging
from typing import List, Tuple, Dict, Any, Optional
from .models import DCAVIStatus, DCAVIRankedChunk, ConflictEdge
from .conflict_graph import conflict_graph
from .nli_gate import nli_gate
from .authority_resolver import authority_resolver

logger = logging.getLogger(__name__)

class DCAVIRetriever:
    """
    Search-Time Dynamic Scoring and Suppression (Section 3.3).
    Intercepts candidate scores from base vector search, applies P_con penalty
    to superseded contradictory chunks, and guarantees Invariant 1 (No-Stale-Context).
    """
    def __init__(self, p_penalty: float = 1000.0, contradiction_threshold: float = 0.85):
        self.p_penalty = p_penalty
        self.tau = contradiction_threshold

    def process_candidates(
        self,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        pairwise_nli_check: bool = False
    ) -> Tuple[List[DCAVIRankedChunk], List[DCAVIRankedChunk]]:
        """
        Applies DCAVI dynamic scoring to raw candidate chunks.
        candidates: list of dicts with 'id', 'text', 'metadata', 'score'.
        Returns: (verified_top_k_chunks, suppressed_chunks)
        """
        if not candidates:
            return [], []

        # 1. Dynamic Ingestion/Preemptive Gate: Check candidates against each other for newly surfaced conflicts
        if pairwise_nli_check and len(candidates) > 1:
            self._evaluate_candidate_pairs(candidates)

        ranked_results: List[DCAVIRankedChunk] = []
        suppressed_results: List[DCAVIRankedChunk] = []

        for cand in candidates:
            chunk_id = cand.get("id") or cand.get("metadata", {}).get("chunk_index", 0)
            raw_score = float(cand.get("score", 0.0))
            text = cand.get("text", "")
            meta = cand.get("metadata", {})

            has_conf = conflict_graph.has_conflict(chunk_id)
            resolved_winner = conflict_graph.get_resolved_winner(chunk_id)
            conflict_edge = conflict_graph.get_edges_for_chunk(chunk_id)[0] if has_conf else None

            # Formula 6 & 7 from Section 3.3 (adapted for Cosine Similarity):
            if has_conf:
                if chunk_id != resolved_winner:
                    # Chunk lost conflict resolution -> Apply P_con penalty
                    penalized_score = raw_score - self.p_penalty
                    status = DCAVIStatus.SUPPRESSED
                    applied_p = self.p_penalty
                else:
                    # Chunk won conflict resolution -> Verified Winner
                    penalized_score = raw_score
                    status = DCAVIStatus.VERIFIED
                    applied_p = 0.0
            else:
                # No conflict recorded -> Standard clean passage
                penalized_score = raw_score
                status = DCAVIStatus.NO_CONFLICT
                applied_p = 0.0

            ranked_chunk = DCAVIRankedChunk(
                chunk_id=chunk_id,
                text=text,
                metadata=meta,
                raw_score=raw_score,
                final_score=penalized_score,
                dcavi_status=status,
                conflict_edge=conflict_edge,
                applied_penalty=applied_p
            )

            if status == DCAVIStatus.SUPPRESSED:
                suppressed_results.append(ranked_chunk)

            ranked_results.append(ranked_chunk)

        # 2. Re-sort by final_score descending (for cosine similarity)
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)

        # 3. Theorem 1: Guaranteed contextual consistency - top-k exclusively contains non-suppressed chunks
        top_k_verified = [c for c in ranked_results if c.dcavi_status != DCAVIStatus.SUPPRESSED][:top_k]

        logger.info(
            f"DCAVI Dynamic Scoring: Evaluated {len(candidates)} candidates | "
            f"Selected {len(top_k_verified)} valid chunks | Suppressed {len(suppressed_results)} conflicting chunks."
        )

        return top_k_verified, suppressed_results

    def _evaluate_candidate_pairs(self, candidates: List[Dict[str, Any]]):
        """
        Evaluates pairs among top candidates that have high mutual similarity
        to detect Noun-Phrase Collisions and record conflict edges on the fly.
        """
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                cand_a = candidates[i]
                cand_b = candidates[j]
                id_a = cand_a.get("id") or cand_a.get("metadata", {}).get("chunk_index", 0)
                id_b = cand_b.get("id") or cand_b.get("metadata", {}).get("chunk_index", 0)

                # Skip if already in conflict graph
                if conflict_graph.has_conflict(id_a) and conflict_graph.has_conflict(id_b):
                    continue

                text_a = cand_a.get("text", "")
                text_b = cand_b.get("text", "")

                nli_res = nli_gate.evaluate_pair(id_a, text_a, id_b, text_b)
                if nli_res.p_con >= self.tau:
                    # Resolve winner using Authority Heuristics Omega(Ca, Cb)
                    winner_id, reason = authority_resolver.resolve_winner(
                        chunk_a_id=id_a,
                        chunk_a_text=text_a,
                        chunk_a_meta=cand_a.get("metadata", {}),
                        chunk_b_id=id_b,
                        chunk_b_text=text_b,
                        chunk_b_meta=cand_b.get("metadata", {})
                    )
                    conflict_graph.add_conflict(
                        chunk_a_id=id_a,
                        chunk_b_id=id_b,
                        p_con=nli_res.p_con,
                        resolved_by_id=winner_id,
                        reason=reason
                    )

dcavi_retriever = DCAVIRetriever()
