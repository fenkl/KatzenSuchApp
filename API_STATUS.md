# FastAPI Backend Status

## Status: ✅ Grundgerüst erweitert und funktionsfähig

**Aktualisiert:** 2026-10-02 11:58:00 +02:00

### Implementierte Routen

Gesamt: **38 Endpunkte** über 7 Router

#### Health
- `GET /api/v1/health/health` - Health check mit DB-Status

#### Authentication
- `POST /api/v1/auth/login` - Login mit Mock-Token
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Current user
- `POST /api/v1/auth/users` - User anlegen
- `GET /api/v1/auth/users/{user_id}` - User abrufen
- `DELETE /api/v1/auth/users/{user_id}` - User deaktivieren
- `PUT /api/v1/auth/users/{user_id}/password` - Passwort ändern
- `GET /api/v1/auth/admin/users` - Userliste Admin

#### Listings
- `GET /api/v1/listings/` - Liste mit Filtern
- `GET /api/v1/listings/{listing_id}` - Einzelnes Listing
- `GET /api/v1/listings/search` - Suche
- `GET /api/v1/listings/platform/{platform_name}` - Nach Plattform
- `GET /api/v1/listings/matching` - Matching
- `GET /api/v1/listings/stats/summary` - Statistiken
- `GET /api/v1/listings/cities` - Städte
- `GET /api/v1/listings/platforms` - Plattformen
- `POST /api/v1/listings/mark-processed` - Als verarbeitet markieren

#### Platforms
- `GET /api/v1/platforms/` - Liste Plattformen

#### Admin
- `GET /api/v1/admin/configs` - App-Konfiguration
- `GET /api/v1/admin/scraper-configs` - Scraper Konfigurationen
- `GET /api/v1/admin/scraper-configs/{platform_name}` - Einzelne Config
- `POST /api/v1/admin/scraper-configs` - Config anlegen
- `PUT /api/v1/admin/scraper-configs/{platform_name}` - Config aktualisieren
- `DELETE /api/v1/admin/scraper-configs/{platform_name}` - Config löschen
- `GET /api/v1/admin/feature-requests` - Feature requests
- `GET /api/v1/admin/feature-requests/{request_id}` - Single request
- `POST /api/v1/admin/feature-requests` - Request anlegen
- `PUT /api/v1/admin/feature-requests/{request_id}` - Request aktualisieren
- `DELETE /api/v1/admin/feature-requests/{request_id}` - Request löschen
- `GET /api/v1/admin/platforms` - Plattformen Admin

#### Scraper
- `POST /api/v1/scraper/trigger` - Manueller Trigger
- `GET /api/v1/scraper/status` - Scraper Status
- `GET /api/v1/scraper/configs` - Scraper Konfigurationen

#### Classifications
- `GET /api/v1/classifications/` - LLM Klassifikationen Liste
- `GET /api/v1/classifications/{url_hash}` - Einzelne Klassifikation
- `POST /api/v1/classifications/batch` - Batch Klassifikation

### Dateien

```
api/
├── main.py                 # FastAPI App, CORS, Router-Include
├── core_security.py        # Security helpers
├── dependencies.py         # DB & Config dependencies
├── __init__.py
├── README.md
├── models/
│   ├── schemas.py          # Pydantic Models
│   └── __init__.py
├── routers/
│   ├── __init__.py
│   ├── health.py           # 1 Route
│   ├── auth.py             # 9 Routen
│   ├── listings.py         # 9 Routen
│   ├── platforms.py        # 1 Route
│   ├── admin.py            # 12 Routen
│   ├── scraper.py          # 3 Routen
│   └── classifications.py  # 3 Routen
└── services/               # vorhanden, leer
```

### Router-Integration
```python
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(listings.router, prefix="/api/v1/listings")
app.include_router(platforms.router, prefix="/api/v1/platforms")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(scraper.router, prefix="/api/v1/scraper")
app.include_router(classifications.router, prefix="/api/v1/classifications")
```

### Tests / Betrieb
- OpenAPI/Swagger unter `/docs`
- ReDoc unter `/redoc`
- CORS offen für Entwicklung
- Root Endpoint `/` mit Version 1.0.0

### Abweichungen zu vorheriger Dokumentation
- Vorher dokumentiert: 13 Routen
- Aktuell vorhanden: 38 Routen
- Neue Router-Erweiterungen: auth User-Management, admin scraper-configs CRUD, listings Erweiterungen
- Zusätzliche Dateien: `core_security.py`, `services/`

### Nächste Schritte
1. JWT Auth implementieren und gegen echte User DB prüfen
2. Repository Pattern in API konsistent nutzen
3. Authentifizierung für schreibende Endpunkte verschärfen
4. Integration Tests für API Endpunkte ergänzen
5. Flet UI auf API umstellen
