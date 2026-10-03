"""Listings router with JWT authentication."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from api.models.schemas import ListingResponse, MarkProcessedRequest
from api.dependencies import get_current_user, UserInfo
from core.services.listing_service import listing_service
from core.services.classification_service import ClassificationService
from modules.Mhandle_log import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    platform: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    processed: Optional[bool] = Query(None),
    age_min: Optional[int] = Query(None, ge=0),
    age_max: Optional[int] = Query(None, ge=0),
    einzelgaenger: Optional[bool] = Query(None),
    freigang_noetig: Optional[bool] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    current_user = Depends(get_current_user)
):
    """Get listings with optional filters - requires authentication."""
    try:
        listings = listing_service.get_listings(
            limit=limit,
            offset=offset,
            platform=platform,
            city=city,
            processed=processed,
            age_min=age_min,
            age_max=age_max,
            einzelgaenger=einzelgaenger,
            freigang_noetig=freigang_noetig,
            min_confidence=min_confidence
        )
        return listings
    except Exception as e:
        log.error(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: int,
    current_user = Depends(get_current_user)
):
    """Get specific listing by ID."""
    listings = listing_service.get_listings(limit=1000)
    for listing in listings:
        if listing.id == listing_id:
            return listing
    
    raise HTTPException(status_code=404, detail="Listing not found")


@router.get("/search/", response_model=List[ListingResponse])
async def search_listings(
    q: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user)
):
    """Search listings by title or description."""
    results = listing_service.search_listings(query=q, limit=limit)
    return results


@router.get("/platform/{platform_name}", response_model=List[ListingResponse])
async def get_listings_by_platform(
    platform_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user)
):
    """Get listings for specific platform."""
    listings = listing_service.get_listings_by_platform(
        platform=platform_name,
        limit=limit,
        offset=offset
    )
    return listings


@router.get("/matching/", response_model=List[ListingResponse])
async def get_matching_listings(
    alter_ok: bool = Query(True),
    einzelgaenger: bool = Query(False),
    freigang_noetig: bool = Query(True),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user)
):
    """Get listings matching classification criteria."""
    listings = listing_service.get_matching_listings(
        alter_ok=alter_ok,
        einzelgaenger=einzelgaenger,
        freigang_noetig=freigang_noetig,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset
    )
    return listings


@router.get("/stats/summary/")
async def get_listing_stats(current_user = Depends(get_current_user)):
    """Get listing statistics."""
    stats = listing_service.get_listing_stats()
    return stats


@router.get("/cities/")
async def get_cities(current_user = Depends(get_current_user)):
    """Get available cities."""
    listings = listing_service.get_listings(limit=1000)
    cities = set()
    for listing in listings:
        if listing.city:
            cities.add(listing.city)
    return {"cities": list(cities)}


@router.get("/platforms/")
async def get_platforms(current_user = Depends(get_current_user)):
    """Get available platforms."""
    listings = listing_service.get_listings(limit=1000)
    platforms = set()
    for listing in listings:
        platforms.add(listing.platform)
    return {"platforms": list(platforms)}


@router.post("/mark-processed")
async def mark_processed(
    request: MarkProcessedRequest,
    current_user = Depends(get_current_user)
):
    """Mark listing as processed."""
    try:
        listing_service.mark_as_processed(request.url, request.platform)
        return {"success": True, "message": f"URL als verarbeitet markiert: {request.url}"}
    except Exception as e:
        log.error(f"Error marking listing as processed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
