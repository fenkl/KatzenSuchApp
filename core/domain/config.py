"""
Domain Entity: Config
Represents application configuration settings.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Config:
    """Domain entity for application configuration."""
    key: str
    value: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dict (e.g. DB row)."""
        return cls(
            key=data.get('key'),
            value=data.get('value'),
            description=data.get('description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dict."""
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class PlatformConfig:
    """Domain entity for platform-specific configuration."""
    platform_name: str
    base_url: str
    listing_selector: Optional[str] = None
    detail_selector: Optional[str] = None
    pagination_param: Optional[str] = None
    city_param: Optional[str] = None
    enabled: bool = True
    handler_class: Optional[str] = None
    login_required: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformConfig':
        """Create PlatformConfig from dict (e.g. DB row)."""
        return cls(
            platform_name=data.get('platform_name'),
            base_url=data.get('base_url'),
            listing_selector=data.get('listing_selector'),
            detail_selector=data.get('detail_selector'),
            pagination_param=data.get('pagination_param'),
            city_param=data.get('city_param'),
            enabled=bool(data.get('enabled', 0)),
            handler_class=data.get('handler_class'),
            login_required=bool(data.get('login_required', 0)),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert PlatformConfig to dict."""
        return {
            'platform_name': self.platform_name,
            'base_url': self.base_url,
            'listing_selector': self.listing_selector,
            'detail_selector': self.detail_selector,
            'pagination_param': self.pagination_param,
            'city_param': self.city_param,
            'enabled': self.enabled,
            'handler_class': self.handler_class,
            'login_required': self.login_required,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def is_enabled(self) -> bool:
        """Check if platform config is enabled."""
        return self.enabled

    def can_scrape(self) -> bool:
        """Check if platform can be scraped (enabled and has selectors)."""
        return self.enabled and self.listing_selector is not None


@dataclass
class FilterCriteria:
    """Domain entity for filter criteria configuration."""
    alter_min: int = 2
    alter_max: int = 8
    einzelgaenger: bool = True
    kein_freigang_noetig: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterCriteria':
        """Create FilterCriteria from dict."""
        return cls(
            alter_min=int(data.get('alter_min', 2)),
            alter_max=int(data.get('alter_max', 8)),
            einzelgaenger=bool(data.get('einzelgaenger', True)),
            kein_freigang_noetig=bool(data.get('kein_freigang_noetig', True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert FilterCriteria to dict."""
        return {
            'alter_min': self.alter_min,
            'alter_max': self.alter_max,
            'einzelgaenger': self.einzelgaenger,
            'kein_freigang_noetig': self.kein_freigang_noetig,
        }
