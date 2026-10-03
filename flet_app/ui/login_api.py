"""API-enabled Login Page for FletBase + FastAPI JWT."""

from __future__ import annotations

import asyncio
import flet as ft
from flet_base.core.auth import login as flet_login
from flet_app.services.api_client import get_api_client
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


class LoginPageAPI(ft.Container):
    """Login page that authenticates via FastAPI API and sets FletBase session."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.username = ft.TextField(label="Benutzername", width=300, on_submit=self._on_login)
        self.password = ft.TextField(label="Passwort", password=True, can_reveal_password=True, width=300, on_submit=self._on_login)
        self.error = ft.Text("", color=ft.Colors.RED)
        self.loading = ft.ProgressRing(visible=False, width=24, height=24)
        # ElevatedButton was removed in flet >= 1.0, use FilledButton
        self.login_button = ft.FilledButton("Login", on_click=self._on_login)

        self.alignment = ft.alignment.Alignment.CENTER
        self.expand = True
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Text("KatzenSuchApp Login", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Bitte anmelden um fortzufahren", size=14, color=ft.Colors.GREY_400),
                self.username,
                self.password,
                ft.Row(
                    controls=[self.login_button, self.loading],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                self.error,
            ],
        )

    def _on_login(self, e):
        """Handle login click/submit."""
        user = self.username.value.strip()
        pwd = self.password.value or ""

        if not user or not pwd:
            self.error.value = "Benutzername und Passwort erforderlich"
            self.update()
            return

        # Disable UI
        self.login_button.disabled = True
        self.loading.visible = True
        self.error.value = ""
        self.update()

        async def do_login():
            try:
                client = get_api_client()
                # API login
                async with client as api_client:
                    resp = await api_client.login(user, pwd)
                    if not resp.success:
                        log.warning(f"API login failed for {user}: {resp.error}")
                        self.error.value = resp.error or "Login fehlgeschlagen"
                        return

                # API success -> set FletBase session
                ok, msg = flet_login(self.page, user, pwd)
                if not ok:
                    log.error(f"FletBase login failed: {msg}")
                    self.error.value = f"Session Fehler: {msg}"
                    # Clear token on failure
                    client.token = None
                    return

                # Store API token persistently in session store
                # This enables auto-login after page reload and token refresh
                try:
                    store = self.page.session.store
                    store.set("api_token", client.token)
                    store.set("api_credentials", {"username": user, "password": pwd})
                    log.info(f"API token stored in session store for {user}")
                except Exception as e:
                    log.warning(f"Could not store token in session: {e}")

                log.info(f"User {user} logged in via API + FletBase")
                self.page.navigate("/dashboard")

            except Exception as exc:
                log.exception("Login exception")
                self.error.value = f"Fehler: {exc}"
            finally:
                # Re-enable UI
                self.login_button.disabled = False
                self.loading.visible = False
                self.update()

        # Run async login
        asyncio.create_task(do_login())
