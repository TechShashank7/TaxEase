import re
import logging
from typing import List, Optional
from app.models.schemas import Citation, RetrievedChunk

logger = logging.getLogger(__name__)

class CitationBuilder:
    @staticmethod
    def build_citations(chunks: List[RetrievedChunk], max_citations: int = 4) -> List[Citation]:
        """
        Builds structured, deduplicated Citation models from retrieved chunks.
        """
        citations: List[Citation] = []
        seen = set()

        for chunk in chunks:
            sec = chunk.metadata.section_number or "General"
            page = chunk.metadata.page_number
            key = (sec, page)

            if key in seen:
                continue
            seen.add(key)

            # Clean excerpt
            excerpt = re.sub(r'\s+', ' ', chunk.text).strip()
            if len(excerpt) > 180:
                excerpt = excerpt[:177] + "..."

            citation = Citation(
                section_number=chunk.metadata.section_number,
                chapter=chunk.metadata.chapter,
                chapter_title=chunk.metadata.chapter_title,
                page_number=chunk.metadata.page_number,
                source_document=chunk.metadata.source_document or "Income Tax Act, 1961",
                excerpt=excerpt,
                relevance_score=round(float(chunk.score), 3),
                dcavi_status=chunk.dcavi_status,
                conflict_reason=chunk.conflict_reason
            )
            citations.append(citation)

            if len(citations) >= max_citations:
                break

        return citations

    @staticmethod
    def format_context_for_prompt(chunks: List[RetrievedChunk]) -> str:
        """
        Formats retrieved chunks into a clear, referenced statutory context block for Gemini.
        """
        if not chunks:
            return ""

        context_lines = ["STATUTORY CONTEXT FROM THE INCOME TAX ACT, 1961:"]
        for idx, chunk in enumerate(chunks, 1):
            sec = f"Section {chunk.metadata.section_number}" if chunk.metadata.section_number else "Provisions"
            chap = f", Chapter {chunk.metadata.chapter}" if chunk.metadata.chapter else ""
            page = f", Page {chunk.metadata.page_number}" if chunk.metadata.page_number else ""
            
            clean_text = re.sub(r'\s+', ' ', chunk.text).strip()
            context_lines.append(f"[{idx}] {sec}{chap}{page}:\n\"{clean_text}\"")

        return "\n\n".join(context_lines)
