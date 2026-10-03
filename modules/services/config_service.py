"""Config Service for KatzenSuchApp."""

import os
from pathlib import Path
from typing import Dict, Any
from classes.Cconfig import Config
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class ConfigService:
    """Service for managing configuration."""
    
    def __init__(self):
        self.config = Config()
        self._load_env()
    
    def _load_env(self):
        """Load environment variables."""
        from dotenv import load_dotenv
        load_dotenv()
        log.info("Environment variables loaded")
    
    def get_db_path(self) -> str:
        """Get database path."""
        return self.config.db_path
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama configuration."""
        return {
            "url": self.config.ollama_url,
            "model": self.config.ollama_model,
            "timeout": self.config.ollama_timeout,
        }
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """Get scraper configuration."""
        return {
            "cities": self.config.cities,
            "interval_minutes": self.config.scraper_interval_minutes,
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration."""
        validation = {
            "db_path_exists": Path(self.config.db_path).parent.exists(),
            "ollama_url_set": bool(self.config.ollama_url),
            "cities_configured": len(self.config.cities) > 0,
            "interval_positive": self.config.scraper_interval_minutes > 0,
        }
        return validation
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return {
            "db_path": self.config.db_path,
            "auth_db_path": self.config.auth_db_path,
            "ollama_url": self.config.ollama_url,
            "ollama_model": self.config.ollama_model,
            "ollama_timeout": self.config.ollama_timeout,
            "cities": self.config.cities,
            "scraper_interval_minutes": self.config.scraper_interval_minutes,
            "log_level": self.config.log_level,
        }


# Singleton instance
config_service = ConfigService()
