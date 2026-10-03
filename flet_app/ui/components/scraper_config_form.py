"""Scraper Config Form Component for Admin."""

import flet as ft
from typing import Callable, Dict, Optional


class ScraperConfigForm(ft.Column):
    def __init__(self, config: Optional[Dict] = None, on_save: Callable = None, on_test: Callable = None, on_cancel: Callable = None):
        super().__init__()
        self.config = config or {}
        self.on_save = on_save
        self.on_test = on_test
        self.on_cancel = on_cancel

        self.platform_name = ft.TextField(label="Plattform Name", value=self.config.get("platform_name", ""))
        self.base_url = ft.TextField(label="Base URL", value=self.config.get("base_url", ""))
        self.listing_selector = ft.TextField(label="Listing Selector", value=self.config.get("listing_selector", ""))
        self.detail_selector = ft.TextField(label="Detail Selector", value=self.config.get("detail_selector", ""))
        self.pagination_param = ft.TextField(label="Pagination Param", value=self.config.get("pagination_param", ""))
        self.city_param = ft.TextField(label="City Param", value=self.config.get("city_param", ""))
        self.enabled = ft.Checkbox(label="Aktiv", value=bool(self.config.get("enabled", 1)))
        self.handler_class = ft.TextField(label="Handler Class", value=self.config.get("handler_class", ""))
        self.login_required = ft.Checkbox(label="Login erforderlich", value=bool(self.config.get("login_required", 0)))

        self.controls = [
            ft.Text("Scraper Konfiguration", size=20, weight=ft.FontWeight.BOLD),
            self.platform_name,
            self.base_url,
            self.listing_selector,
            self.detail_selector,
            ft.Row([self.pagination_param, self.city_param], spacing=10),
            self.enabled,
            self.handler_class,
            self.login_required,
            ft.Row([
                ft.FilledButton("Speichern", on_click=self._save),
                ft.OutlinedButton("Test", on_click=self._test) if self.on_test else ft.Container(),
                ft.OutlinedButton("Abbrechen", on_click=self._cancel),
            ], spacing=10),
        ]

    def _collect_data(self) -> Dict:
        return {
            "platform_name": self.platform_name.value.strip(),
            "base_url": self.base_url.value.strip(),
            "listing_selector": self.listing_selector.value.strip(),
            "detail_selector": self.detail_selector.value.strip(),
            "pagination_param": self.pagination_param.value.strip(),
            "city_param": self.city_param.value.strip(),
            "enabled": 1 if self.enabled.value else 0,
            "handler_class": self.handler_class.value.strip(),
            "login_required": 1 if self.login_required.value else 0,
        }

    def _save(self, e):
        if self.on_save:
            self.on_save(self._collect_data())

    def _test(self, e):
        if self.on_test:
            self.on_test(self._collect_data())
