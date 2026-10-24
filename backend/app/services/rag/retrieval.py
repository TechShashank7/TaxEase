import logging
import time
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

from app.core.config import settings
from app.models.schemas import TaxChunkMetadata, RetrievedChunk
from app.services.rag.dcavi.dcavi_retriever import dcavi_retriever

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.qdrant_url = settings.QDRANT_URL
        self.collection_name = settings.QDRANT_COLLECTION
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_dim = settings.EMBEDDING_DIMENSION
        
        try:
            self.qdrant = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=30.0
            )
        except Exception as e:
            logger.error(f"Failed to initialize QdrantClient: {e}")
            self.qdrant = None

        if genai:
            self.genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.use_new_sdk = True
        elif legacy_genai:
            legacy_genai.configure(api_key=settings.GEMINI_API_KEY)
            self.genai_client = None
            self.use_new_sdk = False
        else:
            self.genai_client = None
            self.use_new_sdk = False
            logger.warning("No Google GenAI SDK found.")

    def _embed_query(self, query: str) -> List[float]:
        """Embeds a single query string using RETRIEVAL_QUERY task type."""
        if self.use_new_sdk and self.genai_client:
            response = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=query,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.embedding_dim,
                    task_type="RETRIEVAL_QUERY"
                )
            )
            return response.embeddings[0].values
        elif legacy_genai:
            model_name = self.embedding_model if self.embedding_model.startswith("models/") else f"models/{self.embedding_model}"
            try:
                res = legacy_genai.embed_content(
                    model=model_name,
                    content=query,
                    task_type="retrieval_query",
                    output_dimensionality=self.embedding_dim
                )
            except TypeError:
                res = legacy_genai.embed_content(
                    model=model_name,
                    content=query,
                    task_type="retrieval_query"
                )
            return res['embedding']
        else:
            raise RuntimeError("Gemini SDK not initialized for query embedding.")

    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        section_filter: Optional[str] = None,
        min_score: Optional[float] = None,
        use_dcavi: bool = True
    ) -> List[RetrievedChunk]:
        """
        Retrieves top-k relevant chunks from Qdrant.
        When use_dcavi=True, enforces Dynamic Contradiction-Aware Vector Indexing
        to mathematically suppress invalidated/conflicting chunks (Section 3.3).
        """
        verified_chunks, _ = self.retrieve_context_with_suppressed(
            query=query,
            top_k=top_k,
            section_filter=section_filter,
            min_score=min_score,
            use_dcavi=use_dcavi
        )
        return verified_chunks

    def retrieve_context_with_suppressed(
        self,
        query: str,
        top_k: Optional[int] = None,
        section_filter: Optional[str] = None,
        min_score: Optional[float] = None,
        use_dcavi: bool = True
    ) -> Tuple[List[RetrievedChunk], List[RetrievedChunk]]:
        """
        Retrieves top-k chunks along with explicitly suppressed conflicting chunks.
        Returns: (verified_chunks, suppressed_chunks)
        """
        if not settings.RAG_ENABLED:
            logger.info("RAG is disabled via configuration. Returning empty context.")
            return [], []

        if not self.qdrant:
            logger.warning("Qdrant client not available. Fallback to empty context.")
            return [], []

        top_k = top_k or settings.RAG_TOP_K
        min_score = min_score if min_score is not None else settings.RAG_MIN_SCORE

        try:
            query_vector = self._embed_query(query)

            query_filter = None
            if section_filter:
                query_filter = rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="section_number",
                            match=rest.MatchValue(value=section_filter)
                        )
                    ]
                )

            # In DCAVI, fetch k' = max(2*top_k, 6) candidates to allow for dynamic suppression
            fetch_limit = max(top_k * 2, 6) if use_dcavi else top_k

            res = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=fetch_limit
            )

            raw_candidates = []
            for point in res.points:
                payload = point.payload or {}
                raw_candidates.append({
                    "id": point.id,
                    "text": payload.get("text", ""),
                    "metadata": payload,
                    "score": float(point.score)
                })

            if use_dcavi:
                top_ranked, suppressed = dcavi_retriever.process_candidates(raw_candidates, top_k=top_k)

                verified_chunks: List[RetrievedChunk] = []
                for rc in top_ranked:
                    if rc.raw_score < min_score:
                        continue
                    meta = TaxChunkMetadata(
                        section_number=rc.metadata.get("section_number"),
                        chapter=rc.metadata.get("chapter"),
                        chapter_title=rc.metadata.get("chapter_title"),
                        subsection=rc.metadata.get("subsection"),
                        page_number=rc.metadata.get("page_number", 1),
                        source_document=rc.metadata.get("source_document", "income_tax_act.pdf"),
                        chunk_index=rc.metadata.get("chunk_index", 0)
                    )
                    verified_chunks.append(RetrievedChunk(
                        id=rc.chunk_id,
                        text=rc.text,
                        metadata=meta,
                        score=float(rc.final_score),
                        raw_score=float(rc.raw_score),
                        dcavi_status=rc.dcavi_status.value,
                        applied_penalty=float(rc.applied_penalty),
                        conflict_reason=rc.conflict_edge.resolution_reason if rc.conflict_edge else None
                    ))

                suppressed_chunks: List[RetrievedChunk] = []
                for sc in suppressed:
                    meta = TaxChunkMetadata(
                        section_number=sc.metadata.get("section_number"),
                        chapter=sc.metadata.get("chapter"),
                        chapter_title=sc.metadata.get("chapter_title"),
                        subsection=sc.metadata.get("subsection"),
                        page_number=sc.metadata.get("page_number", 1),
                        source_document=sc.metadata.get("source_document", "income_tax_act.pdf"),
                        chunk_index=sc.metadata.get("chunk_index", 0)
                    )
                    suppressed_chunks.append(RetrievedChunk(
                        id=sc.chunk_id,
                        text=sc.text,
                        metadata=meta,
                        score=float(sc.final_score),
                        raw_score=float(sc.raw_score),
                        dcavi_status=sc.dcavi_status.value,
                        applied_penalty=float(sc.applied_penalty),
                        conflict_reason=sc.conflict_edge.resolution_reason if sc.conflict_edge else None
                    ))

                logger.info(f"DCAVI Retrieval: {len(verified_chunks)} verified chunks, {len(suppressed_chunks)} suppressed")
                return verified_chunks, suppressed_chunks

            else:
                # Baseline RAG without DCAVI
                retrieved_chunks: List[RetrievedChunk] = []
                for c in raw_candidates[:top_k]:
                    if c["score"] < min_score:
                        continue
                    payload = c["metadata"]
                    meta = TaxChunkMetadata(
                        section_number=payload.get("section_number"),
                        chapter=payload.get("chapter"),
                        chapter_title=payload.get("chapter_title"),
                        subsection=payload.get("subsection"),
                        page_number=payload.get("page_number", 1),
                        source_document=payload.get("source_document", "income_tax_act.pdf"),
                        chunk_index=payload.get("chunk_index", 0)
                    )
                    retrieved_chunks.append(RetrievedChunk(
                        id=c["id"],
                        text=c["text"],
                        metadata=meta,
                        score=float(c["score"]),
                        raw_score=float(c["score"]),
                        dcavi_status="NO CONFLICT"
                    ))
                return retrieved_chunks, []

        except Exception as e:
            logger.error(f"Error during context retrieval: {e}", exc_info=True)
            return [], []

    def retrieve_for_sections(
        self,
        section_ids: List[str],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """Retrieves chunks by matching specific section numbers directly."""
        if not settings.RAG_ENABLED or not self.qdrant or not section_ids:
            return []

        try:
            query_filter = rest.Filter(
                should=[
                    rest.FieldCondition(
                        key="section_number",
                        match=rest.MatchValue(value=sec_id)
                    )
                    for sec_id in section_ids
                ]
            )

            res, _ = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=top_k,
                with_payload=True
            )

            chunks: List[RetrievedChunk] = []
            for point in res:
                payload = point.payload or {}
                meta = TaxChunkMetadata(
                    section_number=payload.get("section_number"),
                    chapter=payload.get("chapter"),
                    chapter_title=payload.get("chapter_title"),
                    subsection=payload.get("subsection"),
                    page_number=payload.get("page_number", 1),
                    source_document=payload.get("source_document", "income_tax_act.pdf"),
                    chunk_index=payload.get("chunk_index", 0)
                )
                chunks.append(
                    RetrievedChunk(
                        id=point.id,
                        text=payload.get("text", ""),
                        metadata=meta,
                        score=1.0
                    )
                )

            return chunks
        except Exception as e:
            logger.error(f"Error retrieving sections {section_ids}: {e}", exc_info=True)
            return []

    def get_status(self) -> Dict[str, Any]:
        """Returns the status and point count of the vector store."""
        if not self.qdrant:
            return {
                "collection_name": self.collection_name,
                "points_count": 0,
                "vector_dimension": self.embedding_dim,
                "status": "disconnected",
                "rag_enabled": settings.RAG_ENABLED
            }

        try:
            info = self.qdrant.get_collection(self.collection_name)
            points_count = info.points_count or 0
            status_val = str(info.status) if hasattr(info, "status") else "green"
            return {
                "collection_name": self.collection_name,
                "points_count": points_count,
                "vector_dimension": self.embedding_dim,
                "status": status_val,
                "rag_enabled": settings.RAG_ENABLED
            }
        except Exception as e:
            logger.error(f"Error checking Qdrant status: {e}")
            return {
                "collection_name": self.collection_name,
                "points_count": 0,
                "vector_dimension": self.embedding_dim,
                "status": f"error: {str(e)}",
                "rag_enabled": settings.RAG_ENABLED
            }

retrieval_service = RetrievalService()
