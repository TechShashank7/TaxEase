from fastapi import APIRouter
from app.models.schemas import UserProfile, EligibilityResponse
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.database import db_service

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])
engine = EligibilityEngine()

@router.post("/evaluate", response_model=EligibilityResponse)
async def evaluate_profile(profile: UserProfile):
    """
    Evaluates a user profile against the Rules Engine and returns tax saving recommendations.
    Saves the profile and results to MongoDB.
    """
    response = engine.evaluate(profile)
    
    # Save to MongoDB
    db_service.save_analysis(
        profile_data=profile.model_dump(), 
        result_data=response.model_dump()
    )
    
    return response
