"""Scraper router for FastAPI API."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import Optional
from api.dependencies import get_current_user, get_config
from core.services.scraper_service import scraper_service

router = APIRouter()


@router.post("/trigger")
async def trigger_scraper(
    platform: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    max_pages: int = Query(3, ge=1, le=10),
    classify: bool = Query(True),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user)
):
    """Manually trigger scraper. Optionally run in background."""
    config = get_config()
    cfg = config()
    platforms = list(cfg.platform_configs.keys())
    
    if platform and platform not in platforms:
        raise HTTPException(status_code=404, detail=f"Platform {platform} not found")
    
    # Validate city if provided
    if city and city not in cfg.cities:
        raise HTTPException(status_code=404, detail=f"City {city} not configured")
    
    target_platforms = [platform] if platform else platforms
    target_city = city or cfg.cities[0] if cfg.cities else None
    
    if background_tasks:
        # Run asynchronously in background
        background_tasks.add_task(
            scraper_service.trigger_scraping,
            city=target_city,
            platform=platform,
            max_pages=max_pages,
            classify=classify
        )
        return {
            "message": f"Scraper triggered in background for platforms: {target_platforms}",
            "platforms": target_platforms,
            "city": target_city,
            "status": "triggered_background"
        }
    else:
        # Run synchronously and return results
        try:
            result = await scraper_service.trigger_scraping(
                city=target_city,
                platform=platform,
                max_pages=max_pages,
                classify=classify
            )
            return {
                "message": "Scraper completed",
                "platforms": target_platforms,
                "city": target_city,
                "result": result,
                "status": "completed"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraper failed: {str(e)}")


@router.get("/status")
async def scraper_status(current_user = Depends(get_current_user)):
    """Get scraper status."""
    status = scraper_service.get_status()
    return {
        "status": "running" if status.running else "idle",
        "last_run": status.last_run.isoformat() if status.last_run else None,
        "current_city": status.current_city,
        "next_city": scraper_service.get_next_city(),
        "active_platforms": status.platforms,
        "cities": status.cities
    }


@router.get("/configs")
async def get_scraper_configs(current_user = Depends(get_current_user)):
    """Get scraper configurations."""
    from modules.db_utils import get_scraper_configs
    configs = get_scraper_configs()
    return {"configs": configs}
