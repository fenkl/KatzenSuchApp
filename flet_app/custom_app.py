"""Custom BaseApp with API-enabled login."""

from flet_base.core.app import BaseApp
from flet_base.core.auth import logout as base_logout
from flet_app.services.api_client import get_api_client
from flet_app.ui.login_api import LoginPageAPI
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class KatzenSuchApp(BaseApp):
    """Extended BaseApp with API login integration."""

    def _show_login(self, page):
        """Override login to use API-enabled login page."""
        if self._login_page is None:
            self._login_page = LoginPageAPI(self)
        page.controls.clear()
        page.add(self._login_page)
        page.update()
    
    def build(self, page):
        """Override build to restore API session from session store and set default route."""
        # Restore API token from session store before base build
        self._restore_api_session(page)
        
        # Override default route if set
        if not hasattr(self, 'default_route'):
            self.default_route = "/dashboard"
            
        # Patch base build to use custom default route
        cfg = None
        from flet_base.core.config import get_config
        cfg = get_config()
        page.title = "FletBase App"
        page.theme_mode = cfg.theme.mode
        for ctrl in list(page.overlay):
            if ctrl in page.overlay:
                page.overlay.remove(ctrl)
        
        from flet_base.core.db import seed_defaults
        seed_defaults()
        
        # Routes
        page.on_route_change = lambda e: self._on_route_change(page, e.route)
        page.on_view_pop = lambda e: self._on_view_pop(page)
        
        # Start at login if not authenticated, else default route
        from flet_base.core.auth import is_authenticated
        if not is_authenticated(page) or page.route in ("", "/"):
            page.navigate("/login")
        else:
            target_route = getattr(self, 'default_route', "/dashboard")
            if target_route not in ["/login", "/logout"]:
                page.navigate(target_route)
            else:
                page.navigate("/home")
    
    def _restore_api_session(self, page):
        """Restore API token from session store for auto-login."""
        try:
            store = page.session.store
            token = store.get("api_token")
            credentials = store.get("api_credentials")
            
            if token:
                client = get_api_client()
                client.token = token
                # Also restore credentials if available
                if credentials and isinstance(credentials, dict):
                    username = credentials.get("username")
                    password = credentials.get("password")
                    if username and password:
                        client.set_credentials(username, password)
                log.info("API session restored from session store")
        except Exception:
            pass
    
    def _on_route_change(self, page, route):
        """Override route change to handle logout sync."""
        # Handle logout route
        if route == "/logout":
            self._handle_logout(page)
            page.navigate("/login")
            return
        
        # Call parent route change
        super()._on_route_change(page, route)
    
    def _handle_logout(self, page):
        """Handle logout: clear API token and FletBase session."""
        try:
            # Clear API token from session store
            store = page.session.store
            store.remove("api_token")
            store.remove("api_credentials")
            
            # Clear API client
            client = get_api_client()
            client.token = None
            client.credentials = None
            
            # Clear FletBase session
            base_logout(page)
            
            log.info("User logged out - API token cleared")
        except Exception as e:
            log.error(f"Logout error: {e}")
