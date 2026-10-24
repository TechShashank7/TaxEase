"""
DCAVI (Dynamic Contradiction-Aware Vector Indexing) Package
Implementation of the DCAVI architecture for eliminating contradiction-induced hallucinations in RAG.
Based on Verma et al., 2026.
"""

from .models import (
    NLIRelation,
    DCAVIStatus,
    NLIResult,
    ConflictEdge,
    DCAVIRankedChunk,
    DCAVIEvaluationResult
)
from .nli_gate import NLICrossEncoderGate, nli_gate
from .authority_resolver import TaxAuthorityResolver, authority_resolver
from .conflict_graph import ConflictGraph, conflict_graph
from .dcavi_retriever import DCAVIRetriever, dcavi_retriever
