"""
Domain Entity: Feature Request
Represents a feature request for new platforms or improvements.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class FeatureRequest:
    """Domain entity for feature requests."""
    id: Optional[int] = None
    platform_name: str = ""
    start_url: str = ""
    example_listing_url: str = ""
    description: str = ""
    created_by: str = ""
    created_at: Optional[datetime] = None
    status: str = "open"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureRequest':
        """Create FeatureRequest from dict (e.g. DB row)."""
        return cls(
            id=data.get('id'),
            platform_name=data.get('platform_name', ''),
            start_url=data.get('start_url', ''),
            example_listing_url=data.get('example_listing_url', ''),
            description=data.get('description', ''),
            created_by=data.get('created_by', ''),
            created_at=data.get('created_at'),
            status=data.get('status', 'open')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert FeatureRequest to dict."""
        return {
            'id': self.id,
            'platform_name': self.platform_name,
            'start_url': self.start_url,
            'example_listing_url': self.example_listing_url,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'status': self.status,
        }

    def is_open(self) -> bool:
        """Check if request is open."""
        return self.status == "open"

    def is_in_progress(self) -> bool:
        """Check if request is in progress."""
        return self.status == "in_progress"

    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == "completed"

    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == "rejected"
