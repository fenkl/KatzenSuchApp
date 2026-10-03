"""
Feature Request Service
Business logic for feature requests.
"""

from typing import List, Optional, Dict, Any
from core.repositories.feature_request_repository import FeatureRequestRepository
from core.domain.feature_request import FeatureRequest
from api.models.schemas import FeatureRequestCreate, FeatureRequestUpdate, FeatureRequestResponse


class FeatureRequestService:
    """Service for feature request management."""

    def __init__(self):
        self.repository = FeatureRequestRepository()

    def create_request(self, request_data: FeatureRequestCreate, created_by: str = "admin") -> FeatureRequestResponse:
        """Create new feature request."""
        feature_request = FeatureRequest(
            platform_name=request_data.platform_name,
            start_url=request_data.start_url,
            example_listing_url=request_data.example_listing_url,
            description=request_data.description,
            created_by=created_by,
            status="open"
        )
        
        saved = self.repository.save(feature_request)
        return self._to_response(saved)

    def get_request(self, request_id: int) -> Optional[FeatureRequestResponse]:
        """Get feature request by ID."""
        request = self.repository.find_by_id(request_id)
        if request:
            return self._to_response(request)
        return None

    def get_all_requests(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeatureRequestResponse]:
        """Get all feature requests with optional filtering."""
        requests = self.repository.find_all(status=status, limit=limit, offset=offset)
        return [self._to_response(req) for req in requests]

    def update_request(
        self,
        request_id: int,
        update_data: FeatureRequestUpdate
    ) -> Optional[FeatureRequestResponse]:
        """Update feature request."""
        existing = self.repository.find_by_id(request_id)
        if not existing:
            return None
        
        if update_data.status:
            existing.status = update_data.status
        
        if update_data.description is not None:
            existing.description = update_data.description
        
        saved = self.repository.save(existing)
        return self._to_response(saved)

    def delete_request(self, request_id: int) -> bool:
        """Delete feature request."""
        if not self.repository.exists(request_id):
            return False
        
        self.repository.delete_by_id(request_id)
        return True

    def update_status(self, request_id: int, status: str) -> Optional[FeatureRequestResponse]:
        """Update feature request status."""
        existing = self.repository.find_by_id(request_id)
        if not existing:
            return None
        
        existing.status = status
        saved = self.repository.save(existing)
        return self._to_response(saved)

    def get_open_requests(self, limit: int = 100) -> List[FeatureRequestResponse]:
        """Get all open feature requests."""
        requests = self.repository.find_open(limit=limit)
        return [self._to_response(req) for req in requests]

    def get_requests_by_platform(self, platform_name: str) -> List[FeatureRequestResponse]:
        """Get feature requests by platform."""
        requests = self.repository.find_by_platform(platform_name)
        return [self._to_response(req) for req in requests]

    def get_stats(self) -> Dict[str, int]:
        """Get feature request statistics."""
        total = self.repository.count_all()
        open_count = self.repository.count_all(status="open")
        in_progress_count = self.repository.count_all(status="in_progress")
        completed_count = self.repository.count_all(status="completed")
        rejected_count = self.repository.count_all(status="rejected")
        
        return {
            "total": total,
            "open": open_count,
            "in_progress": in_progress_count,
            "completed": completed_count,
            "rejected": rejected_count
        }

    def _to_response(self, feature_request: FeatureRequest) -> FeatureRequestResponse:
        """Convert domain entity to response schema."""
        return FeatureRequestResponse(
            id=feature_request.id,
            platform_name=feature_request.platform_name,
            start_url=feature_request.start_url,
            example_listing_url=feature_request.example_listing_url,
            description=feature_request.description,
            created_by=feature_request.created_by,
            created_at=feature_request.created_at,
            status=feature_request.status
        )


# Singleton instance
feature_request_service = FeatureRequestService()
