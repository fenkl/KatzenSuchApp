"""Base Scraper for KatzenSuchApp."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import hashlib
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from modules.playwright_browser import PlaywrightManager
from core.services.listing_service import ListingService
from classes.Cconfig import Config
from modules.Mhandle_log import get_logger

config = Config()
log = get_logger(__name__)

class BaseScraper(ABC):
    """Basis-Klasse für alle Scraper."""

    def __init__(self, platform_name: str, scraper_config: Dict):
        self.platform_name = platform_name
        self.config = scraper_config
        self.pm = PlaywrightManager()
        self.logger = log
        self.listing_service = ListingService()

    def _build_url(self, city: Optional[str] = None, page: int = 1) -> str:
        base_url = self.config.get("base_url", "")
        pagination_param = self.config.get("pagination_param")
        city_param = self.config.get("city_param")
        
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        if pagination_param:
            query_params[pagination_param] = [str(page)]
        
        if city_param and city:
            query_params[city_param] = [city]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return new_url

    def is_known(self, url: str) -> bool:
        return self.listing_service.exists(url, self.platform_name)

    def save_url(self, url: str):
        # URL saving is now handled via listing_service in process flow
        pass

    async def extract_listings(self, page, listing_selector: str) -> List[str]:
        listings = await page.query_selector_all(listing_selector)
        urls = []
        for el in listings:
            href = await el.get_attribute("href")
            if href:
                if href.startswith("http"):
                    urls.append(href)
                else:
                    base = page.url
                    urls.append(base.rstrip("/") + "/" + href.lstrip("/"))
        return urls

    @abstractmethod
    async def extract_detail(self, page) -> Dict:
        """Extract detail information from listing page."""
        pass

    async def scrape_city_page(self, city: Optional[str], page_num: int) -> List[Dict]:
        await self.pm.start()
        url = self._build_url(city, page_num)
        self.logger.info(f"Scraping {self.platform_name} - {url}")
        
        page, context = await self.pm.new_context_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            listing_selector = self.config.get("listing_selector", "")
            urls = await self.extract_listings(page, listing_selector)
            
            results = []
            for url in urls:
                if self.is_known(url):
                    self.logger.debug(f"Already known: {url}")
                    continue
                
                detail_page, detail_context = await self.pm.new_context_page()
                try:
                    await detail_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await detail_page.wait_for_timeout(1500)
                    
                    detail = await self.extract_detail(detail_page)
                    detail["url"] = url
                    detail["platform"] = self.platform_name
                    detail["city"] = city
                    
                    # Note: Direct DB saving removed - listings will be processed via Domain Service
                    # save_scraped_listing moved to listing_service.create_listing_from_scrape
                    # This allows Repository Pattern and Domain Layer processing
                    
                    results.append(detail)
                    
                except Exception as e:
                    self.logger.error(f"Error extracting detail from {url}: {e}")
                finally:
                    await self.pm.close_page(detail_page)
                    try:
                        await detail_context.close()
                    except:
                        pass
            
            await self.pm.close_page(page)
            return results
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            await self.pm.close_page(page)
            return []
        finally:
            try:
                await context.close()
            except:
                pass

    async def scrape(self, cities: List[str], max_pages: int = 5) -> List[Dict]:
        """Execute scraping for multiple cities. Handles city parameter consistently based on config."""
        results = []
        city_param = self.config.get("city_param")
        
        # Determine cities to iterate based on whether platform supports city filtering
        if city_param:
            # Platform supports city filtering - iterate over provided cities
            city_iter = cities if cities else [None]
            self.logger.debug(f"{self.platform_name}: iterating over cities {city_iter}")
        else:
            # Platform does not support city filtering - scrape once with city=None
            city_iter = [None]
            if cities:
                self.logger.debug(f"{self.platform_name}: city_param not configured, ignoring cities {cities}")
        
        for city in city_iter:
            for page_num in range(1, max_pages + 1):
                page_results = await self.scrape_city_page(city, page_num)
                results.extend(page_results)
        
        return results

    def pre_filter(self, data: Dict) -> bool:
        """Deterministischer Pre-Filter."""
        title = data.get("title", "").lower()
        description = data.get("description", "").lower()
        
        # Alter check
        alter_ok = True
        alter_jahre = None
        
        # Simple age extraction - can be improved
        age_match = re.search(r'(\d+)\s*jahr', description + " " + title)
        if age_match:
            alter_jahre = int(age_match.group(1))
            if alter_jahre < config.filter_criteria["alter_min"] or alter_jahre > config.filter_criteria["alter_max"]:
                alter_ok = False
        
        # Einzelgänger check
        einzelgaenger = "einzelgänger" in description or "einsam" in description
        einzelgaenger_unsicher = True
        
        # Freigang check
        freigang_noetig = "freigang" in description or "draußen" in description
        freigang_unsicher = True
        
        data.update({
            "alter_ok": alter_ok,
            "alter_jahre": alter_jahre,
            "alter_unsicher": alter_jahre is None,
            "einzelgaenger": einzelgaenger,
            "einzelgaenger_unsicher": not einzelgaenger,
            "freigang_noetig": freigang_noetig,
            "freigang_unsicher": True,
            "kein_freigang_gewuenscht": not freigang_noetig
        })
        
        # Pre-filter pass if age is definitive
        if alter_jahre is not None and not alter_ok:
            return False
        
        return True
