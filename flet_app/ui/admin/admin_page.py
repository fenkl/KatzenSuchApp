"""Admin Page for KatzenSuchApp with API integration."""

import flet as ft
from typing import List, Dict
from flet_app.ui.components.scraper_config_form import ScraperConfigForm
from flet_app.ui.components.feature_request_dialog import FeatureRequestDialog, FeatureRequestEditDialog
from flet_base.ui.components.data_table import DataTableComponent
from flet_app.services.api_client import get_api_client
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class AdminPage:
    """Admin page using API client."""
    
    def __init__(self):
        self.title = "Admin"
        self.scraper_configs: List[Dict] = []
        self.feature_requests: List[Dict] = []
        self.current_tab = 0
        self.api_client = get_api_client()
        self.loading = False
        self.scraper_running = False
        self.scraper_status_info = {}

    def build(self, page: ft.Page):
        self.page = page
        
        # Setup error handling callback for API client
        def error_handler(message: str, response):
            import asyncio
            asyncio.create_task(self._show_api_error(message, response))
        
        self.api_client.set_error_callback(error_handler)
        
        self.tabs = ft.Tabs(
            selected_index=self.current_tab,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(text="Plattformen & Scraper", content=self._build_platforms_tab()),
                ft.Tab(text="Feature Requests", content=self._build_feature_requests_tab()),
                ft.Tab(text="Ratings", content=self._build_ratings_tab()),
                ft.Tab(text="System", content=self._build_system_tab()),
            ]
        )
        
        return ft.Column(
            controls=[
                ft.Text("Admin Bereich", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Verwaltung von Plattformen, Scrapern und Feature Requests"),
                self.tabs
            ],
            spacing=20,
        )

    async def _show_api_error(self, message: str, response):
        """Show API error with user feedback."""
        if response and response.needs_reauth:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("🔐 Session abgelaufen. Bitte erneut anmelden."),
                action="Login",
                on_action=lambda e: self.page.navigate("/")
            )
            self.api_client.token = None
            self.api_client.credentials = None
            await asyncio.sleep(2)
            self.page.navigate("/")
        else:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"❌ {message}"),
                action="OK"
            )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_tab_change(self, e):
        self.current_tab = e.index
        self._refresh_current_tab()

    def _refresh_current_tab(self):
        if self.current_tab == 0:
            # Load configs via API in async task
            import asyncio
            asyncio.create_task(self._load_scraper_configs_api())
            self._render_platforms_tab()
        elif self.current_tab == 1:
            import asyncio
            asyncio.create_task(self._load_feature_requests_api())
            self._render_feature_requests_tab()

    def _build_platforms_tab(self):
        self.platforms_container = ft.Column(spacing=10)
        # Load via API
        import asyncio
        asyncio.create_task(self._load_scraper_configs_api())
        self._render_platforms_tab()
        return ft.Column([self.platforms_container], scroll=ft.ScrollMode.AUTO)

    async def _load_scraper_configs_api(self):
        """Load scraper configs via API."""
        try:
            async with self.api_client as client:
                response = await client.get_scraper_configs()
                if response.success:
                    # Normalize API response
                    configs = response.data.get('configs', []) if isinstance(response.data, dict) else response.data
                    self.scraper_configs = self._normalize_configs(configs)
                    self.page.update()
                else:
                    log.error(f"Failed to load configs: {response.error}")
                    self._show_snackbar("Fehler beim Laden der Konfigurationen")
        except Exception as e:
            log.error(f"Error loading configs: {e}")
            self._show_snackbar(f"Fehler: {e}")

    def _normalize_configs(self, configs: List[Dict]) -> List[Dict]:
        """Normalize API config format."""
        normalized = []
        for c in configs:
            if hasattr(c, 'dict'):
                c = c.dict()
            elif hasattr(c, 'model_dump'):
                c = c.model_dump()
            
            normalized.append({
                "id": c.get("id"),
                "platform_name": c.get("platform_name", ""),
                "base_url": c.get("base_url", ""),
                "listing_selector": c.get("listing_selector", ""),
                "detail_selector": c.get("detail_selector", ""),
                "pagination_param": c.get("pagination_param", ""),
                "city_param": c.get("city_param", ""),
                "enabled": "Ja" if c.get("enabled") else "Nein",
                "handler_class": c.get("handler_class", ""),
                "login_required": "Ja" if c.get("login_required") else "Nein"
            })
        return normalized

    async def _delete_scraper_config(self, platform_name: str):
        """Delete scraper config with confirmation."""
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Konfiguration löschen"),
            content=ft.Text(f"Möchten Sie die Konfiguration für {platform_name} wirklich löschen?"),
            actions=[
                ft.TextButton("Abbrechen", on_click=lambda e: setattr(confirm_dialog, "open", False)),
                ft.FilledButton("Löschen", on_click=lambda e: self._confirm_delete_config(platform_name, confirm_dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    async def _confirm_delete_config(self, platform_name: str, dialog):
        """Confirm and delete config."""
        dialog.open = False
        self.page.update()
        try:
            async with self.api_client as client:
                response = await client._request(
                    "DELETE",
                    f"/admin/scraper-configs/{platform_name}"
                )
                if response.success:
                    self._show_snackbar("Konfiguration gelöscht")
                    await self._load_scraper_configs_api()
                    self._refresh_current_tab()
                else:
                    self._show_snackbar(f"Fehler: {response.error}")
        except Exception as e:
            self._show_snackbar(f"Fehler: {e}")

    def _render_platforms_tab(self):
        self.platforms_container.controls.clear()
        
        configs = self.scraper_configs
        columns = [
            {"key": "platform_name", "label": "Plattform"},
            {"key": "base_url", "label": "Base URL"},
            {"key": "listing_selector", "label": "Listing Sel."},
            {"key": "detail_selector", "label": "Detail Sel."},
            {"key": "pagination_param", "label": "Pagination"},
            {"key": "city_param", "label": "City Param"},
            {"key": "enabled", "label": "Aktiv"},
            {"key": "handler_class", "label": "Handler"},
            {"key": "login_required", "label": "Login Req."},
        ]
        
        def on_config_action(config):
            # Show action menu
            menu = ft.AlertDialog(
                modal=True,
                title=ft.Text("Aktion wählen"),
                content=ft.Column([
                    ft.Text(f"{config.get('platform_name')}"),
                ]),
                actions=[
                    ft.TextButton("Bearbeiten", on_click=lambda e: self._handle_config_edit(config, menu)),
                    ft.TextButton("Löschen", on_click=lambda e: self._handle_config_delete(config, menu)),
                    ft.TextButton("Schließen", on_click=lambda e: setattr(menu, "open", False)),
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.dialog = menu
            menu.open = True
            self.page.update()
        
        table = DataTableComponent(columns, configs, on_action=on_config_action)
        self.platforms_container.controls.append(table.build())
        
        self.platforms_container.controls.append(
            ft.Row([
                ft.FilledButton("Neue Scraper Konfiguration", on_click=lambda e: self._new_scraper_config())
            ])
        )

    def _build_feature_requests_tab(self):
        self.feature_requests_container = ft.Column(spacing=10)
        import asyncio
        asyncio.create_task(self._load_feature_requests_api())
        self._render_feature_requests_tab()
        return ft.Column([self.feature_requests_container], scroll=ft.ScrollMode.AUTO)

    async def _load_feature_requests_api(self):
        """Load feature requests via API."""
        try:
            async with self.api_client as client:
                response = await client.get_feature_requests()
                if response.success:
                    requests = response.data.get('requests', []) if isinstance(response.data, dict) else response.data
                    self.feature_requests = self._normalize_requests(requests)
                    self.page.update()
                else:
                    log.error(f"Failed to load requests: {response.error}")
        except Exception as e:
            log.error(f"Error loading requests: {e}")

    def _normalize_requests(self, requests: List[Dict]) -> List[Dict]:
        """Normalize API request format."""
        normalized = []
        for r in requests:
            if hasattr(r, 'dict'):
                r = r.dict()
            elif hasattr(r, 'model_dump'):
                r = r.model_dump()
            
            normalized.append({
                "id": r.get("id"),
                "platform_name": r.get("platform_name", ""),
                "start_url": r.get("start_url", ""),
                "status": r.get("status", ""),
                "created_at": r.get("created_at", "")
            })
        return normalized

    def _render_feature_requests_tab(self):
        self.feature_requests_container.controls.clear()
        
        requests = self.feature_requests
        columns = [
            {"key": "platform_name", "label": "Plattform"},
            {"key": "start_url", "label": "Start URL"},
            {"key": "status", "label": "Status"},
            {"key": "created_at", "label": "Erstellt"},
        ]
        
        def on_request_action(req):
            # Show action menu
            menu = ft.AlertDialog(
                modal=True,
                title=ft.Text("Aktion wählen"),
                content=ft.Column([
                    ft.Text(f"{req.get('platform_name')}"),
                ]),
                actions=[
                    ft.TextButton("Bearbeiten", on_click=lambda e: self._handle_request_edit(req, menu)),
                    ft.TextButton("Löschen", on_click=lambda e: self._handle_request_delete(req, menu)),
                    ft.TextButton("Schließen", on_click=lambda e: setattr(menu, "open", False)),
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.dialog = menu
            menu.open = True
            self.page.update()
        
        table = DataTableComponent(columns, requests, on_action=on_request_action)
        self.feature_requests_container.controls.append(table.build())
        
        self.feature_requests_container.controls.append(
            ft.Row([
                ft.FilledButton("Neuer Feature Request", on_click=self._new_feature_request)
            ])
        )

    def _build_ratings_tab(self):
        return ft.Column([
            ft.Text("Ratings Verwaltung", size=18),
            ft.Text("Bewertungen von gelisteten Katzen anzeigen und verwalten")
        ])

    def _build_system_tab(self):
        return ft.Column([
            ft.Text("Systemeinstellungen", size=18),
            ft.Column([
                ft.Text("Scraper Steuerung", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Manueller Scraper Start"),
                ft.Row([
                    ft.ElevatedButton(
                        "Scraper jetzt starten",
                        icon=ft.icons.PLAY_CIRCLE,
                        on_click=self._trigger_scraper,
                        disabled=self.scraper_running
                    ),
                    ft.ElevatedButton(
                        "Scraper Status",
                        icon=ft.icons.INFO,
                        on_click=self._show_scraper_status
                    )
                ], spacing=10),
            ], spacing=10),
            ft.Divider(),
            ft.Text("Datenbank Status"),
            ft.Text("LLM Service Status"),
        ])

    def _new_scraper_config(self, e):
        self._show_config_form()

    def _trigger_scraper(self, e):
        """Trigger scraper manually."""
        self.scraper_running = True
        self.page.update()
        
        import asyncio
        asyncio.create_task(self._trigger_scraper_async())

    async def _trigger_scraper_async(self):
        """Async scraper trigger."""
        try:
            async with self.api_client as client:
                response = await client.trigger_scraper()
                if response.success:
                    self._show_snackbar("✅ Scraper gestartet")
                    await self._load_scraper_status()
                else:
                    self._show_snackbar(f"Scraper Fehler: {response.error}")
        except Exception as e:
            log.error(f"Error triggering scraper: {e}")
            self._show_snackbar(f"Fehler beim Starten: {e}")
        finally:
            self.scraper_running = False
            self.page.update()

    async def _load_scraper_status(self):
        """Load scraper status from API."""
        try:
            async with self.api_client as client:
                response = await client.get_scraper_status()
                if response.success:
                    self.scraper_status_info = response.data
        except Exception as e:
            log.error(f"Error loading scraper status: {e}")

    def _show_scraper_status(self, e):
        """Show scraper status dialog."""
        status = self.scraper_status_info.get("status", "Unbekannt")
        last_run = self.scraper_status_info.get("last_run", "Nie")
        current_city = self.scraper_status_info.get("current_city", "N/A")
        platforms = ", ".join(self.scraper_status_info.get("active_platforms", []))
        
        content = f"""Scraper Status: {status}
Letzter Lauf: {last_run}
Aktuelle Stadt: {current_city}
Aktive Plattformen: {platforms}"""
        
        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Scraper Status"),
            content=ft.Text(content),
            actions=[
                ft.TextButton("Schließen", on_click=lambda e: setattr(self.page.dialog, "open", False))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog.open = True
        self.page.update()

    def _handle_config_edit(self, config, menu):
        menu.open = False
        self.page.update()
        self._show_config_form(config)

    def _handle_config_delete(self, config, menu):
        menu.open = False
        self.page.update()
        self._delete_scraper_config(config.get('platform_name'))


    def _edit_scraper_config(self, config):
        self._show_config_form(config)

    async def _show_config_form(self, config=None):
        """Show config form with API save."""
        async def on_save(data):
            try:
                async with self.api_client as client:
                    # Use PUT for updates, POST for creates
                    platform_name = data.get('platform_name')
                    if config and platform_name:
                        # Update existing config
                        response = await client._request(
                            "PUT",
                            f"/admin/scraper-configs/{platform_name}",
                            json_data=data
                        )
                    else:
                        # Create new config
                        response = await client._request(
                            "POST",
                            "/admin/scraper-configs",
                            json_data=data
                        )
                    
                    if response.success:
                        self._show_snackbar("Konfiguration gespeichert")
                        await self._load_scraper_configs_api()
                        self._refresh_current_tab()
                    else:
                        self._show_snackbar(f"Fehler: {response.error}")
            except Exception as e:
                self._show_snackbar(f"Fehler: {e}")
        
        form = ScraperConfigForm(config=config, on_save=on_save)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Scraper Konfiguration"),
            content=ft.Container(content=form, width=800, height=600),
            actions=[
                ft.TextButton("Schließen", on_click=lambda e: setattr(dialog, "open", False))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _new_feature_request(self, e):
        async def on_submit(data):
            try:
                async with self.api_client as client:
                    response = await client._request(
                        "POST",
                        "/admin/feature-requests",
                        json_data=data
                    )
                    if response.success:
                        self._show_snackbar("Feature Request erstellt")
                        await self._load_feature_requests_api()
                    else:
                        self._show_snackbar(f"Fehler: {response.error}")
            except Exception as e:
                self._show_snackbar(f"Fehler: {e}")
        
        dialog = FeatureRequestDialog(on_submit=on_submit)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _handle_request_edit(self, req, menu):
        menu.open = False
        self.page.update()
        self._edit_feature_request(req)

    def _handle_request_delete(self, req, menu):
        menu.open = False
        self.page.update()
        self._delete_feature_request(req)

    async def _delete_feature_request(self, req):
        """Delete feature request with confirmation."""
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Feature Request löschen"),
            content=ft.Text(f"Möchten Sie den Feature Request für {req.get('platform_name')} wirklich löschen?"),
            actions=[
                ft.TextButton("Abbrechen", on_click=lambda e: setattr(confirm_dialog, "open", False)),
                ft.FilledButton("Löschen", on_click=lambda e: self._confirm_delete_request(req, confirm_dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    async def _confirm_delete_request(self, req, dialog):
        """Confirm and delete request."""
        dialog.open = False
        self.page.update()
        try:
            async with self.api_client as client:
                response = await client._request(
                    "DELETE",
                    f"/admin/feature-requests/{req.get('id')}"
                )
                if response.success:
                    self._show_snackbar("Feature Request gelöscht")
                    await self._load_feature_requests_api()
                    self._refresh_current_tab()
                else:
                    self._show_snackbar(f"Fehler: {response.error}")
        except Exception as e:
            self._show_snackbar(f"Fehler: {e}")

    async def _edit_feature_request(self, req):
        """Edit feature request status and description."""
        async def on_submit(request_id, data):
            try:
                async with self.api_client as client:
                    response = await client._request(
                        "PUT",
                        f"/admin/feature-requests/{request_id}",
                        json_data=data
                    )
                    if response.success:
                        self._show_snackbar("Feature Request aktualisiert")
                        await self._load_feature_requests_api()
                        self._refresh_current_tab()
                    else:
                        self._show_snackbar(f"Fehler: {response.error}")
            except Exception as e:
                self._show_snackbar(f"Fehler: {e}")
        
        dialog = FeatureRequestEditDialog(req, on_submit)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _show_snackbar(self, message: str):
        """Show snackbar message."""
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
