"""Enhanced Feature Request Dialog Components."""

import flet as ft
from flet_base.ui.components.dialogs import ConfirmDialog


class FeatureRequestEditDialog(ft.AlertDialog):
    """Dialog for editing feature request status and description."""
    
    def __init__(self, request: dict, on_submit):
        super().__init__()
        self.on_submit = on_submit
        self.request = request
        self.request_id = request.get("id")
        
        self.status_choices = ["open", "in_progress", "completed", "rejected"]
        self.status_dropdown = ft.Dropdown(
            label="Status",
            options=[ft.dropdown.Option(s) for s in self.status_choices],
            value=request.get("status", "open"),
            width=300
        )
        
        self.description = ft.TextField(
            label="Beschreibung",
            multiline=True,
            min_lines=3,
            max_lines=5,
            value=request.get("description", ""),
            width=300
        )
        
        self.content = ft.Column([
            ft.Text("Feature Request bearbeiten", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(f"Plattform: {request.get('platform_name', '')}", size=14),
            ft.Text(f"URL: {request.get('start_url', '')}", size=12, color=ft.Colors.GREY_600),
            self.status_dropdown,
            self.description,
        ], spacing=10)
        
        self.actions = [
            ft.TextButton("Abbrechen", on_click=self._cancel),
            ft.FilledButton("Speichern", on_click=self._submit),
        ]
        self.open = False
    
    def _cancel(self, e):
        self.open = False
    
    def _submit(self, e):
        data = {
            "status": self.status_dropdown.value,
            "description": self.description.value.strip(),
        }
        self.on_submit(self.request_id, data)
        self.open = False


class FeatureRequestDialog(ft.AlertDialog):
    """Dialog for creating new feature request."""
    
    def __init__(self, on_submit):
        super().__init__()
        self.on_submit = on_submit
        self.platform_name = ft.TextField(label="Plattform Name", width=300)
        self.start_url = ft.TextField(label="Start URL", width=300)
        self.example_url = ft.TextField(label="Beispiel Listing URL", width=300)
        self.description = ft.TextField(label="Beschreibung", multiline=True, min_lines=3, max_lines=5, width=300)

        self.content = ft.Column(
            controls=[
                ft.Text("Feature Request erstellen", size=18, weight=ft.FontWeight.BOLD),
                self.platform_name,
                self.start_url,
                self.example_url,
                self.description,
            ],
            spacing=10
        )
        self.actions = [
            ft.TextButton("Abbrechen", on_click=self._cancel),
            ft.FilledButton("Erstellen", on_click=self._submit),
        ]
        self.open = False

    def _cancel(self, e):
        self.open = False

    def _submit(self, e):
        data = {
            "platform_name": self.platform_name.value.strip(),
            "start_url": self.start_url.value.strip(),
            "example_listing_url": self.example_url.value.strip(),
            "description": self.description.value.strip(),
        }
        if data["platform_name"] and data["start_url"]:
            self.on_submit(data)
            self.open = False
            # Reset fields
            self.platform_name.value = ""
            self.start_url.value = ""
            self.example_url.value = ""
            self.description.value = ""


# Alternative simple dialog using ConfirmDialog pattern
class FeatureRequestSimpleDialog(ft.AlertDialog):
    def __init__(self, url: str, on_confirm):
        super().__init__()
        self.url = url
        self.on_confirm = on_confirm
        self.title = ft.Text("Feature Request")
        self.content = ft.Column([
            ft.Text(f"Feature Request für URL:"),
            ft.Text(url, size=12, color=ft.Colors.GREY_600),
            ft.TextField(label="Beschreibung", multiline=True, min_lines=2),
        ])
        self.actions = [
            ft.TextButton("Abbrechen", on_click=lambda e: setattr(self, "open", False)),
            ft.FilledButton("Erstellen", on_click=self._confirm),
        ]
        self.open = False

    def _confirm(self, e):
        self.on_confirm(self.url)
        self.open = False
