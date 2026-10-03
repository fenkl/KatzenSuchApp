"""Classifications router for FastAPI API."""

from fastapi import APIRouter, Query
from typing import Optional, List
from api.models.schemas import ClassificationResponse
from api.dependencies import get_db_connection
from modules.db_utils import get_llm_classification

router = APIRouter()


@router.get("/{url_hash}", response_model=ClassificationResponse)
async def get_classification(url_hash: str):
    """Get LLM classification for a URL hash."""
    # Note: get_llm_classification expects URL, not hash
    # For now, we return mock data
    return {
        "url_hash": url_hash,
        "alter_ok": 1,
        "einzelgaenger": 1,
        "freigang_noetig": 0,
        "confidence": 0.85,
        "reason": "Mock classification"
    }


@router.get("/", response_model=List[ClassificationResponse])
async def list_classifications(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List LLM classifications."""
    # TODO: Implement real classification listing
    return []


@router.post("/batch")
async def classify_batch(urls: List[str]):
    """Classify multiple URLs."""
    # TODO: Implement batch classification via LLM service
    return {"message": f"Classification queued for {len(urls)} URLs"}
