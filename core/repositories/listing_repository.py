"""
Listing Repository
Handles CRUD operations for listings via Repository Pattern.
"""

from typing import List, Optional, Dict, Any
from core.repositories.base_repository import BaseRepository
from core.domain.listing import Listing
import hashlib
from datetime import datetime


class ListingRepository(BaseRepository):
    """Repository for listing persistence."""

    def save(self, listing: Listing) -> None:
        """Save listing to database."""
        url_hash = hashlib.sha256(listing.url.encode()).hexdigest()
        
        query = """
            INSERT OR REPLACE INTO scraped_listings
            (url, platform, city, title, description, age, url_hash, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            listing.url,
            listing.platform,
            listing.city,
            listing.title,
            listing.description,
            listing.age,
            url_hash,
            listing.extracted_at
        )
        self.execute_single(query, params)

    def find_by_url(self, url: str) -> Optional[Listing]:
        """Find listing by URL."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        query = """
            SELECT sl.*, lc.confidence, lc.alter_ok, lc.einzelgaenger, 
                   lc.freigang_noetig, lc.alter_jahre, lc.alter_unsicher,
                   lc.einzelgaenger_unsicher, lc.freigang_unsicher,
                   lc.kein_freigang_gewuenscht
            FROM scraped_listings sl
            LEFT JOIN llm_classification lc ON sl.url_hash = lc.url_hash
            WHERE sl.url_hash = ?
        """
        result = self.fetch_one(query, (url_hash,))
        if result:
            return Listing.from_dict(result)
        return None

    def find_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        platform: Optional[str] = None,
        city: Optional[str] = None,
        processed: Optional[int] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[Listing]:
        """Find all listings with filters."""
        conditions = []
        params = []
        
        if platform:
            conditions.append("sl.platform = ?")
            params.append(platform)
        
        if city:
            conditions.append("sl.city = ?")
            params.append(city)
            
        if processed is not None:
            conditions.append("sl.processed = ?")
            params.append(processed)
        
        if age_min is not None:
            conditions.append("sl.age >= ?")
            params.append(age_min)
        
        if age_max is not None:
            conditions.append("sl.age <= ?")
            params.append(age_max)
        
        if einzelgaenger is not None:
            conditions.append("lc.einzelgaenger = ?")
            params.append(1 if einzelgaenger else 0)
        
        if freigang_noetig is not None:
            conditions.append("lc.freigang_noetig = ?")
            params.append(1 if freigang_noetig else 0)
        
        if min_confidence is not None:
            conditions.append("lc.confidence >= ?")
            params.append(min_confidence)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT sl.*, lc.confidence, lc.alter_ok, lc.einzelgaenger, 
                   lc.freigang_noetig, lc.alter_jahre, lc.alter_unsicher,
                   lc.einzelgaenger_unsicher, lc.freigang_unsicher,
                   lc.kein_freigang_gewuenscht
            FROM scraped_listings sl
            LEFT JOIN llm_classification lc ON sl.url_hash = lc.url_hash
            {where_clause}
            ORDER BY lc.confidence DESC, sl.extracted_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params))
        return [Listing.from_dict(row) for row in results]

    def find_matching(
        self,
        alter_ok: bool = True,
        einzelgaenger: bool = False,
        freigang_noetig: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Listing]:
        """Find listings matching classification criteria."""
        query = """
            SELECT sl.*, lc.confidence, lc.alter_ok, lc.einzelgaenger, 
                   lc.freigang_noetig, lc.alter_jahre, lc.alter_unsicher,
                   lc.einzelgaenger_unsicher, lc.freigang_unsicher,
                   lc.kein_freigang_gewuenscht
            FROM scraped_listings sl
            JOIN llm_classification lc ON sl.url_hash = lc.url_hash
            WHERE lc.alter_ok = ? 
              AND lc.einzelgaenger = ?
              AND lc.freigang_noetig = ?
            ORDER BY lc.confidence DESC
            LIMIT ? OFFSET ?
        """
        params = (alter_ok, einzelgaenger, freigang_noetig, limit, offset)
        results = self.execute_query(query, params)
        return [Listing.from_dict(row) for row in results]

    def count_all(self, platform: Optional[str] = None) -> int:
        """Count total listings."""
        if platform:
            query = "SELECT COUNT(*) as count FROM scraped_listings WHERE platform = ?"
            result = self.fetch_one(query, (platform,))
        else:
            query = "SELECT COUNT(*) as count FROM scraped_listings"
            result = self.fetch_one(query)
        
        return result['count'] if result else 0

    def mark_processed(self, url: str, platform: str, processed: bool = True) -> None:
        """Mark listing as processed."""
        query = """
            UPDATE seen_urls SET processed = ?, last_seen = CURRENT_TIMESTAMP 
            WHERE url = ? AND platform = ?
        """
        self.execute_single(query, (1 if processed else 0, url, platform))

    def exists(self, url: str, platform: str) -> bool:
        """Check if listing exists."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        query = "SELECT 1 FROM scraped_listings WHERE url_hash = ? AND platform = ?"
        result = self.fetch_one(query, (url_hash, platform))
        return result is not None
