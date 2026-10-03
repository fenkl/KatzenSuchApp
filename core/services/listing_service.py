"""
Listing Service
Business logic for listing operations.
Extracts business logic from API routers.
"""

from typing import List, Optional
from core.domain.listing import Listing
from core.repositories.listing_repository import ListingRepository
import hashlib
from datetime import datetime


class ListingService:
    """Service layer for listing business logic."""
    
    def __init__(self):
        self.repository = ListingRepository()
    
    def create_listing_from_scrape(
        self,
        url: str,
        platform: str,
        city: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        age: Optional[int] = None
    ) -> Listing:
        """Create a listing from scraped data."""
        listing = Listing(
            url=url,
            platform=platform,
            city=city,
            title=title,
            description=description,
            age=age,
            extracted_at=datetime.utcnow(),
            processed=False
        )
        self.repository.save(listing)
        return listing
    
    def get_listing_by_url(self, url: str) -> Optional[Listing]:
        """Get listing by URL."""
        return self.repository.find_by_url(url)
    
    def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        city: Optional[str] = None,
        processed: Optional[bool] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[Listing]:
        """Get listings with optional filters."""
        processed_int = None
        if processed is not None:
            processed_int = 1 if processed else 0
        
        return self.repository.find_all(
            limit=limit,
            offset=offset,
            platform=platform,
            city=city,
            processed=processed_int,
            age_min=age_min,
            age_max=age_max,
            einzelgaenger=einzelgaenger,
            freigang_noetig=freigang_noetig,
            min_confidence=min_confidence
        )
    
    def get_matching_listings(
        self,
        alter_ok: bool = True,
        einzelgaenger: bool = False,
        freigang_noetig: bool = True,
        min_confidence: float = 0.7,
        limit: int = 100,
        offset: int = 0
    ) -> List[Listing]:
        """Get listings matching classification criteria."""
        listings = self.repository.find_matching(
            alter_ok=alter_ok,
            einzelgaenger=einzelgaenger,
            freigang_noetig=freigang_noetig,
            limit=limit,
            offset=offset
        )
        
        # Filter by minimum confidence
        filtered = []
        for listing in listings:
            if listing.confidence is None:
                continue
            if listing.confidence >= min_confidence and listing.is_matching_criteria(
                alter_ok=alter_ok,
                einzelgaenger=einzelgaenger,
                freigang_noetig=freigang_noetig
            ):
                filtered.append(listing)
        
        return filtered
    
    def update_listing_classification(
        self,
        url: str,
        classification_data: dict
    ) -> Optional[Listing]:
        """Update listing with classification data."""
        listing = self.repository.find_by_url(url)
        if not listing:
            return None
        
        # Update classification fields
        listing.confidence = classification_data.get('confidence', listing.confidence)
        listing.alter_ok = classification_data.get('alter_ok', listing.alter_ok)
        listing.alter_jahre = classification_data.get('alter_jahre', listing.alter_jahre)
        listing.alter_unsicher = classification_data.get('alter_unsicher', listing.alter_unsicher)
        listing.einzelgaenger = classification_data.get('einzelgaenger', listing.einzelgaenger)
        listing.einzelgaenger_unsicher = classification_data.get('einzelgaenger_unsicher', listing.einzelgaenger_unsicher)
        listing.freigang_noetig = classification_data.get('freigang_noetig', listing.freigang_noetig)
        listing.freigang_unsicher = classification_data.get('freigang_unsicher', listing.freigang_unsicher)
        listing.kein_freigang_gewuenscht = classification_data.get('kein_freigang_gewuenscht', listing.kein_freigang_gewuenscht)
        
        # Save updated listing
        self.repository.save(listing)
        return listing
    
    def mark_as_processed(self, url: str, platform: str) -> None:
        """Mark listing as processed."""
        self.repository.mark_processed(url, platform, processed=True)
    
    def exists(self, url: str, platform: str) -> bool:
        """Check if listing exists."""
        return self.repository.exists(url, platform)
    
    def count_listings(self, platform: Optional[str] = None) -> int:
        """Count total listings."""
        return self.repository.count_all(platform=platform)
    
    def get_listing_stats(self) -> dict:
        """Get listing statistics."""
        total = self.count_listings()
        
        # Count processed listings
        processed_listings = self.get_listings(processed=True)
        
        # Count matching listings
        matching = self.get_matching_listings(limit=1000)
        
        return {
            'total': total,
            'processed': len(processed_listings),
            'matching': len(matching),
            'unprocessed': total - len(processed_listings)
        }
    
    def search_listings(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Listing]:
        """Search listings by title or description."""
        all_listings = self.get_listings(limit=limit, offset=offset)
        
        query_lower = query.lower()
        results = []
        for listing in all_listings:
            title_match = listing.title and query_lower in listing.title.lower()
            desc_match = listing.description and query_lower in listing.description.lower()
            if title_match or desc_match:
                results.append(listing)
        
        return results[:limit]
    
    def get_listings_by_platform(
        self,
        platform: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Listing]:
        """Get listings for specific platform."""
        return self.get_listings(limit=limit, offset=offset, platform=platform)
    
    def get_recent_listings(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Listing]:
        """Get listings from last N days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        all_listings = self.get_listings(limit=limit)
        recent = []
        for listing in all_listings:
            if listing.extracted_at and listing.extracted_at >= cutoff:
                recent.append(listing)
        
        return recent


# Singleton instance
listing_service = ListingService()
