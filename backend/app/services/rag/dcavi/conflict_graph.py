import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .models import ConflictEdge

logger = logging.getLogger(__name__)

class ConflictGraph:
    """
    Lightweight Metadata Conflict Graph (E_conf).
    Maintains bidirectional conflict edges between contradictory chunks
    and authority resolutions (resolved_by_id).
    """
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent.parent.parent / "data" / "conflict_graph.json"
        self.edges: Dict[str, ConflictEdge] = {}
        self.chunk_conflicts: Dict[int, List[ConflictEdge]] = {}
        self.resolved_winners: Dict[int, int] = {}
        self._load()

    def add_conflict(
        self,
        chunk_a_id: int,
        chunk_b_id: int,
        p_con: float,
        resolved_by_id: int,
        reason: str
    ) -> ConflictEdge:
        """
        Creates a bidirectional conflict edge and updates resolved_by_id records.
        """
        edge_id = f"conf_{min(chunk_a_id, chunk_b_id)}_{max(chunk_a_id, chunk_b_id)}"
        edge = ConflictEdge(
            edge_id=edge_id,
            chunk_a_id=chunk_a_id,
            chunk_b_id=chunk_b_id,
            p_con=p_con,
            resolved_by_id=resolved_by_id,
            resolution_reason=reason
        )

        self.edges[edge_id] = edge

        # Index by chunk ID
        for cid in (chunk_a_id, chunk_b_id):
            if cid not in self.chunk_conflicts:
                self.chunk_conflicts[cid] = []
            self.chunk_conflicts[cid].append(edge)
            self.resolved_winners[cid] = resolved_by_id

        self._save()
        logger.info(f"DCAVI Conflict Edge created: {edge_id} | Winner: Chunk {resolved_by_id}")
        return edge

    def has_conflict(self, chunk_id: int) -> bool:
        """Returns True if chunk is involved in any detected contradiction."""
        return chunk_id in self.chunk_conflicts

    def get_resolved_winner(self, chunk_id: int) -> Optional[int]:
        """Returns the winning authoritative chunk ID if chunk has a conflict."""
        return self.resolved_winners.get(chunk_id)

    def get_edges_for_chunk(self, chunk_id: int) -> List[ConflictEdge]:
        """Returns all conflict edges associated with a given chunk ID."""
        return self.chunk_conflicts.get(chunk_id, [])

    def _save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "edges": {k: v.model_dump() for k, v in self.edges.items()},
                "resolved_winners": self.resolved_winners
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist conflict graph: {e}")

    def _load(self):
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.get("edges", {}).items():
                    edge = ConflictEdge(**v)
                    self.edges[k] = edge
                    for cid in (edge.chunk_a_id, edge.chunk_b_id):
                        if cid not in self.chunk_conflicts:
                            self.chunk_conflicts[cid] = []
                        self.chunk_conflicts[cid].append(edge)
                self.resolved_winners = {int(k): int(v) for k, v in data.get("resolved_winners", {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load conflict graph: {e}")

conflict_graph = ConflictGraph()
