from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfile(BaseModel):
    name: str
    age: int
    annual_income: float
    tax_regime: str = Field(..., description="Either 'old' or 'new'")
    has_girl_child: bool = False
    is_metro_city: bool = False
    
    # Financial data
    basic_salary: float = 0.0
    rent_paid: float = 0.0
    hra_received: float = 0.0
    
    # Investments
    sec_80c_investments: float = 0.0
    health_insurance_premium: float = 0.0
    parents_age: int = 0
    parents_health_insurance_premium: float = 0.0
    nps_contribution: float = 0.0
    home_loan_interest: float = 0.0
    scss_investment: float = 0.0
    ssy_investment: float = 0.0

class Recommendation(BaseModel):
    scheme_id: str
    scheme_name: str
    category: str
    priority_score: int
    triggered_rule: str
    threshold_used: float
    current_investment: float
    gap_amount: float
    potential_tax_benefit: float
    recommendation: str
    explanation: str
    references: List[str]
    is_planning: bool = False

class EligibilityResponse(BaseModel):
    status: str
    recommendations: List[Recommendation]
    total_unclaimed_deductions: float
    total_potential_benefit: float
    high_priority_recommendation_count: int

class Citation(BaseModel):
    section_number: Optional[str] = None
    chapter: Optional[str] = None
    chapter_title: Optional[str] = None
    page_number: int
    source_document: str = "Income Tax Act, 1961"
    excerpt: str
    relevance_score: float = 0.0
    dcavi_status: Optional[str] = None
    conflict_reason: Optional[str] = None

class TaxChunkMetadata(BaseModel):
    section_number: Optional[str] = None
    chapter: Optional[str] = None
    chapter_title: Optional[str] = None
    subsection: Optional[str] = None
    page_number: int
    source_document: str
    chunk_index: int

class RetrievedChunk(BaseModel):
    id: Optional[int] = None
    text: str
    metadata: TaxChunkMetadata
    score: float
    dcavi_status: Optional[str] = "NO CONFLICT"
    raw_score: Optional[float] = None
    applied_penalty: Optional[float] = 0.0
    conflict_reason: Optional[str] = None

class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    section_filter: Optional[str] = None
    min_score: Optional[float] = None
    use_dcavi: bool = True

class RagQueryResponse(BaseModel):
    query: str
    chunks: List[RetrievedChunk]
    count: int
    retrieval_time_ms: float
    fallback_used: bool = False
    dcavi_enabled: bool = True
    suppressed_count: int = 0
    suppressed_chunks: Optional[List[RetrievedChunk]] = None

class RagStatusResponse(BaseModel):
    collection_name: str
    points_count: int
    vector_dimension: int
    status: str
    rag_enabled: bool

class AiExplanationRequest(BaseModel):
    name: str
    recommendations: List[Recommendation]
    total_benefit: float

class AiExplanationResponse(BaseModel):
    explanation: str
    citations: Optional[List[Citation]] = None

class AiChatRequest(BaseModel):
    message: str
    context: str

class AiChatResponse(BaseModel):
    reply: str
    citations: Optional[List[Citation]] = None
