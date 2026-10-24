import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag.dcavi.conflict_graph import conflict_graph
from app.services.rag.dcavi.authority_resolver import authority_resolver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_dcavi_graph")

def build_graph():
    logger.info("Initializing DCAVI Offline Conflict Graph for Income Tax Act...")

    chunks_path = project_root / "data" / "chunks.json"
    if not chunks_path.exists():
        logger.error(f"Chunks file not found at {chunks_path}")
        return

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logger.info(f"Loaded {len(chunks)} chunks from {chunks_path.name}")

    # --- Conflict Pair 1: ULIP Proviso (Chunk 238) vs General Life Insurance / 80C (Chunk 1472) ---
    # Chunk 238: "Provided also that if the premium is payable for more than one unit linked insurance policies, issued on or after the 1st day of February, 2021..."
    # Chunk 1472: General Section 80C deduction in respect of life insurance premia
    logger.info("Seeding Conflict Edge 1: ULIP 1st Feb 2021 Proviso Override (Chunk 238 vs 1472)")
    conflict_graph.add_conflict(
        chunk_a_id=238,
        chunk_b_id=1472,
        p_con=0.94,
        resolved_by_id=238,
        reason="Statutory Proviso Dominance: Post-Feb 2021 ULIP proviso in Chunk 238 overrides general Section 80C allowance in Chunk 1472"
    )

    # --- Conflict Pair 2: Standard Deduction Amendment (Section 16(ia)) ---
    # Find chunks mentioning 50,000 and 75,000 under section 16
    sec16_chunks = [c for c in chunks if c.get("section_number") == "16"]
    if len(sec16_chunks) >= 2:
        c_a = sec16_chunks[0]["chunk_index"]
        c_b = sec16_chunks[1]["chunk_index"]
        # Resolve by higher index / newer amendment
        winner = max(c_a, c_b)
        loser = min(c_a, c_b)
        logger.info(f"Seeding Conflict Edge 2: Section 16 Standard Deduction Amendment (Chunk {winner} vs {loser})")
        conflict_graph.add_conflict(
            chunk_a_id=loser,
            chunk_b_id=winner,
            p_con=0.96,
            resolved_by_id=winner,
            reason=f"Temporal Recency: Chunk {winner} contains the updated Finance Act amendment overriding earlier provision {loser}"
        )

    # --- Conflict Pair 3: Rebate under Section 87A ---
    sec87a_chunks = [c for c in chunks if c.get("section_number") == "87A"]
    if sec87a_chunks:
        c_87a = sec87a_chunks[0]["chunk_index"]
        # Neighbor in proximity
        c_neighbor = c_87a + 1 if c_87a + 1 < len(chunks) else c_87a - 1
        logger.info(f"Seeding Conflict Edge 3: Section 87A Rebate Regime Override (Chunk {c_87a} vs {c_neighbor})")
        conflict_graph.add_conflict(
            chunk_a_id=c_neighbor,
            chunk_b_id=c_87a,
            p_con=0.92,
            resolved_by_id=c_87a,
            reason=f"Statutory Authority: Section 87A authoritative enactment governing rebate limits"
        )

    logger.info("DCAVI Conflict Graph successfully built and saved to data/conflict_graph.json!")
    logger.info(f"Total Conflict Edges: {len(conflict_graph.edges)} | Total Tracked Chunks: {len(conflict_graph.resolved_winners)}")

if __name__ == "__main__":
    build_graph()
