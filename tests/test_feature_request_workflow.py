"""
Tests for Feature Request Workflow
Tests CRUD operations for Feature Requests via Service Layer
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.domain.feature_request import FeatureRequest
from api.models.schemas import FeatureRequestCreate, FeatureRequestUpdate


@pytest.fixture
def feature_request_service(temp_db):
    """Create FeatureRequestService with mocked DB."""
    with patch('classes.Cconfig.Config'):
        from core.services.feature_request_service import FeatureRequestService
        service = FeatureRequestService()
        
        # Clean up test data
        repo = service.repository
        if repo.exists(1):
            repo.delete_by_id(1)
        
        yield service


def test_feature_request_create(feature_request_service):
    """Test creating a feature request."""
    create_data = FeatureRequestCreate(
        platform_name="test_platform",
        start_url="https://example.com",
        example_listing_url="https://example.com/listing/1",
        description="Test feature request",
        created_by="test_user"
    )
    
    result = feature_request_service.create_request(create_data, created_by="test_user")
    
    assert result is not None
    assert result.platform_name == "test_platform"
    assert result.start_url == "https://example.com"
    assert result.description == "Test feature request"
    assert result.created_by == "test_user"
    assert result.status == "open"
    assert result.id is not None
    print("✓ Feature request creation works")


def test_feature_request_get_by_id(feature_request_service):
    """Test retrieving feature request by ID."""
    # First create one
    create_data = FeatureRequestCreate(
        platform_name="test_platform2",
        start_url="https://example2.com",
        description="Test get",
        created_by="test_user"
    )
    
    created = feature_request_service.create_request(create_data)
    request_id = created.id
    
    # Retrieve it
    retrieved = feature_request_service.get_request(request_id)
    
    assert retrieved is not None
    assert retrieved.id == request_id
    assert retrieved.platform_name == "test_platform2"
    print("✓ Feature request retrieval works")


def test_feature_request_update(feature_request_service):
    """Test updating feature request."""
    # Create
    create_data = FeatureRequestCreate(
        platform_name="test_platform3",
        start_url="https://example3.com",
        description="Original description",
        created_by="test_user"
    )
    
    created = feature_request_service.create_request(create_data)
    request_id = created.id
    
    # Update
    update_data = FeatureRequestUpdate(
        status="in_progress",
        description="Updated description"
    )
    
    updated = feature_request_service.update_request(request_id, update_data)
    
    assert updated is not None
    assert updated.status == "in_progress"
    assert updated.description == "Updated description"
    print("✓ Feature request update works")


def test_feature_request_get_all(feature_request_service):
    """Test retrieving all feature requests."""
    # Create multiple
    for i in range(3):
        create_data = FeatureRequestCreate(
            platform_name=f"platform_{i}",
            start_url=f"https://example{i}.com",
            description=f"Test {i}",
            created_by="test_user"
        )
        feature_request_service.create_request(create_data)
    
    all_requests = feature_request_service.get_all_requests()
    
    assert len(all_requests) >= 3
    print(f"✓ Retrieved {len(all_requests)} feature requests")


def test_feature_request_get_by_status(feature_request_service):
    """Test filtering feature requests by status."""
    # Create requests with different statuses
    create_data = FeatureRequestCreate(
        platform_name="status_test",
        start_url="https://status.com",
        description="Status test",
        created_by="test_user"
    )
    
    created = feature_request_service.create_request(create_data)
    
    # Update status
    update_data = FeatureRequestUpdate(status="completed")
    feature_request_service.update_request(created.id, update_data)
    
    # Get open requests
    open_requests = feature_request_service.get_open_requests()
    
    # Get completed requests
    completed = feature_request_service.get_all_requests(status="completed")
    
    assert len(completed) > 0
    assert any(r.id == created.id for r in completed)
    print("✓ Feature request filtering by status works")


def test_feature_request_delete(feature_request_service):
    """Test deleting feature request."""
    create_data = FeatureRequestCreate(
        platform_name="delete_test",
        start_url="https://delete.com",
        description="To be deleted",
        created_by="test_user"
    )
    
    created = feature_request_service.create_request(create_data)
    request_id = created.id
    
    # Delete
    deleted = feature_request_service.delete_request(request_id)
    
    assert deleted is True
    
    # Verify deletion
    retrieved = feature_request_service.get_request(request_id)
    assert retrieved is None
    print("✓ Feature request deletion works")


def test_feature_request_stats(feature_request_service):
    """Test feature request statistics."""
    # Create requests with different statuses
    statuses = ["open", "in_progress", "completed", "rejected", "open"]
    
    for i, status in enumerate(statuses):
        create_data = FeatureRequestCreate(
            platform_name=f"stats_{i}",
            start_url=f"https://stats{i}.com",
            description=f"Stats test {i}",
            created_by="test_user"
        )
        created = feature_request_service.create_request(create_data)
        if status != "open":
            update_data = FeatureRequestUpdate(status=status)
            feature_request_service.update_request(created.id, update_data)
    
    stats = feature_request_service.get_stats()
    
    assert stats["total"] >= len(statuses)
    assert stats["open"] >= 1
    print(f"✓ Stats work: {stats}")


def test_feature_request_get_by_platform(feature_request_service):
    """Test getting feature requests by platform."""
    platform_name = "specific_platform"
    
    for i in range(2):
        create_data = FeatureRequestCreate(
            platform_name=platform_name,
            start_url=f"https://{platform_name}{i}.com",
            description=f"Platform test {i}",
            created_by="test_user"
        )
        feature_request_service.create_request(create_data)
    
    requests = feature_request_service.get_requests_by_platform(platform_name)
    
    assert len(requests) >= 2
    assert all(r.platform_name == platform_name for r in requests)
    print(f"✓ Found {len(requests)} requests for platform {platform_name}")


def test_feature_request_domain_entity():
    """Test FeatureRequest domain entity."""
    request = FeatureRequest(
        platform_name="domain_test",
        start_url="https://domain.com",
        description="Domain test",
        created_by="test_user",
        status="open"
    )
    
    assert request.platform_name == "domain_test"
    assert request.status == "open"
    print("✓ FeatureRequest domain entity works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
