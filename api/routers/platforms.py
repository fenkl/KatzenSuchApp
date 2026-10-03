"""Platforms router for FastAPI API."""

from fastapi import APIRouter, Depends
from typing import List
from api.models.schemas import PlatformResponse
from api.dependencies import get_db_connection
from modules.db_utils import get_platforms

router = APIRouter()


@router.get("/", response_model=List[PlatformResponse])
async def list_platforms(db_conn = Depends(get_db_connection)):
    """Get all platforms."""
    platforms = get_platforms()
    return platforms
