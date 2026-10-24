import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    RagQueryRequest,
    RagQueryResponse,
    RagStatusResponse,
    RetrievedChunk
)
from app.services.rag.retrieval import retrieval_service
from app.services.rag.dcavi.dcavi_retriever import dcavi_retriever
from app.services.rag.dcavi.conflict_graph import conflict_graph
from app.services.rag.dcavi.evaluator import dcavi_evaluator
from app.services.rag.dcavi.models import DCAVIEvaluationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG & DCAVI"])

@router.post(
    "/retrieve",
    response_model=RagQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relevant Income Tax Act chunks with optional DCAVI dynamic scoring"
)
async def retrieve_chunks(request: RagQueryRequest):
    """
    Performs semantic vector search against the Income Tax Act chunks
    with optional DCAVI dynamic scoring to mathematically suppress contradictory passages.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    start_time = time.time()
    try:
        verified_chunks, suppressed_chunks = retrieval_service.retrieve_context_with_suppressed(
            query=request.query,
            top_k=request.top_k,
            section_filter=request.section_filter,
            min_score=request.min_score,
            use_dcavi=request.use_dcavi
        )
        elapsed_ms = (time.time() - start_time) * 1000

        return RagQueryResponse(
            query=request.query,
            chunks=verified_chunks,
            count=len(verified_chunks),
            retrieval_time_ms=round(elapsed_ms, 2),
            fallback_used=len(verified_chunks) == 0,
            dcavi_enabled=request.use_dcavi,
            suppressed_count=len(suppressed_chunks),
            suppressed_chunks=suppressed_chunks
        )
    except Exception as e:
        logger.error(f"Error executing RAG retrieval: {e}", exc_info=True)
        elapsed_ms = (time.time() - start_time) * 1000
        return RagQueryResponse(
            query=request.query,
            chunks=[],
            count=0,
            retrieval_time_ms=round(elapsed_ms, 2),
            fallback_used=True,
            dcavi_enabled=request.use_dcavi,
            suppressed_count=0,
            suppressed_chunks=[]
        )

@router.post(
    "/dcavi/evaluate",
    response_model=DCAVIEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Run Baseline RAG vs DCAVI RAG comparative evaluation"
)
async def evaluate_dcavi(request: RagQueryRequest):
    """
    Runs both Baseline RAG (naive top-k) and DCAVI RAG (P_con penalty scoring) side-by-side
    on the provided query, reporting Context Precision, Hallucination status, and score traces.
    Replicates Section 4 and Table 2/3 of Verma et al., 2026.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Fetch 2k raw candidates from Qdrant without penalty
    query_vector = retrieval_service._embed_query(request.query)
    res = retrieval_service.qdrant.query_points(
        collection_name=retrieval_service.collection_name,
        query=query_vector,
        limit=max(request.top_k * 2, 6)
    )

    raw_candidates = []
    for p in res.points:
        raw_candidates.append({
            "id": p.id,
            "text": p.payload.get("text", "") if p.payload else "",
            "metadata": p.payload or {},
            "score": float(p.score)
        })

    eval_result = dcavi_evaluator.evaluate_query(
        query=request.query,
        raw_candidates=raw_candidates,
        top_k=request.top_k
    )
    return eval_result

@router.get(
    "/dcavi/conflicts",
    summary="Get all active Conflict Edges in the DCAVI Conflict Graph"
)
async def get_active_conflicts():
    """
    Returns the list of all conflict edges, contradiction probabilities,
    and authoritative resolution reasons currently indexed.
    """
    return {
        "total_edges": len(conflict_graph.edges),
        "total_conflicted_chunks": len(conflict_graph.resolved_winners),
        "edges": [edge.model_dump() for edge in conflict_graph.edges.values()]
    }

@router.get(
    "/status",
    response_model=RagStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check RAG and Vector DB status"
)
async def get_rag_status():
    """
    Returns current health status and point counts for the Income Tax Act vector collection.
    """
    status_dict = retrieval_service.get_status()
    return RagStatusResponse(
        collection_name=status_dict["collection_name"],
        points_count=status_dict["points_count"],
        vector_dimension=status_dict["vector_dimension"],
        status=status_dict["status"],
        rag_enabled=status_dict["rag_enabled"]
    )

@router.get(
    "/sections",
    response_model=List[RetrievedChunk],
    status_code=status.HTTP_200_OK,
    summary="Retrieve chunks for specific section IDs"
)
async def get_sections(
    section: List[str] = Query(..., description="One or more section numbers, e.g. 80C, 80D"),
    top_k: int = Query(5, ge=1, le=20)
):
    """
    Directly retrieves chunks corresponding to specified section IDs.
    """
    return retrieval_service.retrieve_for_sections(section_ids=section, top_k=top_k)
