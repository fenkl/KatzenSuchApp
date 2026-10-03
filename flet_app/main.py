"""KatzenSuchApp Flet Entry Point with FletBase integration."""

import sys
from pathlib import Path

# Add project root and libs/flet_base to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs" / "flet_base"))

import flet as ft
from flet_base.core.db import init_db, seed_defaults
from flet_base.core.config import configure
from classes.Cconfig import Config

from flet_app.custom_app import KatzenSuchApp
from flet_app.ui.dashboard import DashboardPage
from flet_app.ui.admin.admin_page import AdminPage

# Configure FletBase
config = Config()
configure(
    db_path=config.auth_db_path,
    session_timeout_minutes=60,
    theme_mode="light",
)

# Initialize auth DB
init_db(config.auth_db_path)
seed_defaults()

# Register pages with custom app - using API-enabled versions
app = KatzenSuchApp(pages={
    "/dashboard": DashboardPage,
    "/admin": AdminPage,
})
# Default route for app start
app.default_route = "/dashboard"

def main(page: ft.Page):
    app.build(page)

if __name__ == "__main__":
    ft.run(main)
