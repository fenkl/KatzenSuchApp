"""API Client for Flet UI to communicate with FastAPI backend."""

import asyncio
import httpx
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from classes.Cconfig import Config
from modules.Mhandle_log import get_logger

log = get_logger(__name__)

config = Config()

@dataclass
class APIResponse:
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    needs_reauth: bool = False


@dataclass
class AuthCredentials:
    """Stored authentication credentials for token refresh."""
    username: Optional[str] = None
    password: Optional[str] = None


class APIClient:
    """HTTP client for FastAPI backend with JWT auth support."""
    
    def __init__(self):
        # API Base URL from Config
        self.base_url = f"{config.api_base_url}/api/v1"
        
        self.token: Optional[str] = None
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = 30.0
        self.credentials: Optional[AuthCredentials] = None
        self._retry_count: int = 0
        self.max_retries: int = 2
        self.error_callback: Optional[Callable[[str, APIResponse], None]] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def set_token(self, token: str):
        """Set JWT token for authenticated requests."""
        self.token = token
    
    def set_credentials(self, username: str, password: str):
        """Store credentials for token refresh."""
        self.credentials = AuthCredentials(username=username, password=password)
    
    def set_error_callback(self, callback: Callable[[str, APIResponse], None]):
        """Set callback for user feedback on errors."""
        self.error_callback = callback
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _refresh_token(self) -> bool:
        """Attempt to refresh token using stored credentials."""
        if not self.credentials or not self.credentials.username:
            log.warning("No credentials stored for token refresh")
            return False
        
        log.info("Attempting token refresh...")
        try:
            # Clear current token to force fresh login
            old_token = self.token
            self.token = None
            
            # Retry login with stored credentials
            login_response = await self.login(
                self.credentials.username,
                self.credentials.password
            )
            
            if login_response.success:
                log.info("Token refreshed successfully")
                return True
            else:
                log.error(f"Token refresh failed: {login_response.error}")
                self.token = None
                return False
                
        except Exception as e:
            log.error(f"Token refresh error: {e}")
            self.token = None
            return False
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_on_401: bool = True
    ) -> APIResponse:
        """Make HTTP request with enhanced error handling and retry logic."""
        if not self.client:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        try:
            headers = self._get_headers()
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers
            )
            
            # Handle 401 Unauthorized - token expired
            if response.status_code == 401:
                log.warning("Authentication failed - token may be expired")
                
                if retry_on_401 and self._retry_count < self.max_retries:
                    self._retry_count += 1
                    log.info(f"Retrying after 401 (attempt {self._retry_count}/{self.max_retries})")
                    
                    # Try to refresh token
                    if await self._refresh_token():
                        # Retry original request with new token
                        log.info("Retrying original request with refreshed token")
                        # Small delay before retry
                        await asyncio.sleep(0.5)
                        return await self._request(
                            method, endpoint, params, json_data, 
                            retry_on_401=False  # Prevent infinite loop
                        )
                    else:
                        # Token refresh failed - need reauth
                        error_msg = "Session abgelaufen – Bitte erneut einloggen"
                        self._notify_user_error(error_msg, status_code=401, needs_reauth=True)
                        return APIResponse(
                            success=False,
                            error=error_msg,
                            status_code=401,
                            needs_reauth=True
                        )
                else:
                    error_msg = "Unauthorized – Authentication fehlgeschlagen"
                    self._notify_user_error(error_msg, status_code=401)
                    return APIResponse(
                        success=False,
                        error=error_msg,
                        status_code=401
                    )
            
            # Handle other HTTP errors
            response.raise_for_status()
            
            # Reset retry count on success
            self._retry_count = 0
            
            try:
                data = response.json()
            except Exception:
                data = response.text
            
            return APIResponse(
                success=True,
                data=data,
                status_code=response.status_code
            )
            
        except httpx.TimeoutException:
            log.error(f"Request timeout for {method} {endpoint}")
            error_msg = "VerbindungsTimeout – Server nicht erreichbar"
            self._notify_user_error(error_msg, status_code=408)
            return APIResponse(
                success=False,
                error=error_msg,
                status_code=408
            )
        except httpx.ConnectError:
            log.error(f"Connection error for {method} {endpoint}")
            error_msg = "Verbindungsfehler – Kann Server nicht erreichen"
            self._notify_user_error(error_msg, status_code=503)
            return APIResponse(
                success=False,
                error=error_msg,
                status_code=503
            )
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error {e.response.status_code} for {method} {endpoint}")
            
            # Handle specific status codes with user-friendly messages
            status_code = e.response.status_code
            error_text = e.response.text
            
            if status_code == 404:
                error_msg = "Ressource nicht gefunden"
            elif status_code == 403:
                error_msg = "Zugriff verweigert – Keine Berechtigung"
            elif status_code == 500:
                error_msg = "Serverfehler – Bitte später erneut versuchen"
            elif status_code == 502:
                error_msg = "Server nicht verfügbar"
            elif status_code == 503:
                error_msg = "Service vorübergehend nicht verfügbar"
            else:
                error_msg = f"HTTP Fehler {status_code}"
            
            self._notify_user_error(error_msg, status_code=status_code)
            return APIResponse(
                success=False,
                error=error_msg,
                status_code=status_code
            )
        except Exception as e:
            log.error(f"Request error for {method} {endpoint}: {e}")
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            self._notify_user_error(error_msg, status_code=500)
            return APIResponse(
                success=False,
                error=error_msg,
                status_code=500
            )
    
    def _notify_user_error(self, message: str, status_code: Optional[int] = None, needs_reauth: bool = False):
        """Notify user about error via callback or logging."""
        error_msg = f"API Fehler [{status_code}]: {message}" if status_code else message
        
        if self.error_callback:
            # Create a simple APIResponse for callback
            resp = APIResponse(
                success=False,
                error=message,
                status_code=status_code,
                needs_reauth=needs_reauth
            )
            try:
                self.error_callback(message, resp)
            except Exception as e:
                log.error(f"Error callback failed: {e}")
        else:
            log.warning(error_msg)
    
    async def login(self, username: str, password: str) -> APIResponse:
        """Login and get JWT token."""
        # Store credentials for potential refresh
        self.set_credentials(username, password)
        
        data = {"username": username, "password": password}
        response = await self._request("POST", "/auth/login", json_data=data, retry_on_401=False)
        
        if response.success and response.data:
            token = response.data.get("access_token")
            if token:
                self.set_token(token)
                log.info(f"Login successful for user {username}")
                # Reset retry count
                self._retry_count = 0
            else:
                log.error("Login response missing access_token")
                response.success = False
                response.error = "Ungültige Login-Antwort"
        
        return response


    async def logout(self) -> APIResponse:
        """Logout."""
        response = await self._request("POST", "/auth/logout", retry_on_401=False)
        if response.success:
            self.token = None
            self.credentials = None
            log.info("User logged out")
        return response
    
    async def get_current_user(self) -> APIResponse:
        """Get current user info."""
        return await self._request("GET", "/auth/me")
    
    # Listings endpoints
    async def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        city: Optional[str] = None,
        processed: Optional[bool] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        einzelgaenger: Optional[bool] = None,
        freigang_noetig: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> APIResponse:
        """Get listings with filters."""
        params = {
            "limit": limit,
            "offset": offset
        }
        if platform:
            params["platform"] = platform
        if city:
            params["city"] = city
        if processed is not None:
            params["processed"] = processed
        if age_min is not None:
            params["age_min"] = age_min
        if age_max is not None:
            params["age_max"] = age_max
        if einzelgaenger is not None:
            params["einzelgaenger"] = einzelgaenger
        if freigang_noetig is not None:
            params["freigang_noetig"] = freigang_noetig
        if min_confidence is not None:
            params["min_confidence"] = min_confidence
        
        return await self._request("GET", "/listings", params=params)
    
    async def mark_processed(self, url: str, platform: str) -> APIResponse:
        """Mark listing as processed."""
        data = {"url": url, "platform": platform}
        return await self._request("POST", "/listings/mark-processed", json_data=data)
    
    async def get_listing(self, listing_id: int) -> APIResponse:
        """Get specific listing."""
        return await self._request("GET", f"/listings/{listing_id}")
    
    async def search_listings(self, query: str, limit: int = 100) -> APIResponse:
        """Search listings."""
        params = {"q": query, "limit": limit}
        return await self._request("GET", "/listings/search", params=params)
    
    async def get_matching_listings(
        self,
        alter_ok: bool = True,
        einzelgaenger: bool = False,
        freigang_noetig: bool = True,
        min_confidence: float = 0.7,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """Get listings matching classification criteria."""
        params = {
            "alter_ok": alter_ok,
            "einzelgaenger": einzelgaenger,
            "freigang_noetig": freigang_noetig,
            "min_confidence": min_confidence,
            "limit": limit,
            "offset": offset
        }
        return await self._request("GET", "/listings/matching", params=params)
    
    async def get_listing_stats(self) -> APIResponse:
        """Get listing statistics."""
        return await self._request("GET", "/listings/stats/summary")
    
    # Platforms endpoints
    async def get_platforms(self) -> APIResponse:
        """Get platforms."""
        return await self._request("GET", "/platforms")
    
    async def get_listings_by_platform(
        self,
        platform_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """Get listings for specific platform."""
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", f"/listings/platform/{platform_name}", params=params)
    
    # Admin endpoints
    async def get_configs(self) -> APIResponse:
        """Get app configurations."""
        return await self._request("GET", "/admin/configs")
    
    async def get_feature_requests(self) -> APIResponse:
        """Get feature requests."""
        return await self._request("GET", "/admin/feature-requests")
    
    # Scraper endpoints
    async def trigger_scraper(self, platform: str = None, city: str = None, max_pages: int = 3, classify: bool = True) -> APIResponse:
        """Trigger scraper manually."""
        params = {}
        if platform:
            params["platform"] = platform
        if city:
            params["city"] = city
        params["max_pages"] = max_pages
        params["classify"] = classify
        return await self._request("POST", "/scraper/trigger", params=params)
    
    async def get_scraper_status(self) -> APIResponse:
        """Get scraper status."""
        return await self._request("GET", "/scraper/status")
    
    async def get_scraper_configs(self) -> APIResponse:
        """Get scraper configurations."""
        return await self._request("GET", "/admin/scraper-configs")
    
    # Classifications endpoints
    async def get_classifications(self) -> APIResponse:
        """Get LLM classifications."""
        return await self._request("GET", "/classifications")
    
    async def get_classification(self, url_hash: str) -> APIResponse:
        """Get specific classification."""
        return await self._request("GET", f"/classifications/{url_hash}")
    
    # Health check
    async def health_check(self) -> APIResponse:
        """Check API health."""
        return await self._request("GET", "/health")


# Singleton instance
_api_client_instance: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get singleton API client instance."""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    return _api_client_instance


# Helper function for simple usage with context manager
async def api_request(method: str, endpoint: str, **kwargs) -> APIResponse:
    """Simple helper for API requests."""
    async with APIClient() as client:
        return await client._request(method, endpoint, **kwargs)
