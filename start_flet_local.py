#!/usr/bin/env python3
"""
Local Flet UI Starter for LAN Testing
Runs Flet UI on 192.168.2.13:8080
"""

import os
import sys
from pathlib import Path

# Load .env.local
env_local = Path(__file__).resolve().parent / ".env.local"
if env_local.exists():
    from dotenv import load_dotenv
    load_dotenv(env_local)
    print(f"✓ Loaded .env.local")

# Add project paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs" / "flet_base"))

print("=" * 60)
print("KatzenSuchApp Flet UI - Local LAN Mode")
print("=" * 60)
print(f"API Base URL: {os.getenv('API_BASE_URL', 'http://192.168.2.13:5000')}")
print("Starting Flet UI...")
print("=" * 60)
print()

if __name__ == "__main__":
    import flet as ft
    from flet_app.main import main
    
    # Get UI port
    ui_port = int(os.getenv("FLET_PORT", "8080"))
    host = os.getenv("FLET_HOST", "0.0.0.0")
    
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=ui_port,
        assets_dir=None
    )
