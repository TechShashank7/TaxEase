from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NLIRelation(str, Enum):
    CONTRADICTION = "Contradiction"
    ENTAILMENT = "Entailment"
    NEUTRAL = "Neutral"

class DCAVIStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NO_CONFLICT = "NO CONFLICT"
    SUPPRESSED = "SUPPRESSED"

class NLIResult(BaseModel):
    relation: NLIRelation
    p_con: float = Field(..., description="Probability of contradiction [0.0, 1.0]")
    p_ent: float = Field(default=0.0, description="Probability of entailment [0.0, 1.0]")
    p_neu: float = Field(default=0.0, description="Probability of neutral relationship [0.0, 1.0]")
    explanation: str = Field(default="", description="Reasoning for the NLI classification")

class ConflictEdge(BaseModel):
    edge_id: str
    chunk_a_id: int
    chunk_b_id: int
    p_con: float
    resolved_by_id: int = Field(..., description="The authoritative/winning chunk ID")
    resolution_reason: str = Field(..., description="Deterministic authority heuristic reason")
    created_at: str = Field(default="2026-10-20", description="ISO timestamp")

class DCAVIRankedChunk(BaseModel):
    chunk_id: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_score: float
    final_score: float
    dcavi_status: DCAVIStatus
    conflict_edge: Optional[ConflictEdge] = None
    applied_penalty: float = 0.0

class DCAVIEvaluationResult(BaseModel):
    query: str
    baseline_top_k: List[Dict[str, Any]]
    dcavi_top_k: List[Dict[str, Any]]
    suppressed_chunks: List[Dict[str, Any]]
    baseline_has_hallucination: bool
    dcavi_has_hallucination: bool
    context_precision_baseline: float
    context_precision_dcavi: float
    token_savings_percent: float
    latency_baseline_s: float
    latency_dcavi_s: float
