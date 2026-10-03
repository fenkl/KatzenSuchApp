"""
Domain Entity: Classification
Represents LLM classification result for a listing.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Classification:
    """Domain entity for LLM classification results."""
    url_hash: str
    url: str
    platform: str
    
    # Alter classification
    alter_ok: bool
    einzelgaenger: bool
    freigang_noetig: bool
    
    # Optional fields
    alter_jahre: Optional[int] = None
    alter_unsicher: bool = False
    einzelgaenger_unsicher: bool = False
    freigang_unsicher: bool = False
    kein_freigang_gewuenscht: bool = False
    
    # Metadata
    confidence: float = 0.0
    reason: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Classification':
        """Create Classification from dict (e.g. DB row)."""
        return cls(
            url_hash=data.get('url_hash'),
            url=data.get('url'),
            platform=data.get('platform'),
            alter_ok=bool(data.get('alter_ok', False)),
            alter_jahre=data.get('alter_jahre'),
            alter_unsicher=bool(data.get('alter_unsicher', False)),
            einzelgaenger=bool(data.get('einzelgaenger', False)),
            einzelgaenger_unsicher=bool(data.get('einzelgaenger_unsicher', False)),
            freigang_noetig=bool(data.get('freigang_noetig', False)),
            freigang_unsicher=bool(data.get('freigang_unsicher', False)),
            kein_freigang_gewuenscht=bool(data.get('kein_freigang_gewuenscht', False)),
            confidence=float(data.get('confidence', 0.0)),
            reason=data.get('reason', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Classification to dict."""
        return {
            'url_hash': self.url_hash,
            'url': self.url,
            'platform': self.platform,
            'alter_ok': self.alter_ok,
            'alter_jahre': self.alter_jahre,
            'alter_unsicher': self.alter_unsicher,
            'einzelgaenger': self.einzelgaenger,
            'einzelgaenger_unsicher': self.einzelgaenger_unsicher,
            'freigang_noetig': self.freigang_noetig,
            'freigang_unsicher': self.freigang_unsicher,
            'kein_freigang_gewuenscht': self.kein_freigang_gewuenscht,
            'confidence': self.confidence,
            'reason': self.reason,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def is_reliable(self, min_confidence: float = 0.7) -> bool:
        """Check if classification is reliable."""
        return self.confidence >= min_confidence

    def get_uncertainties(self) -> list[str]:
        """Get list of uncertain classifications."""
        uncertainties = []
        if self.alter_unsicher:
            uncertainties.append('alter')
        if self.einzelgaenger_unsicher:
            uncertainties.append('einzelgaenger')
        if self.freigang_unsicher:
            uncertainties.append('freigang')
        return uncertainties

    def matches_criteria(self, alter_ok: Optional[bool] = None, 
                        einzelgaenger: Optional[bool] = None,
                        freigang_noetig: Optional[bool] = None) -> bool:
        """Check if classification matches given criteria."""
        if alter_ok is not None and self.alter_ok != alter_ok:
            return False
        if einzelgaenger is not None and self.einzelgaenger != einzelgaenger:
            return False
        if freigang_noetig is not None and self.freigang_noetig != freigang_noetig:
            return False
        return True
