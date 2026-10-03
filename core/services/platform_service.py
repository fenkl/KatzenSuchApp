"""
Platform Service
Business logic for platform configuration management.
"""

from typing import List, Optional, Dict, Any
from core.domain.config import PlatformConfig
from core.repositories.platform_repository import PlatformRepository
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class PlatformService:
    """Service layer for platform configuration management."""
    
    def __init__(self):
        self.repository = PlatformRepository()
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """Get all platform configs."""
        try:
            configs = self.repository.find_all(enabled_only=False, limit=1000)
            return [config.to_dict() for config in configs]
        except Exception as e:
            log.error(f"Error getting platform configs: {e}")
            raise
    
    def get_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get single platform config."""
        try:
            config = self.repository.find_by_name(platform_name)
            return config.to_dict() if config else None
        except Exception as e:
            log.error(f"Error getting platform config {platform_name}: {e}")
            raise
    
    def save_config(self, platform_config: PlatformConfig) -> None:
        """Save platform config."""
        try:
            self.repository.save(platform_config)
            log.info(f"Platform config saved for {platform_config.platform_name}")
        except Exception as e:
            log.error(f"Error saving platform config {platform_config.platform_name}: {e}")
            raise
    
    def update_config(self, platform_name: str, updates: Dict[str, Any]) -> bool:
        """Update platform config fields."""
        try:
            existing = self.repository.find_by_name(platform_name)
            if not existing:
                return False
            
            for field, value in updates.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)
            
            self.repository.save(existing)
            log.info(f"Platform config updated for {platform_name}")
            return True
        except Exception as e:
            log.error(f"Error updating platform config {platform_name}: {e}")
            raise
    
    def delete_config(self, platform_name: str) -> bool:
        """Delete platform config."""
        try:
            if not self.repository.exists(platform_name):
                return False
            
            self.repository.delete_by_name(platform_name)
            log.info(f"Platform config deleted for {platform_name}")
            return True
        except Exception as e:
            log.error(f"Error deleting platform config {platform_name}: {e}")
            raise
    
    def create_config(self, platform_config: PlatformConfig) -> bool:
        """Create new platform config."""
        try:
            if self.repository.exists(platform_config.platform_name):
                log.warning(f"Platform config already exists for {platform_config.platform_name}")
                return False
            
            self.repository.save(platform_config)
            log.info(f"Platform config created for {platform_config.platform_name}")
            return True
        except Exception as e:
            log.error(f"Error creating platform config {platform_config.platform_name}: {e}")
            raise
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get all enabled platforms."""
        try:
            return self.repository.find_enabled()
        except Exception as e:
            log.error(f"Error getting enabled platforms: {e}")
            raise
    
    def count_configs(self) -> int:
        """Count total platform configs."""
        try:
            return self.repository.count_all(enabled_only=False)
        except Exception as e:
            log.error(f"Error counting platform configs: {e}")
            raise


# Singleton instance
platform_service = PlatformService()
