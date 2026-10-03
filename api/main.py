"""FastAPI main application for KatzenSuchApp API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, listings, platforms, auth, admin, scraper, classifications

app = FastAPI(
    title="KatzenSuchApp API",
    description="REST API for KatzenSuchApp - Cat shelter scraper",
    version="1.0.0"
)

# CORS configuration for Android and Web clients
# TODO: Restrict origins in production - currently open for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: ["https://katzensuchapp.com", "http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(listings.router, prefix="/api/v1/listings")
app.include_router(platforms.router, prefix="/api/v1/platforms")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(scraper.router, prefix="/api/v1/scraper")
app.include_router(classifications.router, prefix="/api/v1/classifications")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "KatzenSuchApp API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
