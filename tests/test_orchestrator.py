"""
Tests for Orchestrator Core Logic
Tests city rotation, platform loading, run_once flow
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def orchestrator(temp_db):
    with patch('classes.Cconfig.Config') as mock_cfg:
        from tests.conftest import _make_mock_config
        from pathlib import Path as _P
        mock_cfg.return_value = _make_mock_config(_P(temp_db))
        if 'modules.services.orchestrator' in sys.modules:
            del sys.modules['modules.services.orchestrator']
        from modules.services.orchestrator import ApplicationOrchestrator
        orch = ApplicationOrchestrator()
        yield orch


def test_load_platform_configs(orchestrator):
    """Test platform config loading."""
    configs = orchestrator._load_platform_configs()
    assert isinstance(configs, dict)
    print(f"✓ Platform configs loaded: {len(configs)} platforms")


def test_city_rotation(orchestrator):
    """Test city rotation logic."""
    # Reset index for deterministic test
    orchestrator.current_city_index = 0
    
    # First city
    city1 = orchestrator.get_next_city()
    assert city1 == "Berlin"
    
    # Second city
    city2 = orchestrator.get_next_city()
    assert city2 == "Hamburg"
    
    # Current city should be next in rotation (München) as index advanced after get_next_city
    current = orchestrator.get_current_city()
    assert current == "München"
    print(f"✓ City rotation works: {city1} -> {city2}, next = {current}")


def test_init_scrapers(orchestrator):
    """Test scraper initialization."""
    # _init_scrapers initializes scrapers dict, returns None
    result = orchestrator._init_scrapers()
    assert result is None
    assert isinstance(orchestrator.scrapers, dict)
    print(f"✓ Scrapers initialized: {len(orchestrator.scrapers)} scrapers")


def test_scrape_platform_city(orchestrator):
    """Test scrape_platform_city with mocked scraper."""
    import asyncio
    # Setup a mock scraper
    mock_scraper = MagicMock()
    mock_scraper.scrape = AsyncMock(return_value=[
        {'url': 'https://test.com/cat/1', 'title': 'Test'},
        {'url': 'https://test.com/cat/2', 'title': 'Test2'}
    ])
    orchestrator.scrapers['test_platform'] = mock_scraper
    
    async def run():
        return await orchestrator.scrape_platform_city('test_platform', 'Berlin', max_pages=1)
    
    results = asyncio.run(run())
    
    assert len(results) == 2
    mock_scraper.scrape.assert_called_once_with(['Berlin'], 1)
    print("✓ Scrape platform city works")


def test_get_status(orchestrator):
    """Test status retrieval."""
    status = orchestrator.get_status()
    assert 'running' in status
    assert 'current_city' in status
    assert 'platforms' in status
    assert 'cities' in status
    assert 'current_city_index' in status
    assert 'scraper_interval_minutes' in status
    print(f"✓ Status retrieval works: {status}")


def test_process_scraped_listings(orchestrator, temp_db):
    """Test processing scraped listings."""
    import asyncio
    results = {
        'platform1': [
            {'url': 'https://test.com/cat/1', 'title': 'Test1'},
            {'url': 'https://test.com/cat/2', 'title': 'Test2'}
        ]
    }
    
    # Mock listing service
    from unittest.mock import patch
    async def run():
        with patch('core.services.listing_service.ListingService') as mock_listing_service:
            mock_service_instance = MagicMock()
            mock_service_instance.exists.return_value = False
            mock_listing = MagicMock()
            mock_service_instance.create_listing_from_scrape.return_value = mock_listing
            mock_listing_service.return_value = mock_service_instance
            
            with patch('core.services.classification_service.ClassificationService') as mock_class_service:
                mock_class_instance = MagicMock()
                mock_classification = MagicMock()
                mock_classification.is_reliable.return_value = True
                mock_classification.confidence = 0.9
                mock_classification.alter_ok = True
                mock_classification.einzelgaenger = False
                mock_classification.freigang_noetig = False
                mock_classification.alter_jahre = 4
                mock_classification.alter_unsicher = False
                mock_classification.einzelgaenger_unsicher = False
                mock_classification.freigang_unsicher = False
                mock_classification.kein_freigang_gewuenscht = True
                mock_class_instance.classify_listing_async = AsyncMock(return_value=mock_classification)
                mock_class_service.return_value = mock_class_instance
                
                # Run processing
                await orchestrator._process_scraped_listings(results, 'Berlin')
                
                # Verify listing service was called
                assert mock_service_instance.create_listing_from_scrape.call_count == 2
    
    asyncio.run(run())
    print("✓ Process scraped listings works")


def test_orchestrator_init(orchestrator):
    """Test orchestrator initializes correctly."""
    assert orchestrator.cities is not None
    assert len(orchestrator.cities) > 0
    assert hasattr(orchestrator, 'current_city_index')
    print("✓ Orchestrator initialization works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
