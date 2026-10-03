"""Filter Panel Component for KatzenSuchApp Dashboard."""

import flet as ft
from typing import Callable


class FilterPanel(ft.Column):
    def __init__(self, on_filter_change: Callable):
        super().__init__()
        self.on_filter_change = on_filter_change
        self.age_min = ft.TextField(label="Alter min", value="2", width=100)
        self.age_max = ft.TextField(label="Alter max", value="8", width=100)
        self.einzelgaenger = ft.Checkbox(label="Einzelgänger geeignet", value=True)
        self.freigang = ft.Checkbox(label="Kein Freigang nötig", value=True)
        self.confidence_min = ft.Slider(min=0, max=1, divisions=10, value=0.7, label="{value}")

        self.controls = [
            ft.Text("Filter", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([self.age_min, self.age_max], spacing=10),
            self.einzelgaenger,
            self.freigang,
            ft.Text("Min. Confidence"),
            self.confidence_min,
            ft.FilledButton("Filter anwenden", on_click=self._apply_filter),
            ft.OutlinedButton("Filter zurücksetzen", on_click=self._reset_filter),
        ]

    def _apply_filter(self, e):
        filters = {
            "age_min": int(self.age_min.value or 0),
            "age_max": int(self.age_max.value or 99),
            "einzelgaenger": self.einzelgaenger.value,
            "freigang": self.freigang.value,
            "confidence_min": self.confidence_min.value,
        }
        self.on_filter_change(filters)

    def _reset_filter(self, e):
        self.age_min.value = "2"
        self.age_max.value = "8"
        self.einzelgaenger.value = True
        self.freigang.value = True
        self.confidence_min.value = 0.7
        self._apply_filter(e)
