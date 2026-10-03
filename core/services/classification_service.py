"""
Classification Service
Business logic for LLM classification operations.
"""

from typing import List, Optional, Dict, Any
from core.domain.classification import Classification
from core.repositories.classification_repository import ClassificationRepository
from core.domain.listing import Listing
from core.services.llm_filter_service import llm_filter_service
from modules.Mhandle_log import get_logger
import hashlib
from datetime import datetime

log = get_logger(__name__)


class ClassificationService:
    """Service layer for classification business logic."""
    
    def __init__(self):
        self.repository = ClassificationRepository()
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate SHA256 hash for URL."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    def create_classification(
        self,
        url: str,
        platform: str,
        alter_ok: Optional[bool] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        alter_jahre: Optional[int] = None,
        alter_unsicher: bool = False,
        einzelgaenger_unsicher: bool = False,
        freigang_unsicher: bool = False,
        kein_freigang_gewuenscht: bool = False,
        confidence: float = 0.0,
        reason: str = ""
    ) -> Classification:
        """Create classification entity."""
        url_hash = self._generate_url_hash(url)
        
        classification = Classification(
            url_hash=url_hash,
            url=url,
            platform=platform,
            alter_ok=alter_ok if alter_ok is not None else False,
            einzelgaenger=einzelgaenger if einzelgaenger is not None else False,
            freigang_noetig=freigang_noetig if freigang_noetig is not None else False,
            alter_jahre=alter_jahre,
            alter_unsicher=alter_unsicher,
            einzelgaenger_unsicher=einzelgaenger_unsicher,
            freigang_unsicher=freigang_unsicher,
            kein_freigang_gewuenscht=kein_freigang_gewuenscht,
            confidence=confidence,
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.repository.save(classification)
        return classification
    
    def get_classification_by_url_hash(self, url_hash: str) -> Optional[Classification]:
        """Get classification by URL hash."""
        return self.repository.find_by_url_hash(url_hash)
    
    def get_classification_by_url(self, url: str) -> Optional[Classification]:
        """Get classification by URL."""
        url_hash = self._generate_url_hash(url)
        return self.get_classification_by_url_hash(url_hash)
    
    def get_classifications(
        self,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        alter_ok: Optional[bool] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[Classification]:
        """Get classifications with optional filters."""
        return self.repository.find_all(
            limit=limit,
            offset=offset,
            platform=platform,
            alter_ok=alter_ok,
            einzelgaenger=einzelgaenger,
            freigang_noetig=freigang_noetig,
            min_confidence=min_confidence
        )
    
    def get_matching_classifications(
        self,
        alter_ok: bool = True,
        einzelgaenger: bool = False,
        freigang_noetig: bool = True,
        min_confidence: float = 0.7,
        limit: int = 100,
        offset: int = 0
    ) -> List[Classification]:
        """Get classifications matching criteria with minimum confidence."""
        return self.repository.find_matching_criteria(
            alter_ok=alter_ok,
            einzelgaenger=einzelgaenger,
            freigang_noetig=freigang_noetig,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset
        )
    
    async def classify_listing_async(
        self,
        url: str,
        platform: str,
        listing_data: Dict[str, Any],
        force_reclassify: bool = False
    ) -> Classification:
        """Classify listing using LLM with caching."""
        url_hash = self._generate_url_hash(url)
        
        # Check cache first
        if not force_reclassify:
            cached = self.get_classification_by_url_hash(url_hash)
            if cached:
                log.debug(f"Classification cache hit for {url}")
                return cached
        
        # Pre-filter check
        if not self._pre_filter_pass(listing_data):
            log.debug(f"Pre-filter rejected {url}")
            classification = self.create_classification(
                url=url,
                platform=platform,
                alter_ok=False,
                einzelgaenger=False,
                freigang_noetig=False,
                confidence=0.9,
                reason="Pre-filter rejected"
            )
            return classification
        
        # Query LLM
        result = await llm_filter_service.classify_listing(url, listing_data, platform)
        
        # Create classification from LLM result
        classification = self.create_classification(
            url=url,
            platform=platform,
            alter_ok=result.age_ok,
            einzelgaenger=result.einzelgaenger_ok,
            freigang_noetig=not result.freigang_ok,
            alter_unsicher=result.age_unsicher,
            einzelgaenger_unsicher=result.einzelgaenger_unsicher,
            freigang_unsicher=result.freigang_unsicher,
            confidence=result.confidence,
            reason=result.reasoning
        )
        
        return classification
    
    def _pre_filter_pass(self, listing: Dict) -> bool:
        """Quick pre-filter to avoid unnecessary LLM calls."""
        description = (listing.get("description", "") + " " + listing.get("title", "")).lower()
        
        # Very basic checks
        import re
        age_match = re.search(r'(\d+)\s*jahr', description)
        if age_match:
            age = int(age_match.group(1))
            if age < 2 or age > 8:
                return False
        
        # If no age info or age is ok, proceed to LLM
        return True
    
    def update_classification(
        self,
        url: str,
        updates: Dict[str, Any]
    ) -> Optional[Classification]:
        """Update classification with new data."""
        classification = self.get_classification_by_url(url)
        if not classification:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(classification, field):
                setattr(classification, field, value)
        
        classification.updated_at = datetime.utcnow()
        self.repository.save(classification)
        return classification
    
    def delete_classification(self, url: str) -> bool:
        """Delete classification by URL."""
        url_hash = self._generate_url_hash(url)
        self.repository.delete_by_url_hash(url_hash)
        return True
    
    def bulk_classify_listings(
        self,
        listings: List[Dict[str, Any]],
        platform: str,
        force_reclassify: bool = False
    ) -> List[Classification]:
        """Classify multiple listings (async batch)."""
        import asyncio
        
        async def classify_all():
            tasks = []
            for listing in listings:
                url = listing.get("url")
                if url:
                    tasks.append(self.classify_listing_async(url, platform, listing, force_reclassify))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            classifications = []
            for result in results:
                if isinstance(result, Classification):
                    classifications.append(result)
                elif isinstance(result, Exception):
                    log.error(f"Classification error: {result}")
            
            return classifications
        
        try:
            # Run event loop in current thread context
            return asyncio.run(classify_all())
        except RuntimeError:
            # If already in event loop, use alternative
            log.warning("Cannot run async classify in current context")
            return []
    
    def count_classifications(self, platform: Optional[str] = None) -> int:
        """Count total classifications."""
        return self.repository.count_all(platform=platform)
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        total = self.count_classifications()
        
        matching = self.get_matching_classifications(limit=10000)
        reliable = [c for c in self.get_classifications(limit=10000) if c.is_reliable()]
        
        # Count by platform
        platforms = {}
        classifications = self.get_classifications(limit=1000)
        for cls in classifications:
            platform = cls.platform
            if platform not in platforms:
                platforms[platform] = 0
            platforms[platform] += 1
        
        return {
            'total': total,
            'matching': len(matching),
            'reliable': len(reliable),
            'uncertain': len([c for c in classifications if c.get_uncertainties()]),
            'platforms': platforms
        }
    
    def get_uncertain_classifications(self, limit: int = 100) -> List[Classification]:
        """Get classifications with uncertainties."""
        all_classifications = self.get_classifications(limit=limit)
        uncertain = [c for c in all_classifications if c.get_uncertainties()]
        return uncertain
    
    def reclassify_outdated(
        self,
        days_old: int = 30,
        limit: int = 100
    ) -> List[Classification]:
        """Reclassify old classifications (placeholder)."""
        # TODO: Implement outdated detection logic
        log.info(f"Reclassify outdated classifications older than {days_old} days")
        return []


# Singleton instance
classification_service = ClassificationService()
