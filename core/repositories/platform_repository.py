"""
Platform Repository
Handles CRUD operations for platforms via Repository Pattern.
"""

from typing import List, Optional, Dict, Any
from core.repositories.base_repository import BaseRepository
from core.domain.config import PlatformConfig
import hashlib


class PlatformRepository(BaseRepository):
    """Repository for platform persistence."""

    def save(self, platform_config: PlatformConfig) -> None:
        """Save platform config to database."""
        query = """
            INSERT OR REPLACE INTO scraper_configs
            (platform_name, base_url, listing_selector, detail_selector,
             pagination_param, city_param, enabled, handler_class, login_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            platform_config.platform_name,
            platform_config.base_url,
            platform_config.listing_selector,
            platform_config.detail_selector,
            platform_config.pagination_param,
            platform_config.city_param,
            1 if platform_config.enabled else 0,
            platform_config.handler_class,
            1 if platform_config.login_required else 0
        )
        self.execute_single(query, params)

    def find_by_name(self, platform_name: str) -> Optional[PlatformConfig]:
        """Find platform config by name."""
        query = """
            SELECT platform_name, base_url, listing_selector, detail_selector,
                   pagination_param, city_param, enabled, handler_class, login_required
            FROM scraper_configs
            WHERE platform_name = ?
        """
        result = self.fetch_one(query, (platform_name,))
        if result:
            return PlatformConfig.from_dict(result)
        return None

    def find_all(
        self,
        enabled_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[PlatformConfig]:
        """Find all platform configs."""
        conditions = []
        params = []
        
        if enabled_only:
            conditions.append("enabled = ?")
            params.append(1)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT platform_name, base_url, listing_selector, detail_selector,
                   pagination_param, city_param, enabled, handler_class, login_required
            FROM scraper_configs
            {where_clause}
            ORDER BY platform_name ASC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params))
        return [PlatformConfig.from_dict(row) for row in results]

    def find_enabled(self) -> List[PlatformConfig]:
        """Find all enabled platforms."""
        return self.find_all(enabled_only=True)

    def find_by_url(self, url: str) -> Optional[PlatformConfig]:
        """Find platform by URL."""
        # Extract platform from URL or check all platforms
        platforms = self.find_all(enabled_only=False)
        for platform in platforms:
            if platform.base_url and platform.base_url in url:
                return platform
        return None

    def count_all(self, enabled_only: bool = False) -> int:
        """Count total platforms."""
        if enabled_only:
            query = "SELECT COUNT(*) as count FROM scraper_configs WHERE enabled = 1"
            result = self.fetch_one(query)
        else:
            query = "SELECT COUNT(*) as count FROM scraper_configs"
            result = self.fetch_one(query)
        
        return result['count'] if result else 0

    def delete_by_name(self, platform_name: str) -> None:
        """Delete platform config by name."""
        query = "DELETE FROM scraper_configs WHERE platform_name = ?"
        self.execute_single(query, (platform_name,))

    def bulk_save(self, platform_configs: List[PlatformConfig]) -> None:
        """Bulk save platform configs."""
        query = """
            INSERT OR REPLACE INTO scraper_configs
            (platform_name, base_url, listing_selector, detail_selector,
             pagination_param, city_param, enabled, handler_class, login_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_list = []
        for config in platform_configs:
            params_list.append((
                config.platform_name,
                config.base_url,
                config.listing_selector,
                config.detail_selector,
                config.pagination_param,
                config.city_param,
                1 if config.enabled else 0,
                config.handler_class,
                1 if config.login_required else 0
            ))
        self.execute_many(query, params_list)

    def exists(self, platform_name: str) -> bool:
        """Check if platform exists."""
        query = "SELECT 1 FROM scraper_configs WHERE platform_name = ?"
        result = self.fetch_one(query, (platform_name,))
        return result is not None

    def update_enabled(self, platform_name: str, enabled: bool) -> None:
        """Update platform enabled status."""
        query = "UPDATE scraper_configs SET enabled = ? WHERE platform_name = ?"
        self.execute_single(query, (1 if enabled else 0, platform_name))
