"""Scraper Service with City Rotation and Platform Management."""

from typing import List, Dict
from modules.Mhandle_log import get_logger
from classes.Cconfig import Config
from modules.services.orchestrator import orchestrator

log = get_logger(__name__)
config = Config()


class ScraperService:
    """Service for managing scrapers with city rotation."""
    
    def __init__(self):
        self.orchestrator = orchestrator
        self.cities = config.cities
        self.platforms = config.platform_configs
    
    def get_platforms(self) -> List[str]:
        """Get list of enabled platforms."""
        return [
            name for name, config in self.platforms.items()
            if config.get("enabled", True)
        ]
    
    def get_cities(self) -> List[str]:
        """Get list of cities."""
        return self.cities
    
    async def scrape_platform_for_city(self, platform_name: str, city: str, max_pages: int = 3) -> List[Dict]:
        """Scrape specific platform for a city."""
        return await self.orchestrator.scrape_platform_city(platform_name, city, max_pages)
    
    async def scrape_all_platforms_for_city(self, city: str, max_pages: int = 3) -> Dict[str, List[Dict]]:
        """Scrape all platforms for a given city."""
        results = {}
        for platform_name in self.get_platforms():
            listings = await self.scrape_platform_for_city(platform_name, city, max_pages)
            results[platform_name] = listings
        return results
    
    async def scrape_all_cities_rotation(self, max_pages: int = 3) -> Dict:
        """Scrape all cities in rotation."""
        all_results = {}
        for city in self.cities:
            log.info(f"Scraping all platforms for city: {city}")
            city_results = await self.scrape_all_platforms_for_city(city, max_pages)
            all_results[city] = city_results
        return all_results
    
    def get_next_city_in_rotation(self) -> str:
        """Get next city in rotation."""
        return self.orchestrator.get_next_city()
    
    def get_current_city(self) -> str:
        """Get current city."""
        return self.orchestrator.get_current_city()


# Singleton instance
scraper_service = ScraperService()
