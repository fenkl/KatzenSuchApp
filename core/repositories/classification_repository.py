"""
Classification Repository
Handles CRUD operations for classifications via Repository Pattern.
"""

from typing import List, Optional, Dict, Any
from core.repositories.base_repository import BaseRepository
from core.domain.classification import Classification
from datetime import datetime


class ClassificationRepository(BaseRepository):
    """Repository for classification persistence."""

    def save(self, classification: Classification) -> None:
        """Save classification to database."""
        query = """
            INSERT OR REPLACE INTO llm_classification
            (url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
             einzelgaenger, einzelgaenger_unsicher, freigang_noetig,
             freigang_unsicher, kein_freigang_gewuenscht, confidence, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            classification.url_hash,
            classification.url,
            classification.platform,
            1 if classification.alter_ok else 0,
            classification.alter_jahre,
            1 if classification.alter_unsicher else 0,
            1 if classification.einzelgaenger else 0,
            1 if classification.einzelgaenger_unsicher else 0,
            1 if classification.freigang_noetig else 0,
            1 if classification.freigang_unsicher else 0,
            1 if classification.kein_freigang_gewuenscht else 0,
            classification.confidence,
            classification.reason
        )
        self.execute_single(query, params)

    def find_by_url_hash(self, url_hash: str) -> Optional[Classification]:
        """Find classification by url_hash."""
        query = """
            SELECT url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
                   einzelgaenger, einzelgaenger_unsicher, freigang_noetig,
                   freigang_unsicher, kein_freigang_gewuenscht, confidence, reason,
                   classified_at as created_at
            FROM llm_classification
            WHERE url_hash = ?
        """
        result = self.fetch_one(query, (url_hash,))
        if result:
            return Classification.from_dict(result)
        return None

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        alter_ok: Optional[bool] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[Classification]:
        """Find classifications with filters."""
        conditions = []
        params = []
        
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        
        if alter_ok is not None:
            conditions.append("alter_ok = ?")
            params.append(1 if alter_ok else 0)
        
        if einzelgaenger is not None:
            conditions.append("einzelgaenger = ?")
            params.append(1 if einzelgaenger else 0)
        
        if freigang_noetig is not None:
            conditions.append("freigang_noetig = ?")
            params.append(1 if freigang_noetig else 0)
        
        if min_confidence is not None:
            conditions.append("confidence >= ?")
            params.append(min_confidence)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
                   einzelgaenger, einzelgaenger_unsicher, freigang_noetig,
                   freigang_unsicher, kein_freigang_gewuenscht, confidence, reason,
                   classified_at as created_at
            FROM llm_classification
            {where_clause}
            ORDER BY classified_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params))
        return [Classification.from_dict(row) for row in results]

    def find_matching_criteria(
        self,
        alter_ok: bool = True,
        einzelgaenger: bool = False,
        freigang_noetig: bool = True,
        min_confidence: float = 0.7,
        limit: int = 100,
        offset: int = 0
    ) -> List[Classification]:
        """Find classifications matching criteria with minimum confidence."""
        query = """
            SELECT url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
                   einzelgaenger, einzelgaenger_unsicher, freigang_noetig,
                   freigang_unsicher, kein_freigang_gewuenscht, confidence, reason,
                   classified_at as created_at
            FROM llm_classification
            WHERE alter_ok = ? 
              AND einzelgaenger = ?
              AND freigang_noetig = ?
              AND confidence >= ?
            ORDER BY confidence DESC
            LIMIT ? OFFSET ?
        """
        params = (
            1 if alter_ok else 0,
            1 if einzelgaenger else 0,
            1 if freigang_noetig else 0,
            min_confidence,
            limit,
            offset
        )
        results = self.execute_query(query, params)
        return [Classification.from_dict(row) for row in results]

    def count_all(self, platform: Optional[str] = None) -> int:
        """Count total classifications."""
        if platform:
            query = "SELECT COUNT(*) as count FROM llm_classification WHERE platform = ?"
            result = self.fetch_one(query, (platform,))
        else:
            query = "SELECT COUNT(*) as count FROM llm_classification"
            result = self.fetch_one(query)
        
        return result['count'] if result else 0

    def delete_by_url_hash(self, url_hash: str) -> None:
        """Delete classification by url_hash."""
        query = "DELETE FROM llm_classification WHERE url_hash = ?"
        self.execute_single(query, (url_hash,))

    def bulk_save(self, classifications: List[Classification]) -> None:
        """Bulk save classifications."""
        query = """
            INSERT OR REPLACE INTO llm_classification
            (url_hash, url, platform, alter_ok, alter_jahre, alter_unsicher,
             einzelgaenger, einzelgaenger_unsicher, freigang_noetig,
             freigang_unsicher, kein_freigang_gewuenscht, confidence, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_list = []
        for cls in classifications:
            params_list.append((
                cls.url_hash,
                cls.url,
                cls.platform,
                1 if cls.alter_ok else 0,
                cls.alter_jahre,
                1 if cls.alter_unsicher else 0,
                1 if cls.einzelgaenger else 0,
                1 if cls.einzelgaenger_unsicher else 0,
                1 if cls.freigang_noetig else 0,
                1 if cls.freigang_unsicher else 0,
                1 if cls.kein_freigang_gewuenscht else 0,
                cls.confidence,
                cls.reason
            ))
        self.execute_many(query, params_list)
