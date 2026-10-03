"""DB Service wrapper for KatzenSuchApp."""

from typing import Dict, List, Optional, Any
from modules.Mhandle_log import get_logger
from modules.db_utils import init_db, is_known, save_url, get_scraper_configs, add_scraper_config, get_platforms, add_feature_request, get_feature_requests, cache_llm_classification, get_llm_classification

log = get_logger(__name__)


class DBService:
    """Service for database operations."""
    
    def init_db(self):
        """Initialize database."""
        log.info("Initializing database")
        init_db()
        log.info("Database initialized")
    
    def is_known(self, url: str, platform: str) -> bool:
        """Check if URL is already known."""
        return is_known(url, platform)
    
    def save_url(self, url: str, platform: str):
        """Save URL to database."""
        save_url(url, platform)
    
    def get_scraper_configs(self) -> List[Dict]:
        """Get all scraper configurations."""
        return get_scraper_configs()
    
    def add_scraper_config(self, platform: str, config: Dict):
        """Add scraper configuration."""
        add_scraper_config(platform, config)
    
    def get_platforms(self) -> List[Dict]:
        """Get all platforms."""
        return get_platforms()
    
    def add_feature_request(self, request_type: str, description: str, user_id: Optional[str] = None):
        """Add feature request."""
        add_feature_request(request_type, description, user_id)
    
    def get_feature_requests(self, status: Optional[str] = None) -> List[Dict]:
        """Get feature requests."""
        return get_feature_requests(status)
    
    def cache_llm_classification(self, url: str, platform: str, result: Dict):
        """Cache LLM classification."""
        cache_llm_classification(url, platform, result)
    
    def get_llm_classification(self, url: str) -> Optional[Dict]:
        """Get cached LLM classification."""
        return get_llm_classification(url)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            "platforms": len(self.get_platforms()),
            "feature_requests": len(self.get_feature_requests()),
        }
        return stats


# Singleton instance
db_service = DBService()
