"""Admin router for FastAPI API."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel
from api.models.schemas import (
    PlatformResponse,
    ScraperConfigCreate,
    ScraperConfigUpdate,
    ScraperConfigResponse,
    FeatureRequestCreate,
    FeatureRequestUpdate,
    FeatureRequestResponse
)
from api.dependencies import get_db_connection, get_config, get_current_user, require_admin
from core.services.platform_service import platform_service
from core.services.feature_request_service import feature_request_service
from modules.db_utils import get_platforms, get_feature_requests, get_scraper_configs, add_scraper_config
import sqlite3
from pathlib import Path
import os

router = APIRouter()


class FeatureRequestCreateLegacy(BaseModel):
    platform_name: str
    start_url: str
    example_listing_url: str = ""
    description: str = ""
    status: str = "open"


@router.get("/configs")
async def get_configs(config=get_config):
    """Get app configs."""
    cfg = config()
    return {
        "db_path": cfg.db_path,
        "auth_db_path": cfg.auth_db_path,
        "ollama_url": cfg.ollama_url,
        "ollama_model": cfg.ollama_model,
        "cities": cfg.cities,
        "scraper_interval_minutes": cfg.scraper_interval_minutes,
        "platform_configs": cfg.platform_configs,
        "filter_criteria": cfg.filter_criteria
    }


@router.get("/scraper-configs")
async def get_scraper_configs(current_user=Depends(require_admin)):
    """Get all scraper configs."""
    try:
        configs = platform_service.get_all_configs()
        return {"configs": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scraper-configs/{platform_name}")
async def get_scraper_config(platform_name: str, current_user=Depends(require_admin)):
    """Get single scraper config."""
    try:
        config = platform_service.get_config(platform_name)
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
        return {"config": config}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scraper-configs")
async def create_scraper_config(config: ScraperConfigCreate, current_user=Depends(require_admin)):
    """Create or update scraper config."""
    try:
        from core.domain.config import PlatformConfig
        platform_config = PlatformConfig(
            platform_name=config.platform_name,
            base_url=config.base_url,
            listing_selector=config.listing_selector,
            detail_selector=config.detail_selector,
            pagination_param=config.pagination_param,
            city_param=config.city_param,
            enabled=bool(config.enabled),
            handler_class=config.handler_class,
            login_required=bool(config.login_required)
        )
        platform_service.save_config(platform_config)
        return {"message": "Config saved", "platform_name": config.platform_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/scraper-configs/{platform_name}")
async def update_scraper_config(
    platform_name: str,
    config: ScraperConfigUpdate,
    current_user=Depends(require_admin)
):
    """Update scraper config."""
    try:
        from core.domain.config import PlatformConfig
        existing = platform_service.get_config(platform_name)
        if not existing:
            raise HTTPException(status_code=404, detail="Config not found")
        
        # Update fields
        existing.base_url = config.base_url or existing.base_url
        existing.listing_selector = config.listing_selector or existing.listing_selector
        existing.detail_selector = config.detail_selector or existing.detail_selector
        existing.pagination_param = config.pagination_param or existing.pagination_param
        existing.city_param = config.city_param or existing.city_param
        existing.enabled = bool(config.enabled)
        existing.handler_class = config.handler_class or existing.handler_class
        existing.login_required = bool(config.login_required)
        
        platform_service.save_config(existing)
        return {"message": "Config updated", "platform_name": platform_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scraper-configs/{platform_name}")
async def delete_scraper_config(platform_name: str, current_user=Depends(require_admin)):
    """Delete scraper config."""
    try:
        if not platform_service.delete_config(platform_name):
            raise HTTPException(status_code=404, detail="Config not found")
        return {"message": "Config deleted", "platform_name": platform_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-requests")
async def get_feature_requests_list(
    status: str = None,
    current_user=Depends(require_admin)
):
    """Get feature requests."""
    try:
        requests = feature_request_service.get_all_requests(status=status)
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-requests/{request_id}")
async def get_feature_request(
    request_id: int,
    current_user=Depends(require_admin)
):
    """Get single feature request."""
    try:
        request = feature_request_service.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Feature request not found")
        return {"request": request}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature-requests")
async def create_feature_request(
    request_data: FeatureRequestCreate,
    current_user=Depends(require_admin)
):
    """Create new feature request."""
    try:
        request = feature_request_service.create_request(request_data, created_by=current_user.username)
        return {"message": "Feature request created", "request": request}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/feature-requests/{request_id}")
async def update_feature_request(
    request_id: int,
    request_data: FeatureRequestUpdate,
    current_user=Depends(require_admin)
):
    """Update feature request."""
    try:
        updated = feature_request_service.update_request(request_id, request_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Feature request not found")
        return {"message": "Feature request updated", "request": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/feature-requests/{request_id}")
async def delete_feature_request(
    request_id: int,
    current_user=Depends(require_admin)
):
    """Delete feature request."""
    try:
        if not feature_request_service.delete_request(request_id):
            raise HTTPException(status_code=404, detail="Feature request not found")
        return {"message": "Feature request deleted", "id": request_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_all_platforms():
    """Get all platforms."""
    return get_platforms()
