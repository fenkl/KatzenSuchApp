"""Dashboard Page for KatzenSuchApp with API integration."""

import asyncio
import flet as ft
from typing import List, Dict
from flet_app.ui.components.filter_panel import FilterPanel
from flet_app.ui.components.listing_card import ListingCard
from flet_app.services.api_client import get_api_client
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class DashboardPage:
    """Dashboard page using API client instead of direct DB access."""
    
    scraper_mode = "ui"
    
    def __init__(self):
        self.title = "Dashboard"
        self.listings: List[Dict] = []
        self.filtered_listings: List[Dict] = []
        self.filters = {
            "age_min": 2,
            "age_max": 8,
            "einzelgaenger": True,
            "freigang": True,
            "confidence_min": 0.7,
        }
        self.current_page = 0
        self.page_size = 10
        self.scraper_status_dot = None
        self.scraper_button = None
        self.api_client = get_api_client()
        self.is_loading = False
        self.polling_task = None
        self.polling_active = False
        self.last_update_label = None

    def build(self, page: ft.Page):
        self.page = page
        # Stop previous polling if exists to prevent multiple loops
        self.polling_active = False
        # Small delay to let previous loop exit
        if hasattr(self.page, 'run_task'):
            # Use page overlay to ensure clean stop
            pass
        self.filter_panel = FilterPanel(self._on_filter_change)
        
        # Setup error handling callback for API client
        def error_handler(message: str, response):
            # Use existing error UI but with better messages
            asyncio.create_task(self._show_api_error(message, response))
        
        self.api_client.set_error_callback(error_handler)
        
        # Main layout
        self.listings_container = ft.Column(spacing=10)
        self.pagination_controls = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        # Determine scraper status color based on mode
        mode = getattr(self.__class__, 'scraper_mode', 'ui')
        if mode == 'both':
            status_color = ft.Colors.GREEN_400
            status_tooltip = "Scraper aktiv"
        else:
            status_color = ft.Colors.RED_400
            status_tooltip = "Scraper inaktiv"
        
        # Scraper status indicator
        self.scraper_status_dot = ft.Container(
            width=12,
            height=12,
            border_radius=6,
            bgcolor=status_color,
            tooltip=status_tooltip
        )
        
        # Create button with new label
        self.scraper_button = ft.FilledButton(
            "Aktualisieren",
            on_click=self._on_scrape
        )
        
        # Last update indicator
        self.last_update_label = ft.Text(
            "Letztes Update: -",
            size=12,
            italic=True,
            color=ft.Colors.GREY_600
        )
        
        self.content = ft.Row(
            controls=[
                ft.Container(
                    content=self.filter_panel,
                    width=300,
                    padding=10,
                    bgcolor=ft.Colors.GREY_100
                ),
                ft.VerticalDivider(width=1),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text("KatzenSuchApp Dashboard", size=24, weight=ft.FontWeight.BOLD),
                                        self.scraper_status_dot,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8
                                ),
                                self.scraper_button,
                                ft.IconButton(ft.Icons.REFRESH, on_click=self._refresh_listings),
                                self.loading_indicator
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        self.last_update_label,
                        self.listings_container,
                        self.pagination_controls,
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    margin=10
                )
            ],
            expand=True
        )
        
        # Initial load - use async task
        page.run_task(self._start_polling)
        return self.content

    async def _start_polling(self):
        """Start polling for updates."""
        # Stop any existing polling first
        self.polling_active = False
        await asyncio.sleep(0.1)  # Give previous loop time to stop
        
        await self._load_listings_async()
        self.polling_active = True
        await self._polling_loop()
        
    async def _polling_loop(self):
        """Polling loop with 30s interval."""
        while self.polling_active:
            # Wait 30 seconds, but check active flag periodically
            for _ in range(30):
                if not self.polling_active:
                    break
                await asyncio.sleep(1)
            
            if self.polling_active and self.page:
                try:
                    # Refresh listings in background
                    await self._load_listings_async()
                    log.info("Dashboard polling: listings refreshed")
                except Exception as e:
                    log.error(f"Polling error: {e}")
    
    async def _initial_load(self):
        """Initial async load of listings."""
        await self._load_listings_async()
        self.page.update()

    async def _load_listings_async(self):
        """Load listings from API."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_indicator.visible = True
        self.page.update()
        
        try:
            # Check if user is authenticated
            async with self.api_client as client:
                # Try to get current user (will fail if not authenticated)
                user_response = await client.get_current_user()
                
                # Check if reauth needed
                if user_response.needs_reauth:
                    await self._handle_needs_reauth(user_response)
                    return
                
                if not user_response.success:
                    # Not authenticated - show login prompt or use mock data
                    log.warning("User not authenticated, using mock data")
                    self._load_mock_data()
                    await self._show_auth_warning()
                    return
                
                # Load listings via API with server-side filters
                response = await client.get_listings(
                    limit=100,
                    offset=self.current_page * 10,
                    age_min=self.filters.get("age_min"),
                    age_max=self.filters.get("age_max"),
                    einzelgaenger=self.filters.get("einzelgaenger"),
                    freigang_noetig=self.filters.get("freigang"),
                    min_confidence=self.filters.get("confidence_min")
                )
                
                if response.success and response.data:
                    self.listings = self._normalize_listings(response.data)
                    self.filtered_listings = self.listings.copy()
                    log.info(f"Loaded {len(self.listings)} listings from API (server-side filtered)")
                else:
                    log.error(f"Failed to load listings: {response.error}")
                    self._load_mock_data()
                    await self._show_error("Fehler beim Laden der Listings")
                
        except Exception as e:
            log.error(f"Error loading listings from API: {e}")
            self._load_mock_data()
            await self._show_error(f"API Fehler: {e}")
        
        finally:
            self.is_loading = False
            self.loading_indicator.visible = False
        
        self._apply_filters()
        self._render_listings()
        self._update_last_update_label()

    def _normalize_listings(self, api_listings: List[Dict]) -> List[Dict]:
        """Normalize API response to dashboard format."""
        normalized = []
        for item in api_listings:
            # API returns Pydantic models, convert to dict
            if hasattr(item, 'dict'):
                item = item.dict()
            elif hasattr(item, 'model_dump'):
                item = item.model_dump()
            
            listing = {
                "id": item.get("id"),
                "url": item.get("url", ""),
                "platform": item.get("platform", ""),
                "city": item.get("city", ""),
                "title": item.get("title", "Unbekannt"),
                "description": item.get("description", ""),
                "age": item.get("age"),
                "extracted_at": item.get("extracted_at", ""),
                "llm_classification": {
                    "confidence": float(item.get("confidence", 0) or 0),
                    "alter_ok": bool(item.get("alter_ok", False)),
                    "einzelgaenger_ok": bool(item.get("einzelgaenger", False)),
                    "freigang_ok": bool(item.get("freigang_noetig", False)),
                }
            }
            normalized.append(listing)
        
        return normalized

    def _update_last_update_label(self):
        """Update last update timestamp label."""
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.value = f"Letztes Update: {now}"
        if self.page:
            self.page.update()
    
    def _load_mock_data(self):
        """Fallback mock data."""
        self.listings = [
            {
                "id": i,
                "url": f"https://example.com/cat/{i}",
                "platform": "TierheimHelden",
                "title": f"Katze {i} - Süße Maus",
                "description": "",
                "city": "",
                "age": None,
                "llm_classification": {
                    "confidence": 0.85 + (i % 3) * 0.05,
                    "alter_ok": True,
                    "einzelgaenger_ok": True,
                    "freigang_ok": True,
                }
            }
            for i in range(25)
        ]

    async def _show_auth_warning(self):
        """Show authentication warning."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text("⚠️ Nicht authentifiziert – Bitte erst einloggen"),
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def _show_error(self, message: str):
        """Show error message."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"❌ {message}"),
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def _show_api_error(self, message: str, response):
        """Show API error with specific handling for auth errors."""
        if response and response.needs_reauth:
            # Token expired - redirect to login
            self.page.snack_bar = ft.SnackBar(
                ft.Text("🔐 Session abgelaufen. Bitte erneut anmelden."),
                action="Login",
                on_action=lambda e: self.page.navigate("/")
            )
        else:
            # Regular error
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"❌ {message}"),
                action="OK"
            )
        self.page.snack_bar.open = True
        self.page.update()
        
        # Handle reauth - clear token and redirect
        if response and response.needs_reauth:
            self.api_client.token = None
            self.api_client.credentials = None
            # Small delay before redirect
            await asyncio.sleep(2)
            self.page.navigate("/")

    async def _handle_needs_reauth(self, response):
        """Handle authentication required response."""
        if response and response.needs_reauth:
            await self._show_api_error("Session abgelaufen", response)
            return True
        return False

    def _on_filter_change(self, filters):
        self.filters = filters
        # Reset to first page when filters change
        self.current_page = 0
        # Reload listings with new server-side filters
        asyncio.create_task(self._load_listings_async())

    def _apply_filters(self):
        """Apply client-side filters to listings - now mostly handled server-side."""
        # With server-side filtering, we just use the listings returned from API
        # No additional client-side filtering needed
        # Keep for backward compatibility and any additional client-side logic
        self.filtered_listings = self.listings.copy()

    def _render_listings(self):
        """Render listings to UI."""
        self.listings_container.controls.clear()
        
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_items = self.filtered_listings[start:end]
        
        if not page_items:
            self.listings_container.controls.append(
                ft.Text("Keine Listings gefunden", size=16, italic=True)
            )
        else:
            for listing in page_items:
                card = ListingCard(
                    listing=listing,
                    on_mark_processed=self._mark_processed,
                    on_rate=self._rate_listing,
                    on_feature_request=self._feature_request
                )
                self.listings_container.controls.append(card)
        
        self._render_pagination()
        self.page.update()

    def _render_pagination(self):
        total_pages = max(1, (len(self.filtered_listings) + self.page_size - 1) // self.page_size)
        self.pagination_controls.controls = []
        
        prev_disabled = self.current_page == 0
        next_disabled = self.current_page >= total_pages - 1
        
        self.pagination_controls.controls.extend([
            ft.IconButton(
                ft.Icons.ARROW_BACK,
                disabled=prev_disabled,
                on_click=lambda e: self._go_to_page(self.current_page - 1)
            ),
            ft.Text(f"{self.current_page + 1} / {total_pages}"),
            ft.IconButton(
                ft.Icons.ARROW_FORWARD,
                disabled=next_disabled,
                on_click=lambda e: self._go_to_page(self.current_page + 1)
            ),
        ])

    def _go_to_page(self, page_num):
        """Navigate to page."""
        self.current_page = page_num
        # Reload data for new page
        asyncio.create_task(self._load_listings_async())

    async def _on_scrape(self, e):
        """Trigger scraper refresh via API."""
        try:
            async with self.api_client as client:
                response = await client.trigger_scraper()
                if response.success:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("✅ Scraper gestartet"),
                        action="OK"
                    )
                    # Reload after short delay
                    await asyncio.sleep(2)
                    await self._load_listings_async()
                else:
                    await self._show_error(f"Scraper Fehler: {response.error}")
        except Exception as ex:
            await self._show_error(f"Fehler: {ex}")
        
        self.page.snack_bar.open = True
        self.page.update()

    async def _refresh_listings(self, e):
        """Refresh listings."""
        self.current_page = 0
        await self._load_listings_async()
        self.page.update()

    async def _mark_processed(self, url):
        """Mark listing as processed."""
        try:
            # Find platform for this URL
            platform = "unknown"
            for listing in self.listings:
                if listing.get("url") == url:
                    platform = listing.get("platform", "unknown")
                    break
            
            # Call API to mark as processed
            async with self.api_client as client:
                response = await client.mark_processed(url, platform)
                
                if response.success:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"✓ URL als verarbeitet markiert: {url[:50]}..."),
                        action="OK"
                    )
                    # Refresh listings to reflect new state
                    self.current_page = 0
                    await self._load_listings_async()
                else:
                    await self._show_error(f"Fehler beim Markieren: {response.error}")
        except Exception as e:
            await self._show_error(f"Fehler: {e}")
        
        self.page.snack_bar.open = True
        self.page.update()

    def _rate_listing(self, url):
        """Rate listing."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"⭐ Rating für {url[:50]}..."),
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _feature_request(self, url):
        """Feature request."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"💡 Feature Request für {url[:50]}..."),
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()
