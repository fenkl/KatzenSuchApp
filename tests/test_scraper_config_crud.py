"""
Tests for Scraper Config CRUD
Tests CRUD operations for Platform Configs via Service Layer
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.domain.config import PlatformConfig
from core.services.platform_service import PlatformService


@pytest.fixture
def mock_config():
    """Mock config with temporary DB."""
    class MockConfig:
        def __init__(self):
            self.db_path = tempfile.mktemp(suffix='.db')
            self.auth_db_path = tempfile.mktemp(suffix='.db')
            self.ollama_url = "http://fake:11434"
            self.ollama_model = "test"
            self.log_level = "INFO"
            self.cities = []
            self.scraper_interval_minutes = 15
            self.platform_configs = {}
            self.filter_criteria = {}
    
    return MockConfig()


@pytest.fixture
def platform_service(mock_config):
    """Create PlatformService with mocked DB."""
    with patch('classes.Cconfig.Config', return_value=mock_config):
        from modules.db_utils import init_db
        
        # Initialize DB
        init_db()
        
        # Ensure scraper_configs table has unique constraint
        from modules.db_utils import get_connection
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Recreate table with unique constraint to avoid duplicate issues
            cur.execute("DROP TABLE IF EXISTS scraper_configs")
            cur.execute("""
                CREATE TABLE scraper_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT NOT NULL UNIQUE,
                    base_url TEXT,
                    listing_selector TEXT,
                    detail_selector TEXT,
                    pagination_param TEXT,
                    city_param TEXT,
                    enabled INTEGER DEFAULT 1,
                    handler_class TEXT,
                    login_required INTEGER DEFAULT 0
                )
            """)
            conn.commit()
        finally:
            conn.close()
        
        # Create service
        service = PlatformService()
        
        yield service


def test_platform_config_create(platform_service):
    """Test creating platform config."""
    config = PlatformConfig(
        platform_name="test_platform",
        base_url="https://example.com",
        listing_selector="div.listing",
        detail_selector="div.detail",
        pagination_param="page",
        city_param="city",
        enabled=True,
        handler_class="TestHandler",
        login_required=False
    )
    
    result = platform_service.create_config(config)
    
    assert result is True
    
    # Verify it was created
    retrieved = platform_service.get_config("test_platform")
    assert retrieved is not None
    assert retrieved["platform_name"] == "test_platform"
    assert retrieved["base_url"] == "https://example.com"
    assert retrieved["enabled"] is True
    print("✓ Platform config creation works")


def test_platform_config_save_update(platform_service):
    """Test saving/updating platform config."""
    config = PlatformConfig(
        platform_name="test_platform_update",
        base_url="https://example.com",
        listing_selector="div.listing",
        enabled=True,
        handler_class="TestHandler"
    )
    
    # Create
    platform_service.save_config(config)
    
    # Update
    config.base_url = "https://updated.com"
    config.enabled = False
    platform_service.save_config(config)
    
    retrieved = platform_service.get_config("test_platform_update")
    assert retrieved is not None
    assert retrieved["base_url"] == "https://updated.com"
    assert retrieved["enabled"] is False
    print("✓ Platform config update works")


def test_platform_config_get_by_name(platform_service):
    """Test retrieving platform config by name."""
    config = PlatformConfig(
        platform_name="test_platform_get",
        base_url="https://get.example.com",
        listing_selector="div.listing"
    )
    
    platform_service.save_config(config)
    
    retrieved = platform_service.get_config("test_platform_get")
    
    assert retrieved is not None
    assert retrieved["platform_name"] == "test_platform_get"
    assert retrieved["base_url"] == "https://get.example.com"
    print("✓ Platform config retrieval works")


def test_platform_config_get_all(platform_service):
    """Test retrieving all platform configs."""
    # Create multiple configs
    for i in range(3):
        config = PlatformConfig(
            platform_name=f"test_platform_all_{i}",
            base_url=f"https://example{i}.com",
            enabled=True if i % 2 == 0 else False
        )
        platform_service.save_config(config)
    
    all_configs = platform_service.get_all_configs()
    
    # Should have at least 3 test configs
    test_configs = [c for c in all_configs if c["platform_name"].startswith("test_platform_all_")]
    assert len(test_configs) >= 3
    print(f"✓ Retrieved {len(all_configs)} platform configs, {len(test_configs)} test configs")


def test_platform_config_delete(platform_service):
    """Test deleting platform config."""
    config = PlatformConfig(
        platform_name="test_platform_delete",
        base_url="https://delete.com",
        enabled=True
    )
    
    platform_service.save_config(config)
    
    # Verify exists
    retrieved = platform_service.get_config("test_platform_delete")
    assert retrieved is not None
    
    # Delete
    deleted = platform_service.delete_config("test_platform_delete")
    assert deleted is True
    
    # Verify deletion
    retrieved = platform_service.get_config("test_platform_delete")
    assert retrieved is None
    print("✓ Platform config deletion works")


def test_platform_config_update_fields(platform_service):
    """Test updating specific fields."""
    config = PlatformConfig(
        platform_name="test_platform_fields",
        base_url="https://original.com",
        listing_selector="div.original",
        enabled=True
    )
    
    platform_service.save_config(config)
    
    # Update specific fields
    updates = {
        "base_url": "https://updated.com",
        "listing_selector": "div.updated",
        "enabled": False
    }
    
    result = platform_service.update_config("test_platform_fields", updates)
    
    assert result is True
    
    retrieved = platform_service.get_config("test_platform_fields")
    assert retrieved["base_url"] == "https://updated.com"
    assert retrieved["listing_selector"] == "div.updated"
    assert retrieved["enabled"] is False
    print("✓ Platform config field updates work")


def test_platform_config_enabled_filter(platform_service):
    """Test filtering enabled platforms."""
    # Create enabled and disabled configs
    enabled_config = PlatformConfig(
        platform_name="test_platform_enabled",
        base_url="https://enabled.com",
        enabled=True
    )
    disabled_config = PlatformConfig(
        platform_name="test_platform_disabled",
        base_url="https://disabled.com",
        enabled=False
    )
    
    platform_service.save_config(enabled_config)
    platform_service.save_config(disabled_config)
    
    enabled_platforms = platform_service.get_enabled_platforms()
    
    enabled_names = [p.platform_name for p in enabled_platforms]
    assert "test_platform_enabled" in enabled_names
    assert "test_platform_disabled" not in enabled_names
    print("✓ Enabled platform filtering works")


def test_platform_config_domain_entity():
    """Test PlatformConfig domain entity."""
    config = PlatformConfig(
        platform_name="domain_test_platform",
        base_url="https://example.com",
        listing_selector="div.listing",
        detail_selector="div.detail",
        enabled=True,
        handler_class="TestHandler"
    )
    
    assert config.is_enabled() is True
    assert config.can_scrape() is True
    
    # Test serialization with enabled=True
    data = config.to_dict()
    assert data["platform_name"] == "domain_test_platform"
    assert data["base_url"] == "https://example.com"
    assert data["enabled"] is True
    
    # Test deserialization preserves enabled
    restored = PlatformConfig.from_dict(data)
    assert restored.platform_name == "domain_test_platform"
    assert restored.enabled is True
    
    # Test with disabled
    config.enabled = False
    assert config.is_enabled() is False
    assert config.can_scrape() is False
    
    data_disabled = config.to_dict()
    restored_disabled = PlatformConfig.from_dict(data_disabled)
    assert restored_disabled.enabled is False
    
    print("✓ PlatformConfig domain entity works")


def test_platform_config_count(platform_service):
    """Test counting platform configs."""
    # Create configs
    for i in range(5):
        config = PlatformConfig(
            platform_name=f"test_platform_count_{i}",
            base_url=f"https://count{i}.com",
            enabled=True if i % 2 == 0 else False
        )
        platform_service.save_config(config)
    
    total_count = platform_service.count_configs()
    
    assert total_count >= 5
    print(f"✓ Platform config count works: {total_count} total")


def test_platform_config_exists(platform_service):
    """Test checking if platform config exists."""
    config = PlatformConfig(
        platform_name="test_platform_exists",
        base_url="https://exists.com"
    )
    
    # Should not exist yet
    repo = platform_service.repository
    assert not repo.exists("test_platform_exists")
    
    # Create
    platform_service.save_config(config)
    assert repo.exists("test_platform_exists")
    
    print("✓ Platform config existence check works")


def test_platform_config_bulk_save(platform_service):
    """Test bulk saving platform configs."""
    configs = [
        PlatformConfig(
            platform_name=f"bulk_test_{i}",
            base_url=f"https://bulk{i}.com",
            enabled=True
        )
        for i in range(5)
    ]
    
    repo = platform_service.repository
    repo.bulk_save(configs)
    
    # Verify all were saved
    for i in range(5):
        retrieved = platform_service.get_config(f"bulk_test_{i}")
        assert retrieved is not None
        assert retrieved["base_url"] == f"https://bulk{i}.com"
    
    print("✓ Platform config bulk save works")


def test_platform_config_with_login_required(platform_service):
    """Test platform config with login required flag."""
    config = PlatformConfig(
        platform_name="test_platform_login",
        base_url="https://login.example.com",
        listing_selector="div.listing",
        login_required=True,
        enabled=True
    )
    
    platform_service.save_config(config)
    
    retrieved = platform_service.get_config("test_platform_login")
    assert retrieved is not None
    assert retrieved["login_required"] is True
    print("✓ Platform config with login required works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
