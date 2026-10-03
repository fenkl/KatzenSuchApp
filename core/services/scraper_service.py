"""
Scraper Service
Business logic for scraping orchestration.
Integrates with existing scraper modules and domain layer.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
from modules.Mhandle_log import get_logger
from classes.Cconfig import Config
from core.domain.listing import Listing
from core.repositories.listing_repository import ListingRepository
from core.services.listing_service import ListingService
from core.services.classification_service import ClassificationService

log = get_logger(__name__)
config = Config()


@dataclass
class ScraperStatus:
    """Status information for scraper operations."""
    running: bool
    current_city: str
    cities: List[str]
    platforms: List[str]
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class ScraperService:
    """Service for managing scraper orchestration with domain integration."""
    
    def __init__(self):
        self.config = Config()
        self.listing_service = ListingService()
        self.classification_service = ClassificationService()
        self.cities = self.config.cities
        self.platform_configs = self.config.platform_configs
        self.current_city_index = 0
        self.running = False
        self.last_run_timestamp: Optional[datetime] = None
    
    def get_platforms(self) -> List[str]:
        """Get list of enabled platforms."""
        platforms = []
        for name, cfg in self.platform_configs.items():
            if cfg.get("enabled", True):
                platforms.append(name)
        return platforms
    
    def get_cities(self) -> List[str]:
        """Get list of cities."""
        return self.cities
    
    def get_status(self) -> ScraperStatus:
        """Get current scraper status."""
        return ScraperStatus(
            running=self.running,
            current_city=self.get_current_city(),
            cities=self.cities,
            platforms=self.get_platforms(),
            last_run=self.last_run_timestamp
        )
    
    def get_current_city(self) -> str:
        """Get current city in rotation."""
        return self.cities[self.current_city_index]
    
    def get_next_city(self) -> str:
        """Get next city in rotation and advance index."""
        city = self.cities[self.current_city_index]
        self.current_city_index = (self.current_city_index + 1) % len(self.cities)
        return city
    
    async def scrape_platform_city(
        self, 
        platform_name: str, 
        city: str, 
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """Scrape specific platform for a city using existing scraper infrastructure."""
        try:
            # Import here to avoid circular dependencies
            from modules.services.orchestrator import orchestrator
            results = await orchestrator.scrape_platform_city(platform_name, city, max_pages)
            log.info(f"Scraped {len(results)} listings from {platform_name} for {city}")
            return results
        except Exception as e:
            log.error(f"Error scraping {platform_name} for {city}: {e}")
            return []
    
    async def scrape_all_platforms_for_city(
        self, 
        city: str, 
        max_pages: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape all platforms for a given city."""
        results = {}
        platforms = self.get_platforms()
        
        for platform_name in platforms:
            listings = await self.scrape_platform_city(platform_name, city, max_pages)
            results[platform_name] = listings
        
        return results
    
    async def trigger_scraping(
        self,
        city: Optional[str] = None,
        platform: Optional[str] = None,
        max_pages: int = 3,
        classify: bool = True
    ) -> Dict[str, Any]:
        """Trigger scraping operation with optional classification."""
        self.running = True
        self.last_run_timestamp = datetime.utcnow()
        
        log.info(f"Starting scraping operation: city={city}, platform={platform}")
        
        try:
            if city is None:
                city = self.get_next_city()
            
            if platform:
                # Scrape specific platform
                results = await self.scrape_platform_city(platform, city, max_pages)
                platform_results = {platform: results}
            else:
                # Scrape all platforms
                platform_results = await self.scrape_all_platforms_for_city(city, max_pages)
            
            # Process results and create domain entities
            total_listings = 0
            classified_count = 0
            
            for platform_name, listings in platform_results.items():
                for listing_data in listings:
                    try:
                        # Create listing from scraped data
                        listing = self.listing_service.create_listing_from_scrape(
                            url=listing_data.get("url", ""),
                            platform=platform_name,
                            city=city,
                            title=listing_data.get("title"),
                            description=listing_data.get("description"),
                            age=listing_data.get("age")
                        )
                        
                        total_listings += 1
                        
                        # Classify if enabled
                        if classify:
                            classification = await self.classification_service.classify_listing_async(
                                url=listing.url,
                                platform=platform_name,
                                listing_data=listing_data,
                                force_reclassify=False
                            )
                            
                            if classification and classification.is_reliable():
                                # Update listing with classification
                                self.listing_service.update_listing_classification(
                                    url=listing.url,
                                    classification_data={
                                        'confidence': classification.confidence,
                                        'alter_ok': classification.alter_ok,
                                        'einzelgaenger': classification.einzelgaenger,
                                        'freigang_noetig': classification.freigang_noetig,
                                        'alter_jahre': classification.alter_jahre,
                                        'alter_unsicher': classification.alter_unsicher,
                                        'einzelgaenger_unsicher': classification.einzelgaenger_unsicher,
                                        'freigang_unsicher': classification.freigang_unsicher,
                                        'kein_freigang_gewuenscht': classification.kein_freigang_gewuenscht
                                    }
                                )
                                classified_count += 1
                                
                    except Exception as e:
                        log.error(f"Error processing listing {listing_data.get('url')}: {e}")
                        continue
            
            result_summary = {
                "city": city,
                "platforms_scraped": list(platform_results.keys()),
                "total_listings": total_listings,
                "classified_count": classified_count,
                "timestamp": self.last_run_timestamp.isoformat()
            }
            
            log.info(f"Scraping completed: {result_summary}")
            return result_summary
            
        except Exception as e:
            log.error(f"Scraping operation failed: {e}")
            raise
        finally:
            self.running = False
    
    async def scrape_rotation(
        self,
        cities: Optional[List[str]] = None,
        max_pages: int = 3
    ) -> Dict[str, Any]:
        """Scrape multiple cities in rotation."""
        if cities is None:
            cities = self.cities
        
        results = {}
        for city in cities:
            log.info(f"Scraping city: {city}")
            city_results = await self.scrape_all_platforms_for_city(city, max_pages)
            results[city] = city_results
        
        return results
    
    def get_scraper_config(self, platform_name: str) -> Optional[Dict]:
        """Get configuration for a specific platform."""
        return self.platform_configs.get(platform_name)
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get scraping statistics per platform."""
        stats = {}
        for platform in self.get_platforms():
            try:
                count = self.listing_service.count_listings(platform=platform)
                stats[platform] = {
                    "total_listings": count,
                    "enabled": True,
                    "config": self.get_scraper_config(platform)
                }
            except Exception as e:
                log.error(f"Error getting stats for {platform}: {e}")
                stats[platform] = {"error": str(e)}
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of scraper components."""
        health = {
            "status": "unknown",
            "platforms": {},
            "cities": len(self.cities),
            "config_loaded": bool(self.platform_configs)
        }
        
        for platform in self.get_platforms():
            try:
                # Try to initialize scraper
                from modules.services.orchestrator import orchestrator
                if platform in orchestrator.scrapers:
                    health["platforms"][platform] = "ok"
                else:
                    health["platforms"][platform] = "not_initialized"
            except Exception as e:
                health["platforms"][platform] = f"error: {str(e)}"
        
        if all(v == "ok" for v in health["platforms"].values()):
            health["status"] = "healthy"
        elif health["platforms"]:
            health["status"] = "degraded"
        else:
            health["status"] = "unhealthy"
        
        return health


# Singleton instance
scraper_service = ScraperService()
