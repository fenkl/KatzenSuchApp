#!/usr/bin/env python3
"""
Local API Server Starter for LAN Testing
Runs FastAPI on 192.168.2.13:5000
"""

import os
import uvicorn
from pathlib import Path

# Load .env.local
env_local = Path(__file__).resolve().parent / ".env.local"
if env_local.exists():
    from dotenv import load_dotenv
    load_dotenv(env_local)
    print(f"✓ Loaded .env.local")
else:
    print("⚠ .env.local not found, using defaults")

# Get port from env
port = int(os.getenv("API_PORT", "5000"))
api_host_raw = os.getenv("API_HOST", "http://192.168.2.13")
# Extract host without scheme for printing
host = api_host_raw.replace("http://", "").replace("https://", "")
# Use API_BASE_URL if set, else construct
api_base_url = os.getenv("API_BASE_URL", f"http://{host}:{port}")

print("=" * 60)
print("KatzenSuchApp API - Local LAN Mode")
print("=" * 60)
print(f"API Host: {host}")
print(f"API Port: {port}")
print(f"API URL: {api_base_url}")
print(f"Docs:    {api_base_url}/docs")
print("=" * 60)
print("Press Ctrl+C to stop")
print()

if __name__ == "__main__":
    # Use import string for app to enable reload/workers
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True
    )
