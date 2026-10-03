"""
Feature Request Repository
Handles CRUD operations for feature requests via Repository Pattern.
"""

from typing import List, Optional, Dict, Any
from core.repositories.base_repository import BaseRepository
from core.domain.feature_request import FeatureRequest


class FeatureRequestRepository(BaseRepository):
    """Repository for feature requests."""

    def save(self, feature_request: FeatureRequest) -> FeatureRequest:
        """Save feature request to database."""
        if feature_request.id is None:
            # Create new
            query = """
                INSERT INTO feature_requests
                (platform_name, start_url, example_listing_url, description, created_by, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                feature_request.platform_name,
                feature_request.start_url,
                feature_request.example_listing_url,
                feature_request.description,
                feature_request.created_by,
                feature_request.status
            )
            feature_request.id = self.execute_single(query, params, require_lastrowid=True)
        else:
            # Update existing
            query = """
                UPDATE feature_requests
                SET platform_name = ?, start_url = ?, example_listing_url = ?, 
                    description = ?, created_by = ?, status = ?
                WHERE id = ?
            """
            params = (
                feature_request.platform_name,
                feature_request.start_url,
                feature_request.example_listing_url,
                feature_request.description,
                feature_request.created_by,
                feature_request.status,
                feature_request.id
            )
            self.execute_single(query, params)
        
        return feature_request

    def find_by_id(self, request_id: int) -> Optional[FeatureRequest]:
        """Find feature request by ID."""
        query = """
            SELECT id, platform_name, start_url, example_listing_url, description,
                   created_by, created_at, status
            FROM feature_requests
            WHERE id = ?
        """
        result = self.fetch_one(query, (request_id,))
        if result:
            return FeatureRequest.from_dict(result)
        return None

    def find_all(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeatureRequest]:
        """Find all feature requests with optional filtering."""
        conditions = []
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT id, platform_name, start_url, example_listing_url, description,
                   created_by, created_at, status
            FROM feature_requests
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params))
        return [FeatureRequest.from_dict(row) for row in results]

    def find_by_platform(self, platform_name: str) -> List[FeatureRequest]:
        """Find feature requests by platform."""
        query = """
            SELECT id, platform_name, start_url, example_listing_url, description,
                   created_by, created_at, status
            FROM feature_requests
            WHERE platform_name = ?
            ORDER BY created_at DESC
        """
        results = self.execute_query(query, (platform_name,))
        return [FeatureRequest.from_dict(row) for row in results]

    def find_open(self, limit: int = 100) -> List[FeatureRequest]:
        """Find all open feature requests."""
        return self.find_all(status="open", limit=limit)

    def find_by_status(self, status: str, limit: int = 100) -> List[FeatureRequest]:
        """Find feature requests by status."""
        return self.find_all(status=status, limit=limit)

    def count_all(self, status: Optional[str] = None) -> int:
        """Count total feature requests."""
        if status:
            query = "SELECT COUNT(*) as count FROM feature_requests WHERE status = ?"
            result = self.fetch_one(query, (status,))
        else:
            query = "SELECT COUNT(*) as count FROM feature_requests"
            result = self.fetch_one(query)
        
        return result['count'] if result else 0

    def delete_by_id(self, request_id: int) -> None:
        """Delete feature request by ID."""
        query = "DELETE FROM feature_requests WHERE id = ?"
        self.execute_single(query, (request_id,))

    def update_status(self, request_id: int, status: str) -> None:
        """Update feature request status."""
        query = "UPDATE feature_requests SET status = ? WHERE id = ?"
        self.execute_single(query, (status, request_id))

    def exists(self, request_id: int) -> bool:
        """Check if feature request exists."""
        query = "SELECT 1 FROM feature_requests WHERE id = ?"
        result = self.fetch_one(query, (request_id,))
        return result is not None
