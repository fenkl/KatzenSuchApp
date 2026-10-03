# KatzenSuchApp FastAPI Backend

REST API for KatzenSuchApp - Cat shelter scraper backend.

## Installation

```bash
pip install fastapi uvicorn pydantic
```

## Running the API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Endpoints

**Gesamt: 38 Endpunkte über 7 Router**

### Health - 1 Route
- `GET /api/v1/health/health` - Health check mit DB-Status

### Auth - 9 Routen
- `POST /api/v1/auth/login` - Login mit username/password
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/users` - User anlegen
- `GET /api/v1/auth/users/{user_id}` - User abrufen
- `DELETE /api/v1/auth/users/{user_id}` - User deaktivieren
- `PUT /api/v1/auth/users/{user_id}/password` - Passwort ändern
- `GET /api/v1/auth/admin/users` - Userliste Admin

### Listings - 9 Routen
- `GET /api/v1/listings/` - List listings with filters
- `GET /api/v1/listings/{listing_id}` - Get single listing
- `GET /api/v1/listings/search` - Suche
- `GET /api/v1/listings/platform/{platform_name}` - Nach Plattform filtern
- `GET /api/v1/listings/matching` - Matching Listings
- `GET /api/v1/listings/stats/summary` - Statistiken
- `GET /api/v1/listings/cities` - Städte auflisten
- `GET /api/v1/listings/platforms` - Plattformen auflisten
- `POST /api/v1/listings/mark-processed` - Als verarbeitet markieren

### Platforms - 1 Route
- `GET /api/v1/platforms/` - List platforms

### Admin - 12 Routen
- `GET /api/v1/admin/configs` - Get app configs
- `GET /api/v1/admin/scraper-configs` - Scraper Konfigurationen
- `GET /api/v1/admin/scraper-configs/{platform_name}` - Einzelne Config
- `POST /api/v1/admin/scraper-configs` - Config anlegen
- `PUT /api/v1/admin/scraper-configs/{platform_name}` - Config aktualisieren
- `DELETE /api/v1/admin/scraper-configs/{platform_name}` - Config löschen
- `GET /api/v1/admin/feature-requests` - List feature requests
- `GET /api/v1/admin/feature-requests/{request_id}` - Single request
- `POST /api/v1/admin/feature-requests` - Request anlegen
- `PUT /api/v1/admin/feature-requests/{request_id}` - Request aktualisieren
- `DELETE /api/v1/admin/feature-requests/{request_id}` - Request löschen
- `GET /api/v1/admin/platforms` - Plattformen Admin

### Scraper - 3 Routen
- `POST /api/v1/scraper/trigger` - Manueller Trigger
- `GET /api/v1/scraper/status` - Get scraper status
- `GET /api/v1/scraper/configs` - Get scraper configs

### Classifications - 3 Routen
- `GET /api/v1/classifications/` - List LLM classifications
- `GET /api/v1/classifications/{url_hash}` - Get classification
- `POST /api/v1/classifications/batch` - Batch classification

## Development

The API uses:
- FastAPI for REST endpoints
- Pydantic for data validation
- SQLite for database (via existing modules)
- CORS enabled for Android clients

## Architecture

```
api/
├── main.py              # FastAPI app entry
├── core_security.py     # Security helpers
├── dependencies.py      # DB and config dependencies
├── __init__.py
├── README.md
├── models/
│   ├── schemas.py       # Pydantic models
│   └── __init__.py
├── routers/
│   ├── __init__.py
│   ├── health.py        # 1 Route
│   ├── auth.py          # 9 Routen
│   ├── listings.py      # 9 Routen
│   ├── platforms.py     # 1 Route
│   ├── admin.py         # 12 Routen
│   ├── scraper.py       # 3 Routen
│   └── classifications.py # 3 Routen
└── services/            # vorhanden
```

## Router Integration

```python
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(listings.router, prefix="/api/v1/listings")
app.include_router(platforms.router, prefix="/api/v1/platforms")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(scraper.router, prefix="/api/v1/scraper")
app.include_router(classifications.router, prefix="/api/v1/classifications")
```

**Stand:** 2026-10-02
