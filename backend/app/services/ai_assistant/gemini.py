import re
import logging
from typing import List, Tuple, Optional

try:
    from google import genai
except ImportError:
    genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

from app.core.config import settings
from app.models.schemas import Citation
from app.services.rag.retrieval import retrieval_service
from app.services.rag.citation_builder import CitationBuilder

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.client = None
        self.legacy_model = None
        self.model_name = "gemini-2.5-flash"

        if settings.GEMINI_API_KEY:
            if genai:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            elif legacy_genai:
                legacy_genai.configure(api_key=settings.GEMINI_API_KEY)
                self.legacy_model = legacy_genai.GenerativeModel(self.model_name)

    def _generate_text(self, prompt: str) -> str:
        """Helper to invoke Gemini text generation using available SDK."""
        if self.client:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        elif self.legacy_model:
            response = self.legacy_model.generate_content(prompt)
            return response.text
        else:
            return "Gemini API key not configured. I am operating in offline fallback mode."

    def generate_explanation(
        self,
        name: str,
        recommendations: list,
        total_benefit: float
    ) -> Tuple[str, List[Citation]]:
        """
        Generates an AI summary for the rules engine output, grounded in statutory provisions.
        """
        if not (self.client or self.legacy_model):
            return (
                "Gemini API key not configured. The rules engine identified tax savings for you.",
                []
            )

        try:
            # 1. Identify section references from recommendations
            section_matches = set()
            for r in recommendations:
                ref_list = r.get("references", [])
                for ref in ref_list:
                    found = re.findall(r"Section\s+([0-9]+[A-Za-z0-9\(\)]*)", ref, re.IGNORECASE)
                    section_matches.update(found)
                rule_text = r.get("triggered_rule", "") + " " + r.get("scheme_name", "")
                found = re.findall(r"\b(80[A-Z0-9]+|24b?|10\(13A\))\b", rule_text)
                section_matches.update(found)

            # 2. Retrieve statutory context
            retrieved_chunks = []
            if section_matches:
                retrieved_chunks = retrieval_service.retrieve_for_sections(
                    section_ids=list(section_matches),
                    top_k=4
                )

            # Fallback to semantic query if direct section lookup returned nothing
            if not retrieved_chunks and recommendations:
                query_str = " ".join([r.get("scheme_name", "") for r in recommendations[:3]])
                retrieved_chunks = retrieval_service.retrieve_context(query=query_str, top_k=3)

            statutory_context = CitationBuilder.format_context_for_prompt(retrieved_chunks)
            citations = CitationBuilder.build_citations(retrieved_chunks)

            # 3. Format recommendations summary
            schemes = [
                f"- {r.get('scheme_name')}: {r.get('recommendation')} (Potential Benefit: ₹{r.get('potential_tax_benefit')})"
                for r in recommendations
            ]
            schemes_text = "\n".join(schemes)

            context_block = f"\n{statutory_context}\n" if statutory_context else ""

            prompt = f"""
You are TaxEase, a friendly and expert Indian tax assistant.
You are speaking to {name}.

The deterministic rules engine just computed that they can save ₹{total_benefit} in taxes under the Income Tax Act.
Here are the specific actions recommended:
{schemes_text}
{context_block}
Write a short, encouraging message explaining these findings.
Do not hallucinate numbers. Summarize the overall strategy, emphasize the biggest opportunity, and reference the governing IT Act provisions where applicable.
Keep it conversational, under 3 paragraphs.
IMPORTANT: Output plain text only. Do NOT use markdown asterisks (*, **) or bold formatting.
"""
            explanation = self._generate_text(prompt)
            return explanation, citations

        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            return f"Error connecting to Gemini: {str(e)}", []

    def chat(self, message: str, context: str) -> Tuple[str, List[Citation]]:
        """
        Interactive Q&A chat grounded in the Income Tax Act via Qdrant RAG.
        """
        if not (self.client or self.legacy_model):
            return "Gemini API key not configured. I am the fallback offline assistant.", []

        try:
            # 1. Retrieve statutory chunks via semantic search
            retrieved_chunks = retrieval_service.retrieve_context(query=message, top_k=settings.RAG_TOP_K)
            statutory_context = CitationBuilder.format_context_for_prompt(retrieved_chunks)
            citations = CitationBuilder.build_citations(retrieved_chunks)

            context_block = f"\n{statutory_context}\n" if statutory_context else ""

            prompt = f"""
You are TaxEase, an expert Indian tax intelligence assistant grounded in the official Income Tax Act, 1961.

User Profile Context:
{context}
{context_block}
User Query: {message}

Instructions:
- Provide an accurate, helpful, and concise answer based on the Income Tax Act provisions and statutory context provided above.
- Specifically mention relevant section numbers (e.g. Section 80C, Section 80D, Section 24(b)) and their eligibility conditions when relevant.
- Do not give generic or unauthorized financial advice.
- IMPORTANT: Output plain text only. Do NOT use markdown formatting, asterisks, or bold tags.
"""
            reply = self._generate_text(prompt)
            return reply, citations

        except Exception as e:
            logger.error(f"Error during AI chat: {e}", exc_info=True)
            return f"Error connecting to Gemini: {str(e)}", []

gemini_service = GeminiService()
