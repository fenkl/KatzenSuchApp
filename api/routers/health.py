"""Health check router."""

from fastapi import APIRouter
from api.models.schemas import HealthResponse
from api.dependencies import get_config

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(config=get_config):
    """Health check endpoint."""
    cfg = config()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        db_path=cfg.db_path
    )
