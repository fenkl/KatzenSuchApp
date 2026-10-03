"""Listing Card Component for KatzenSuchApp Dashboard."""

import flet as ft
from typing import Dict, Callable


class ListingCard(ft.Card):
    def __init__(self, listing: Dict, on_mark_processed: Callable, on_rate: Callable, on_feature_request: Callable):
        super().__init__()
        self.listing = listing
        self.on_mark_processed = on_mark_processed
        self.on_rate = on_rate
        self.on_feature_request = on_feature_request
        self.content = self._build_content()

    def _build_content(self):
        url = self.listing.get("url", "")
        platform = self.listing.get("platform", "")
        title = self.listing.get("title", "Ohne Titel")
        llm = self.listing.get("llm_classification", {})
        
        # Extract classification info
        age_ok = llm.get("age_ok", False)
        einzel_ok = llm.get("einzelgaenger_ok", False)
        freigang_ok = llm.get("freigang_ok", False)
        confidence = llm.get("confidence", 0.0)
        if confidence is None:
            confidence = 0.0
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        
        # Build status chips
        chips = []
        if age_ok:
            chips.append(ft.Container(content=ft.Text("✓ Alter 2-8J", size=10), bgcolor=ft.Colors.GREEN_100, padding=5))
        if einzel_ok:
            chips.append(ft.Container(content=ft.Text("✓ Einzelgänger", size=10), bgcolor=ft.Colors.BLUE_100, padding=5))
        if freigang_ok:
            chips.append(ft.Container(content=ft.Text("✓ Kein Freigang", size=10), bgcolor=ft.Colors.ORANGE_100, padding=5))
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(content=ft.Text(f"{confidence:.0%}", size=10), bgcolor=ft.Colors.GREY_200, padding=3)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Text(f"Plattform: {platform}", size=12, color=ft.Colors.GREY_600),
                ft.Text(url, size=10, color=ft.Colors.BLUE_400),
                ft.Row(controls=chips, spacing=5, wrap=True),
                ft.Row(
                    controls=[
                        ft.FilledButton("Als verarbeitet markieren", on_click=lambda e: self.on_mark_processed(url)),
                        ft.IconButton(ft.Icons.STAR, tooltip="Bewerten", on_click=lambda e: self.on_rate(url)),
                        ft.IconButton(ft.Icons.FEATURED_PLAY_LIST, tooltip="Feature Request", on_click=lambda e: self.on_feature_request(url)),
                    ],
                    spacing=10
                )
            ],
            spacing=10
        )
