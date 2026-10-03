#!/usr/bin/env python3
"""
run_dev.py - Development runner for KatzenSuchApp.

This script provides convenient entry points for developers to run
the Flet UI, scraper orchestrator, or both in development mode.

Usage:
    python run_dev.py ui              # Start Flet UI
    python run_dev.py ui --port 8080  # UI on custom port
    python run_dev.py scraper --once  # Run scraper once
    python run_dev.py scraper         # Run scraper loop
    python run_dev.py both            # Run UI + scraper together
    python run_dev.py test            # Run tests
"""

import sys
import asyncio
import argparse
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs" / "flet_base"))

from classes.Cconfig import Config
from modules.Mhandle_log import get_logger

log = get_logger(__name__)

# Configure from .env
config = Config()


def run_ui(host: str = "0.0.0.0", port: int = 8080, web: bool = True, mode: str = "ui"):
    """Run Flet UI in development mode."""
    import flet as ft
    
    # Configure paths
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "libs" / "flet_base"))
    
    from flet_base.core.app import BaseApp
    from flet_base.core.db import init_db, seed_defaults
    from flet_base.core.config import configure
    from flet_app.ui.dashboard import DashboardPage
    from flet_app.ui.admin.admin_page import AdminPage
    
    # Configure FletBase with dev settings
    configure(
        db_path=config.auth_db_path,
        session_timeout_minutes=60,
        theme_mode="light",
    )
    
    # Initialize auth DB
    init_db(config.auth_db_path)
    seed_defaults()
    
    # Register pages
    app = BaseApp(pages={
        "/dashboard": DashboardPage,
        "/admin": AdminPage,
    })
    
    def main(page: ft.Page):
        page.title = "KatzenSuchApp - Dev"
        # Set scraper mode on DashboardPage instances
        for route, page_cls in app.pages.items():
            if page_cls == DashboardPage:
                # Store mode in class variable for access in build
                DashboardPage.scraper_mode = mode
        app.build(page)
    
    log.info(f"Starting KatzenSuchApp UI on {host}:{port} (web={web})")
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER if web else ft.AppView.FLET_APP,
        host=host,
        port=port,
        assets_dir=None,
    )


async def run_scraper(interval_minutes: int = None, once: bool = False):
    """Run scraper orchestrator in development mode."""
    from modules.services.orchestrator import orchestrator
    
    if interval_minutes is None:
        interval_minutes = config.scraper_interval_minutes
    
    log.info("Starting KatzenSuchApp Scraper in dev mode")
    log.info(f"Interval: {interval_minutes} minutes")
    log.info(f"Cities: {', '.join(config.cities)}")
    log.info(f"Platforms: {', '.join(orchestrator.scrapers.keys())}")
    
    if once:
        log.info("Running single iteration (--once)")
        result = await orchestrator.run_once()
        log.info(f"Single run complete, city: {result['city']}")
        total = sum(len(v) for v in result['results'].values())
        log.info(f"Total listings found: {total}")
        return
    
    # Run main loop
    try:
        await orchestrator.run_loop(interval_minutes)
    except KeyboardInterrupt:
        log.info("Scraper stopped by user")
        orchestrator.stop()


async def run_both(ui_host: str = "127.0.0.1", ui_port: int = 8080, scraper_interval: int = None):
    """Run both UI and scraper concurrently in dev mode."""
    import flet as ft
    import threading
    
    log.info("Starting KatzenSuchApp dev mode - UI + Scraper")
    
    # Start scraper in background task
    async def scraper_task():
        from modules.services.orchestrator import orchestrator
        if scraper_interval is None:
            scraper_interval = config.scraper_interval_minutes
        log.info(f"Scraper running with {scraper_interval} minute interval")
        await orchestrator.run_loop(scraper_interval)
    
    # Start UI in main thread
    from flet_base.core.app import BaseApp
    from flet_base.core.db import init_db, seed_defaults
    from flet_base.core.config import configure
    from flet_app.ui.dashboard import DashboardPage
    from flet_app.ui.admin.admin_page import AdminPage
    
    configure(
        db_path=config.auth_db_path,
        session_timeout_minutes=60,
        theme_mode="light",
    )
    
    init_db(config.auth_db_path)
    seed_defaults()
    
    app = BaseApp(pages={
        "/dashboard": DashboardPage,
        "/admin": AdminPage,
    })
    
    def main(page: ft.Page):
        page.title = "KatzenSuchApp - Dev"
        # Set scraper mode to both
        DashboardPage.scraper_mode = "both"
        app.build(page)
    
    # Run scraper in background thread
    scraper_thread = threading.Thread(
        target=lambda: asyncio.run(scraper_task()),
        daemon=True
    )
    scraper_thread.start()
    
    log.info(f"UI starting on {ui_host}:{ui_port}")
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host=ui_host,
        port=ui_port,
        assets_dir=None,
    )


def main():
    parser = argparse.ArgumentParser(description="KatzenSuchApp Development Runner")
    parser.add_argument(
        "command",
        choices=["ui", "scraper", "both", "test", "api"],
        nargs="?",
        default="ui",
        help="Command to run: ui, scraper, both, api, or test"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for UI server (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Port for UI server (default: 8080)"
    )
    
    parser.add_argument(
        "--web",
        action="store_true",
        default=True,
        help="Run UI in web browser mode (default: True)"
    )
    
    parser.add_argument(
        "--no-web",
        dest="web",
        action="store_false",
        help="Run UI in desktop app mode"
    )
    
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=None,
        help="Scraper interval in minutes"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run scraper once and exit"
    )
    
    parser.add_argument(
        "--db",
        help="Override database path"
    )
    
    args = parser.parse_args()
    
    # Override config if specified
    if args.db:
        config.db_path = args.db
        log.info(f"Using custom DB path: {args.db}")
    
    log.info("=" * 60)
    log.info("KatzenSuchApp Development Runner")
    log.info(f"DB: {config.db_path}")
    log.info(f"Cities: {', '.join(config.cities)}")
    log.info(f"Ollama: {config.ollama_url}")
    log.info("=" * 60)
    
    if args.command == "ui":
        run_ui(host=args.host, port=args.port, web=args.web, mode="ui")
    
    elif args.command == "scraper":
        if args.once:
            asyncio.run(run_scraper(interval_minutes=args.interval, once=True))
        else:
            asyncio.run(run_scraper(interval_minutes=args.interval))
    
    elif args.command == "both":
        asyncio.run(run_both(ui_host=args.host, ui_port=args.port, scraper_interval=args.interval))
    
    elif args.command == "api":
        import uvicorn
        from api.main import app
        api_port = int(os.getenv("API_PORT", "5000"))
        uvicorn.run(app, host="0.0.0.0", port=api_port, reload=True)
    elif args.command == "test":
        print("Running tests...")
        print("python -m pytest tests/ -v")
        import os
        os.system("python -m pytest tests/ -v")
        print("\nRunning integration test specifically:")
        os.system("python tests/test_integration_scrape_llm_db.py")


if __name__ == "__main__":
    main()
