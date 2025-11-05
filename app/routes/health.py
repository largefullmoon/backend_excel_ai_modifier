"""
Health check and status routes
"""

from fastapi import APIRouter
from ..models.schemas import APIResponse, OpenAIStatusResponse
from ..services.openai_service import OpenAIService
from ..core.config import SAMPLE_RULES

router = APIRouter()


@router.get("/", response_model=APIResponse)
async def root():
    """Health check endpoint"""
    return APIResponse(
        status="success",
        message="Excel AI Modifier API is running"
    )


@router.get("/sample-data")
async def get_sample_data():
    """
    Returns the JSON rules for enrichment
    """
    return SAMPLE_RULES


@router.get("/openai-status", response_model=OpenAIStatusResponse)
async def get_openai_status():
    """
    Check OpenAI configuration and API connectivity
    """
    result = OpenAIService.test_connection()
    return OpenAIStatusResponse(**result)
