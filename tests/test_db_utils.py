"""
Tests for Core DB Utils
Tests DB initialization, is_known, save_url, cache_llm_classification etc.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_init_db_creates_tables(temp_db):
    """Test DB initialization creates all tables."""
    from modules.db_utils import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    
    expected = ['platforms', 'seen_urls', 'configs', 'scraper_configs', 
                'feature_requests', 'scraped_listings', 'llm_classification', 'ratings']
    for table in expected:
        assert table in tables, f"Table {table} missing"
    print("✓ DB initialization works")


def test_is_known_save_url(temp_db):
    """Test is_known and save_url."""
    from modules.db_utils import is_known, save_url
    url = "https://example.com/cat/1_test_is_known"
    platform = "test_platform_is_known"
    
    assert not is_known(url, platform)
    
    save_url(url, platform)
    assert is_known(url, platform)
    
    # Duplicate save should not error
    save_url(url, platform)
    assert is_known(url, platform)
    print("✓ is_known / save_url works")


def test_mark_processed(temp_db):
    """Test mark_processed updates processed flag."""
    from modules.db_utils import save_url, mark_processed, get_connection
    url = "https://example.com/cat/2"
    platform = "test_platform"
    
    save_url(url, platform)
    mark_processed(url, platform, processed=True)
    
    # Verify via direct query
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT processed FROM seen_urls WHERE url=? AND platform=?", (url, platform))
    row = cur.fetchone()
    conn.close()
    assert row['processed'] == 1
    print("✓ mark_processed works")


def test_scraper_configs_crud(temp_db):
    """Test scraper config CRUD."""
    from modules.db_utils import add_scraper_config, get_scraper_configs
    platform_name = "test_platform_unique"
    add_scraper_config(
        platform_name=platform_name,
        base_url="https://test.com",
        listing_selector=".listing",
        detail_selector=".detail",
        pagination_param="page",
        city_param="city",
        enabled=1,
        handler_class="TestHandler",
        login_required=0
    )
    
    configs = get_scraper_configs()
    assert len(configs) >= 1
    # Find our config
    found = False
    for cfg in configs:
        if cfg[1] == platform_name:
            assert cfg[2] == "https://test.com"
            assert cfg[8] == "TestHandler"
            found = True
            break
    assert found, f"Config for {platform_name} not found"
    print("✓ Scraper config CRUD works")


def test_feature_request_crud(temp_db):
    """Test feature request CRUD."""
    from modules.db_utils import add_feature_request, get_feature_requests
    platform_name = "test_platform_unique_2"
    add_feature_request(
        platform_name=platform_name,
        start_url="https://start.com",
        example_listing_url="https://example.com/1",
        description="Test request unique",
        created_by="tester"
    )
    
    requests = get_feature_requests()
    assert len(requests) >= 1
    # Find our request
    found = False
    for req in requests:
        if req['platform_name'] == platform_name:
            assert req['description'] == "Test request unique"
            assert req['status'] == 'open'
            found = True
            break
    assert found, f"Feature request for {platform_name} not found"
    
    # Filter by status
    open_reqs = get_feature_requests(status='open')
    assert len(open_reqs) >= 1
    print("✓ Feature request CRUD works")


def test_save_scraped_listing(temp_db):
    """Test save_scraped_listing."""
    from modules.db_utils import save_scraped_listing, get_scraped_listings
    save_scraped_listing(
        url="https://example.com/cat/3",
        platform="test_platform",
        city="Berlin",
        title="Mia",
        description="Süße Katze",
        age=3
    )
    
    listings = get_scraped_listings(limit=10)
    assert len(listings) >= 1
    lst = listings[0]
    assert lst['url'] == "https://example.com/cat/3"
    assert lst['platform'] == "test_platform"
    assert lst['city'] == "Berlin"
    assert lst['title'] == "Mia"
    assert lst['age'] == 3
    print("✓ Scraped listing save works")


def test_cache_and_get_llm_classification(temp_db):
    """Test LLM classification cache."""
    from modules.db_utils import cache_llm_classification, get_llm_classification
    url = "https://example.com/cat/4"
    platform = "test_platform"
    result = {
        "alter_ok": True,
        "alter_jahre": 4,
        "alter_unsicher": False,
        "einzelgaenger": True,
        "einzelgaenger_unsicher": False,
        "freigang_noetig": False,
        "freigang_unsicher": False,
        "kein_freigang_gewuenscht": False,
        "confidence": 0.92,
        "reason": "Test classification"
    }
    
    cache_llm_classification(url, platform, result)
    cached = get_llm_classification(url)
    
    assert cached is not None
    assert cached['url'] == url
    assert cached['platform'] == platform
    assert cached['alter_ok'] == 1
    assert cached['alter_jahre'] == 4
    assert abs(cached['confidence'] - 0.92) < 0.001
    print("✓ LLM classification cache works")


def test_get_scraped_listings_with_processed_filter(temp_db):
    """Test filtered listing retrieval."""
    from modules.db_utils import save_scraped_listing, get_scraped_listings
    save_scraped_listing(url="https://example.com/cat/a", platform="p", city="A", title="A", description="a", age=1)
    save_scraped_listing(url="https://example.com/cat/b", platform="p", city="B", title="B", description="b", age=2)
    
    all_listings = get_scraped_listings(limit=10)
    assert len(all_listings) >= 2
    
    # Test processed filter
    unprocessed = get_scraped_listings(limit=10, processed=0)
    assert len(unprocessed) >= 2
    print("✓ Scraped listings filter works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
