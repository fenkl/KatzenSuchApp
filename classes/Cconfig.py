"""Configuration class for KatzenSuchApp."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local if exists, otherwise fallback to .env
env_local = Path(__file__).resolve().parents[1] / ".env.local"
env_file = Path(__file__).resolve().parents[1] / ".env"

if env_local.exists():
    load_dotenv(env_local)
    print(f"Loading config from .env.local")
else:
    load_dotenv(env_file)
    print(f"Loading config from .env")

class Config:
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", str(Path(__file__).resolve().parents[1] / "gesehen.db"))
        self.auth_db_path = os.getenv("AUTH_DB_PATH", str(Path(__file__).resolve().parents[1] / "flet_app" / "data" / "auth.db"))
        # API Configuration
        self.api_host = os.getenv("API_HOST", "http://localhost")
        self.api_port = os.getenv("API_PORT", "8000")
        # Support explicit API_BASE_URL for easier configuration
        api_base_url_env = os.getenv("API_BASE_URL")
        if api_base_url_env:
            self.api_base_url = api_base_url_env
        else:
            self.api_base_url = f"{self.api_host}:{self.api_port}"
        self.ollama_url = os.getenv("OLLAMA_URL", "http://home-ai:11434/api/chat")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "phi-4-mini")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        self.cities = os.getenv("CITIES", "Berlin,Hamburg,München,Köln,Frankfurt").split(",")
        self.scraper_interval_minutes = int(os.getenv("SCRAPER_INTERVAL_MINUTES", "15"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # JWT Settings - Environment-based
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Platform configs - Single Source of Truth
        self.platform_configs = {
            "tierheimhelden": {
                "base_url": "https://www.tierheimhelden.de",
                "listing_selector": "a[href*='/tier/']",
                "detail_selector": "div.detail",
                "pagination_param": "page",
                "city_param": "city",
                "enabled": True,
                "handler_class": "TierheimHeldenHandler"
            },
            "shelta": {
                "base_url": "https://www.shelta.tasso.net",
                "listing_selector": "form[action*='/Katze/']",
                "detail_selector": "div.detail",
                "pagination_param": "s",
                "city_param": None,
                "enabled": True,
                "handler_class": "SheltaHandler"
            },
            "leipziger_land": {
                "base_url": "https://www.tierschutzverein-leipziger-land.de",
                "listing_selector": "a[href*='/Project/']",
                "detail_selector": "div.project",
                "pagination_param": "page",
                "city_param": None,
                "enabled": True,
                "handler_class": "LeipzigerLandHandler"
            }
        }
        
        # Filter criteria - Single Source of Truth
        self.filter_criteria = {
            "alter_min": 2,
            "alter_max": 8,
            "einzelgaenger": True,
            "kein_freigang_noetig": True
        }
    
    
    def get_no_bot(self):
        return os.getenv("NO_BOT", "false").lower() == "true"
