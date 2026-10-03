"""
Integration test for happy path: Scraping → LLM → DB

Tests the complete flow from scraper to LLM classification to database persistence.
Uses mocks for Playwright browser and Ollama API to avoid external dependencies.
"""

import asyncio
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_utils import init_db, get_connection, save_scraped_listing, cache_llm_classification, get_llm_classification


class FakePage:
    """Mock Playwright page for testing."""
    
    def __init__(self, url="", listings=None, detail_data=None):
        self.url = url
        self.listings = listings or []
        self.detail_data = detail_data or {}
        self._closed = False
    
    async def goto(self, url, wait_until="domcontentloaded", timeout=30000):
        self.url = url
        return True
    
    async def wait_for_timeout(self, ms):
        pass
    
    async def query_selector_all(self, selector):
        # Return mock listing elements
        elements = []
        for listing_url in self.listings:
            el = Mock()
            el.get_attribute = AsyncMock(return_value=listing_url)
            elements.append(el)
        return elements
    
    async def query_selector(self, selector):
        # Return mock element for detail extraction
        if self.detail_data:
            el = Mock()
            el.inner_text = AsyncMock(return_value=self.detail_data.get("title", ""))
            return el
        return None
    
    async def close(self):
        self._closed = True


class FakeContext:
    async def close(self):
        pass


class TestScraper:
    """Test scraper with mocked extraction - standalone to avoid Playwright init."""
    
    def __init__(self, platform_name, scraper_config):
        self.platform_name = platform_name
        self.config = scraper_config
        self.logger = Mock()
        self.logger.info = Mock()
        self.logger.debug = Mock()
        self.logger.error = Mock()
    
    def _build_url(self, city=None, page=1):
        from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
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
    
    async def extract_listings(self, page, listing_selector):
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
    
    async def extract_detail(self, page):
        return {
            "title": "Test Katze, 5 Jahre, Wohnungskatze",
            "description": "Schöne Katze, 5 Jahre alt, Einzelgänger geeignet, kein Freigang gewünscht",
            "age": 5
        }
    
    async def scrape_city_page(self, city, page_num, mock_pm):
        url = self._build_url(city, page_num)
        self.logger.info(f"Scraping {self.platform_name} - {url}")
        
        page, context = await mock_pm.new_context_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            listing_selector = self.config.get("listing_selector", "")
            urls = await self.extract_listings(page, listing_selector)
            
            results = []
            for url in urls:
                detail_page, detail_context = await mock_pm.new_context_page()
                try:
                    await detail_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await detail_page.wait_for_timeout(1500)
                    
                    detail = await self.extract_detail(detail_page)
                    detail["url"] = url
                    detail["platform"] = self.platform_name
                    detail["city"] = city
                    
                    # Save scraped details to DB
                    from modules.db_utils import save_scraped_listing
                    try:
                        save_scraped_listing(
                            url=url,
                            platform=self.platform_name,
                            city=city,
                            title=detail.get("title", ""),
                            description=detail.get("description", ""),
                            age=detail.get("age")
                        )
                        self.logger.debug(f"Saved scraped listing to DB: {url}")
                    except Exception as e:
                        self.logger.error(f"Error saving scraped listing to DB: {e}")
                    
                    results.append(detail)
                    
                except Exception as e:
                    self.logger.error(f"Error extracting detail from {url}: {e}")
                finally:
                    await mock_pm.close_page(detail_page)
                    await detail_context.close()
            
            await mock_pm.close_page(page)
            return results
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            await mock_pm.close_page(page)
            return []
        finally:
            await context.close()


async def test_happy_path_scraping_llm_db():
    """Test happy path: Scraper extracts → LLM classifies → DB persists."""
    
    print("=== Integration Test: Scraping → LLM → DB ===")
    
    # Setup temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_KatzenSuchApp.db"
        auth_db_path = str(Path(tmpdir) / "auth.db")
        
        # Create mock config object before importing modules that use it
        class MockConfig:
            def __init__(self):
                self.db_path = str(db_path)
                self.auth_db_path = auth_db_path
                self.ollama_url = "http://fake-ollama:11434/api/chat"
                self.ollama_model = "test-model"
                self.ollama_timeout = 30
                self.log_level = "INFO"
                self.cities = ["Berlin", "Hamburg"]
                self.scraper_interval_minutes = 15
                self.platform_configs = {
                    "test_platform": {
                        "base_url": "https://test.example.com",
                        "listing_selector": "a.listing",
                        "detail_selector": "div.detail",
                        "pagination_param": "page",
                        "city_param": "city",
                        "enabled": True,
                        "handler_class": "TestScraper"
                    }
                }
                self.filter_criteria = {
                    "alter_min": 2,
                    "alter_max": 8,
                    "einzelgaenger": True,
                    "kein_freigang_noetig": True
                }
        
        mock_config = MockConfig()
        
        # Patch Config before importing anything that uses it
        with patch('classes.Cconfig.Config', return_value=mock_config):
            # Now import modules
            from modules.db_utils import init_db, get_connection
            from core.services.llm_filter_service import LLMFilterService
            
            # Initialize DB
            init_db()
            print(f"✓ Database initialized at {db_path}")
            
            # Test data
            test_url = "https://test.example.com/listing/123"
            test_city = "Berlin"
            test_platform = "test_platform"
            
            # Create mock Playwright manager
            mock_pm = Mock()
            mock_pm.start = AsyncMock()
            mock_pm.close_page = AsyncMock()
            
            # Setup mock page and context for listing page
            listing_page = FakePage(
                url="https://test.example.com/listings?city=Berlin&page=1",
                listings=[test_url]
            )
            listing_context = FakeContext()
            
            # Setup mock page and context for detail page
            detail_page = FakePage(url=test_url)
            detail_context = FakeContext()
            
            call_count = [0]
            async def new_context_page_side_effect(**kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # Listing page
                    return listing_page, listing_context
                else:
                    # Detail page
                    return detail_page, detail_context
            
            mock_pm.new_context_page = AsyncMock(side_effect=new_context_page_side_effect)
            
            # Create test scraper
            scraper = TestScraper(
                platform_name=test_platform,
                scraper_config={
                    "base_url": "https://test.example.com",
                    "listing_selector": "a.listing",
                    "detail_selector": "div.detail",
                    "pagination_param": "page",
                    "city_param": "city",
                    "enabled": True,
                    "handler_class": "TestScraper"
                }
            )
            
            # Test scraping
            print("→ Running scraper...")
            results = await scraper.scrape_city_page(test_city, 1, mock_pm)
            
            assert len(results) == 1, f"Expected 1 result, got {len(results)}"
            result = results[0]
            assert result["url"] == test_url
            assert result["platform"] == test_platform
            assert result["city"] == test_city
            print(f"✓ Scraper extracted listing: {result['title']}")
            
            # Verify DB persistence
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM scraped_listings WHERE url = ?", (test_url,))
            db_row = cur.fetchone()
            assert db_row is not None, "Listing not saved to DB"
            assert db_row["title"] == "Test Katze, 5 Jahre, Wohnungskatze"
            assert db_row["age"] == 5
            conn.close()
            print("✓ Scraped listing persisted to DB")
            
            # Mock Ollama response
            mock_ollama_response = {
                "is_match": True,
                "confidence": 0.85,
                "reasoning": "Katze passt zu Kriterien: Alter 5 Jahre, Einzelgänger geeignet, kein Freigang",
                "age_ok": True,
                "einzelgaenger_ok": True,
                "freigang_ok": True,
                "age_unsicher": False,
                "einzelgaenger_unsicher": False,
                "freigang_unsicher": False
            }
            
            # Test LLM classification
            llm_service = LLMFilterService()
            
            # Ensure cache is empty for this test
            with patch.object(llm_service, '_get_cached_classification', return_value=None):
                with patch.object(llm_service, '_query_ollama', return_value=mock_ollama_response):
                    print("→ Running LLM classification...")
                    classification = await llm_service.classify_listing(
                        url=test_url,
                        listing=result,
                        platform=test_platform
                    )
                    
                    assert classification.is_match is True
                    assert classification.confidence == 0.85
                    assert classification.age_ok is True
                    print(f"✓ LLM classification: match={classification.is_match}, confidence={classification.confidence}")
            
            # Verify LLM result cached in DB (check via raw DB query)
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT confidence, url_hash FROM llm_classification WHERE url = ?", (test_url,))
            llm_row = cur.fetchone()
            assert llm_row is not None, "LLM classification not cached in DB"
            assert llm_row["confidence"] == 0.85
            assert llm_row["url_hash"] is not None
            conn.close()
            print("✓ LLM classification cached in DB")
            
            print("\n=== All tests passed! Happy path works correctly ===")
            print(f"Scraping → LLM → DB integration verified")
            print(f"Results: Scraped {len(results)} listing(s), LLM classified with confidence {classification.confidence}")


if __name__ == "__main__":
    asyncio.run(test_happy_path_scraping_llm_db())
