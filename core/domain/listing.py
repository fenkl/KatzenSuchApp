"""
Domain Entity: Listing
Represents a scraped cat listing from various platforms.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Listing:
    """Domain entity for cat listings."""
    url: str
    platform: str
    city: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    age: Optional[int] = None
    url_hash: Optional[str] = None
    extracted_at: Optional[datetime] = None
    processed: Optional[bool] = None
    
    # Classification fields (from LLM)
    confidence: Optional[float] = None
    alter_ok: Optional[bool] = None
    alter_jahre: Optional[int] = None
    alter_unsicher: Optional[bool] = None
    einzelgaenger: Optional[bool] = None
    einzelgaenger_unsicher: Optional[bool] = None
    freigang_noetig: Optional[bool] = None
    freigang_unsicher: Optional[bool] = None
    kein_freigang_gewuenscht: Optional[bool] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Listing':
        """Create Listing from dict (e.g. DB row)."""
        return cls(
            url=data.get('url'),
            platform=data.get('platform'),
            city=data.get('city'),
            title=data.get('title'),
            description=data.get('description'),
            age=data.get('age'),
            url_hash=data.get('url_hash'),
            extracted_at=data.get('extracted_at'),
            processed=bool(data.get('processed')) if data.get('processed') is not None else None,
            confidence=data.get('confidence'),
            alter_ok=bool(data.get('alter_ok')) if data.get('alter_ok') is not None else None,
            alter_jahre=data.get('alter_jahre'),
            alter_unsicher=bool(data.get('alter_unsicher')) if data.get('alter_unsicher') is not None else None,
            einzelgaenger=bool(data.get('einzelgaenger')) if data.get('einzelgaenger') is not None else None,
            einzelgaenger_unsicher=bool(data.get('einzelgaenger_unsicher')) if data.get('einzelgaenger_unsicher') is not None else None,
            freigang_noetig=bool(data.get('freigang_noetig')) if data.get('freigang_noetig') is not None else None,
            freigang_unsicher=bool(data.get('freigang_unsicher')) if data.get('freigang_unsicher') is not None else None,
            kein_freigang_gewuenscht=bool(data.get('kein_freigang_gewuenscht')) if data.get('kein_freigang_gewuenscht') is not None else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Listing to dict."""
        return {
            'url': self.url,
            'platform': self.platform,
            'city': self.city,
            'title': self.title,
            'description': self.description,
            'age': self.age,
            'url_hash': self.url_hash,
            'extracted_at': self.extracted_at,
            'processed': self.processed,
            'confidence': self.confidence,
            'alter_ok': self.alter_ok,
            'alter_jahre': self.alter_jahre,
            'alter_unsicher': self.alter_unsicher,
            'einzelgaenger': self.einzelgaenger,
            'einzelgaenger_unsicher': self.einzelgaenger_unsicher,
            'freigang_noetig': self.freigang_noetig,
            'freigang_unsicher': self.freigang_unsicher,
            'kein_freigang_gewuenscht': self.kein_freigang_gewuenscht,
        }

    def is_matching_criteria(self, alter_ok: bool = True, einzelgaenger: bool = False, freigang_noetig: bool = True) -> bool:
        """Check if listing matches filter criteria."""
        if self.alter_ok is None or self.einzelgaenger is None or self.freigang_noetig is None:
            return False
        
        return (
            self.alter_ok == alter_ok and
            self.einzelgaenger == einzelgaenger and
            self.freigang_noetig == freigang_noetig
        )

    def get_match_score(self) -> float:
        """Calculate match score based on classification confidence."""
        if self.confidence is None:
            return 0.0
        return self.confidence
