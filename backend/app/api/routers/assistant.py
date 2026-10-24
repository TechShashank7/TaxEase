from fastapi import APIRouter
from app.models.schemas import AiExplanationRequest, AiExplanationResponse, AiChatRequest, AiChatResponse
from app.services.ai_assistant.gemini import gemini_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.post("/explain", response_model=AiExplanationResponse)
async def explain_recommendations(req: AiExplanationRequest):
    """
    Generates a personalized AI explanation for the rules engine's output.
    """
    recs = [r.model_dump() for r in req.recommendations]
    explanation, citations = gemini_service.generate_explanation(
        name=req.name,
        recommendations=recs,
        total_benefit=req.total_benefit
    )
    return AiExplanationResponse(explanation=explanation, citations=citations)

@router.post("/chat", response_model=AiChatResponse)
async def chat_with_assistant(req: AiChatRequest):
    """
    Interactive Q&A chat with the Gemini assistant grounded in the Income Tax Act.
    """
    reply, citations = gemini_service.chat(message=req.message, context=req.context)
    return AiChatResponse(reply=reply, citations=citations)
