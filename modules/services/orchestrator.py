"""Orchestrator with Loop and City-Rotation for KatzenSuchApp."""

import asyncio
import time
from pathlib import Path
from typing import List, Dict
from classes.Cconfig import Config
from modules.Mhandle_log import get_logger
from modules.scraper.base import BaseScraper
from core.repositories.platform_repository import PlatformRepository
from core.services.scraper_service import scraper_service as domain_scraper_service

log = get_logger(__name__)
config = Config()


class ApplicationOrchestrator:
    """Orchestrates scraping with city rotation and platform handlers."""
    
    def __init__(self):
        self.cities = config.cities
        self.platform_repository = PlatformRepository()
        self.platform_configs = self._load_platform_configs()
        self.current_city_index = 0
        self.running = False
        self.scrapers: Dict[str, BaseScraper] = {}
        self._init_scrapers()
        
        # Initialize domain services for Repository Pattern - using Domain Layer services
        self.domain_scraper_service = domain_scraper_service
        # Services are accessed via domain_scraper_service which uses ListingService, ClassificationService
        
        # Initialize LLM filter service from Domain Layer
        from core.services.llm_filter_service import llm_filter_service as domain_llm_filter_service
        try:
            self.llm_service = domain_llm_filter_service
            log.info("LLM Filter Service from Domain Layer initialized in Orchestrator")
        except Exception as e:
            log.warning(f"LLM Filter Service not available: {e}")
            self.llm_service = None
    
    def _load_platform_configs(self) -> Dict[str, Dict]:
        """Load platform configs via Repository Pattern, fallback to Config if DB empty."""
        try:
            # Use Repository Pattern instead of direct DB access
            platform_configs = self.platform_repository.find_enabled()
            if platform_configs:
                configs = {}
                for platform_config in platform_configs:
                    configs[platform_config.platform_name] = {
                        "base_url": platform_config.base_url,
                        "listing_selector": platform_config.listing_selector,
                        "detail_selector": platform_config.detail_selector,
                        "pagination_param": platform_config.pagination_param,
                        "city_param": platform_config.city_param,
                        "enabled": platform_config.enabled,
                        "handler_class": platform_config.handler_class,
                        "login_required": platform_config.login_required
                    }
                log.info(f"Loaded {len(configs)} platform configs via Repository")
                return configs
            else:
                log.info("No DB configs found, using Config fallback")
                return config.platform_configs
        except Exception as e:
            log.error(f"Error loading configs via Repository: {e}, falling back to Config")
            return config.platform_configs
    
    def _init_scrapers(self):
        """Initialize scraper handlers from configs."""
        from modules.scraper import tierheimhelden, shelta, leipziger_land
        
        handler_map = {
            "TierheimHeldenHandler": tierheimhelden.TierheimHeldenHandler,
            "SheltaHandler": shelta.SheltaHandler,
            "LeipzigerLandHandler": leipziger_land.LeipzigerLandHandler,
        }
        
        for platform_name, platform_config in self.platform_configs.items():
            if not platform_config.get("enabled", True):
                continue
            
            handler_class_name = platform_config.get("handler_class")
            if handler_class_name in handler_map:
                handler_class = handler_map[handler_class_name]
                self.scrapers[platform_name] = handler_class(platform_name, platform_config)
                log.info(f"Initialized scraper for {platform_name}")
            else:
                log.warning(f"Unknown handler class {handler_class_name} for {platform_name}")
    
    def get_next_city(self) -> str:
        """Get next city in rotation."""
        city = self.cities[self.current_city_index]
        self.current_city_index = (self.current_city_index + 1) % len(self.cities)
        return city
    
    def get_current_city(self) -> str:
        """Get current city without advancing."""
        return self.cities[self.current_city_index]
    
    async def scrape_platform_city(self, platform_name: str, city: str, max_pages: int = 3) -> List[Dict]:
        """Scrape a single platform for a city."""
        if platform_name not in self.scrapers:
            log.warning(f"No scraper for {platform_name}")
            return []
        
        scraper = self.scrapers[platform_name]
        log.info(f"Scraping {platform_name} for city {city}")
        
        try:
            results = await scraper.scrape([city], max_pages)
            return results
        except Exception as e:
            log.error(f"Error scraping {platform_name} for {city}: {e}")
            return []
    
    async def run_once(self) -> Dict[str, List[Dict]]:
        """Run one scraping iteration for current city across all platforms."""
        city = self.get_next_city()
        log.info(f"Starting scraping iteration for city: {city}")
        
        results = {}
        tasks = []
        
        for platform_name in self.scrapers:
            tasks.append(self.scrape_platform_city(platform_name, city))
        
        scraped_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for platform_name, result in zip(self.scrapers.keys(), scraped_results):
            if isinstance(result, Exception):
                log.error(f"Scraper {platform_name} failed: {result}")
                results[platform_name] = []
            else:
                results[platform_name] = result
                log.info(f"{platform_name} found {len(result)} new listings")
        
        # Process listings with Domain Services
        if results:
            await self._process_scraped_listings(results, city)
        
        return {
            "city": city,
            "results": results,
            "timestamp": time.time()
        }
    
    async def _process_scraped_listings(self, results: Dict[str, List[Dict]], city: str) -> None:
        """Process scraped listings using Domain Services."""
        log.info(f"Processing scraped listings via Domain Layer")
        
        for platform_name, listings in results.items():
            if not listings:
                continue
            
            log.info(f"Processing {len(listings)} listings from {platform_name} via Domain Service")
            
            try:
                # Process each listing via Domain Services - ensures Repository Pattern usage
                from core.services.listing_service import ListingService
                from core.services.classification_service import ClassificationService
                from core.services.llm_filter_service import llm_filter_service
                
                listing_service = ListingService()
                classification_service = ClassificationService()
                
                processed_count = 0
                classified_count = 0
                
                for listing_data in listings:
                    url = listing_data.get("url")
                    if not url:
                        continue
                    
                    try:
                        # Check if listing already exists via Repository
                        if listing_service.exists(url, platform_name):
                            log.debug(f"Listing already exists: {url}")
                            continue
                        
                        # Create listing via Domain Service (uses ListingRepository)
                        listing = listing_service.create_listing_from_scrape(
                            url=url,
                            platform=platform_name,
                            city=city,
                            title=listing_data.get("title"),
                            description=listing_data.get("description"),
                            age=listing_data.get("age")
                        )
                        
                        processed_count += 1
                        
                        # Classify via Domain Services
                        try:
                            classification = await classification_service.classify_listing_async(
                                url=url,
                                platform=platform_name,
                                listing_data=listing_data
                            )
                            
                            if classification and classification.is_reliable():
                                # Update listing with classification
                                listing_service.update_listing_classification(
                                    url=url,
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
                                
                                if classification.is_reliable(min_confidence=0.7):
                                    classified_count += 1
                        
                        except Exception as e:
                            log.error(f"Classification failed for {url}: {e}")
                    
                    except Exception as e:
                        log.error(f"Error processing listing {url}: {e}")
                        continue
                
                log.info(f"{platform_name}: Processed {processed_count} listings, {classified_count} classified")
                
            except Exception as e:
                log.error(f"Error processing {platform_name}: {e}")
                continue
    
    async def run_loop(self, interval_minutes: int = None):
        """Main loop with city rotation."""
        if interval_minutes is None:
            interval_minutes = config.scraper_interval_minutes
        
        self.running = True
        log.info(f"Starting orchestrator loop with {interval_minutes} minute intervals")
        log.info(f"Cities rotation: {', '.join(self.cities)}")
        log.info(f"Platforms: {', '.join(self.scrapers.keys())}")
        
        while self.running:
            try:
                iteration_result = await self.run_once()
                
                # Log summary
                total_new = sum(len(listings) for listings in iteration_result["results"].values())
                log.info(f"Iteration complete for {iteration_result['city']}: {total_new} new listings")
                
                if not self.running:
                    break
                
                log.info(f"Next run in {interval_minutes} minutes")
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                log.error(f"Orchestrator loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop(self):
        """Stop the orchestrator loop."""
        self.running = False
        log.info("Orchestrator stopped")
    
    def get_status(self) -> Dict:
        """Get current orchestrator status."""
        return {
            "running": self.running,
            "current_city": self.get_current_city(),
            "cities": self.cities,
            "current_city_index": self.current_city_index,
            "platforms": list(self.scrapers.keys()),
            "scraper_interval_minutes": config.scraper_interval_minutes,
        }


# Global orchestrator instance
orchestrator = ApplicationOrchestrator()


async def main():
    """Entry point for orchestrator."""
    await orchestrator.run_loop()


if __name__ == "__main__":
    asyncio.run(main())
