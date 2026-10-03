# KatzenSuchApp

**Automatiserte Scraper- & Filter-Lösung für Katzenvermittlungen mit Domain-Driven Design**

KatzenSuchApp scraped Tierheim-Websites, filtert Tier-Listings mittels LLM nach Kriterien wie Alter, Einzelgänger-Eignung und Freigang und stellt die Ergebnisse über eine Flet-basierte UI bereit. Die Architektur folgt nach dem Refactoring einem Clean Architecture / Domain-Driven Design Ansatz mit klarer Trennung zwischen Domain, Repositories, Services und API.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flet](https://img.shields.io/badge/UI-Flet-green.svg)](https://flet.dev)

## 🎯 Überblick

Das System erkennt neue Katzen-Listings auf mehreren Plattformen, klassifiziert sie mittels LLM-Filter und macht sie über eine Web-UI verfügbar. Authentifizierung läuft über FletBase, Scraper läuft als Hintergrund-Service.

### Kernfeatures

- **Multi-Plattform Scraping**: Tierheimhelden, Shelta, Leipziger Land u.a.
- **LLM-gestütztes Filtering**: Klassifikation via Ollama (Phi-4-mini)
- **Admin-UI**: Scraper-Config CRUD, Feature Requests, Ratings, System Steuerung
- **API-First**: REST API für alle Operationen, Flet UI konsumiert API
- **Domain Layer**: Clean Architecture mit Domain Entities, Repositories, Services
- **Echtzeit-Scraper Steuerung**: Manueller Trigger via API und Admin UI

## 🏗️ Architektur nach Refactoring

```
┌─────────────────────────────────────────────────────────────┐
│                     Flet UI Layer                            │
│  flet_app/ui/dashboard.py, admin/admin_page.py              │
│  flet_app/services/api_client.py                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                     API Layer                                │
│  api/routers/ (FastAPI)                                      │
│  - admin.py, listings.py, scraper.py, auth.py                │
│  api/models/schemas.py (Pydantic)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ Dependency Injection
┌──────────────────────▼──────────────────────────────────────┐
│                   Service Layer                              │
│  core/services/                                              │
│  - listing_service, scraper_service, classification_service │
│  - feature_request_service, platform_service, auth_service   │
│  modules/services/orchestrator.py (Legacy)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Repository Layer                             │
│  core/repositories/                                          │
│  - listing_repository, platform_repository                   │
│  - feature_request_repository, classification_repository     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Domain Layer                                │
│  core/domain/                                                │
│  - Listing, PlatformConfig, FeatureRequest, Classification   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Database Layer                             │
│  SQLite: gesehen.db, flet_app/data/auth.db                   │
│  modules/db_utils.py (Legacy Utilities)                      │
└─────────────────────────────────────────────────────────────┘
```

### Legacy Komponenten (kompatibel)

- `modules/services/orchestrator.py`: Stadt-Rotation & Scraping Loop
- `modules/scraper/`: Platform-spezifische Scraper mit BaseScraper
- `modules/db_utils.py`: Direkte SQLite Operationen
- `classes/Cconfig.py`: Central Configuration

### Neue Domain-Architektur

**Core Domain (`core/`)**

```python
core/
├── domain/              # Entities & Value Objects
│   ├── listing.py       # Listing Entity
│   ├── config.py        # PlatformConfig, ScraperConfig
│   ├── feature_request.py
│   └── classification.py
├── repositories/        # Data Access Abstraction
│   ├── listing_repository.py
│   ├── platform_repository.py
│   └── ...
├── services/           # Business Logic
│   ├── listing_service.py
│   ├── scraper_service.py
│   └── ...
└── ...
```

**API Layer (`api/`)**

FastAPI Anwendung mit Routern für:
- `admin` - Scraper Config CRUD, Feature Requests
- `listings` - Listing Abfrage mit Server-Side Filtering
- `scraper` - Trigger & Status
- `auth` - JWT Auth via FletBase

## 📋 Voraussetzungen

### Server (Linode / Linux)
- Python 3.11+
- Linux Debian/Ubuntu
- SQLite3
- Playwright Firefox Browser
- Netzwerkzugang via Tailscale zu Home AI Server
- `python-dotenv`, `flet`, `playwright`, `aiohttp`, `fastapi`

### Home AI
- Ollama installiert
- Modell `phi-4-mini` geladen
- Erreichbar unter `http://home-ai:11434/api/chat`
- Tailscale Node mit festem Hostnamen

## 🚀 Installation

### 1. Repository klonen
```bash
cd /home/cesco/PycharmProjects
git clone <repo-url> KatzenSuchApp
cd KatzenSuchApp
```

### 2. Virtuelle Umgebung
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
# oder
pip install .
```

### 3. Playwright Browser
```bash
python3 -m playwright install firefox
python3 -m playwright install-deps firefox
```

### 4. Konfiguration
```bash
cp .env.example .env
# .env anpassen
```

**.env Beispiel:**
```env
# Database
DB_PATH=./gesehen.db
AUTH_DB_PATH=./flet_app/data/auth.db

# Ollama LLM
OLLAMA_URL=http://home-ai:11434/api/chat
OLLAMA_MODEL=phi-4-mini
OLLAMA_TIMEOUT=30

# App Config
CITIES=Berlin,Hamburg,München,Köln,Frankfurt,Stuttgart,Dresden,Leipzig,Düsseldorf,Hannover
SCRAPER_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
NO_BOT=false

# API
API_HOST=http://192.168.2.13
API_PORT=5000
API_BASE_URL=http://192.168.2.13:5000
CORS_ORIGINS=*

# JWT
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### 5. Datenbank initialisieren
```bash
python3 -c "from modules.db_utils import init_db; init_db()"
python3 -c "from flet_base.core.db import init_db, seed_defaults; init_db('./flet_app/data/auth.db'); seed_defaults()"
```

## 🏃 Services starten

### API Server
```bash
# Lokal
./start_api_local.py

# Oder manuell
uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload

# Produktiv
python3 start_api_local.py
```

API läuft auf: http://localhost:5000
Docs: http://localhost:5000/docs

### Flet UI
```bash
# Lokal
./start_flet_local.py

# Oder manuell
python3 flet_app/main.py --web --port 8080
```

UI läuft auf: http://localhost:8080

### Scraper Orchestrator (Legacy)
```bash
python3 -m modules.services.orchestrator
```

Für Produktivbetrieb als Systemd Service:
```bash
# /etc/systemd/system/katzensuchapp-api.service
[Unit]
Description=KatzenSuchApp API
After=network.target

[Service]
Type=simple
User=cesco
WorkingDirectory=/home/cesco/PycharmProjects/KatzenSuchApp
Environment="PATH=/home/cesco/PycharmProjects/KatzenSuchApp/.venv/bin"
ExecStart=/home/cesco/PycharmProjects/KatzenSuchApp/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable katzensuchapp-api
sudo systemctl start katzensuchapp-api
```

## 📚 API Dokumentation

### Authentifizierung
Alle Endpunkte außer `/health` benötigen JWT Bearer Token.

```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password"
}
```

### Listings
```bash
# Gefilterte Listings abrufen
GET /api/v1/listings?
  age_min=0&
  age_max=15&
  einzelgaenger=true&
  freigang_noetig=false&
  min_confidence=0.7&
  city=Leipzig&
  platform=tierheimhelden

# Listing als verarbeitet markieren
POST /api/v1/listings/mark-processed
{"listing_id": 123}
```

### Admin
```bash
# Scraper Config CRUD
GET    /api/v1/admin/scraper-configs
POST   /api/v1/admin/scraper-configs
PUT    /api/v1/admin/scraper-configs/{platform_name}
DELETE /api/v1/admin/scraper-configs/{platform_name}

# Feature Requests
GET    /api/v1/admin/feature-requests
POST   /api/v1/admin/feature-requests
PUT    /api/v1/admin/feature-requests/{id}
DELETE /api/v1/admin/feature-requests/{id}
```

### Scraper Steuerung
```bash
# Scraper manuell triggern
POST /api/v1/scraper/trigger?platform=tierheimhelden&city=Leipzig&max_pages=3

# Scraper Status
GET /api/v1/scraper/status

# Scraper Configs
GET /api/v1/scraper/configs
```

## 🎨 UI Nutzung

### Login
- Flet UI starten
- Admin Login: Siehe Auth DB

### Dashboard
- **Filter Panel**: Alter, Einzelgänger, Freigang, Confidence
- **Listings Tabelle**: Alle gefilterten Ergebnisse
- **Aktualisieren Button**: Trigger Scraper via API
- **Pagination**: Seitenweise Navigation

### Admin Bereich

**Plattformen & Scraper Tab:**
- Liste aller Scraper Configs
- CRUD Operationen via Dialog
- Felder: platform_name, base_url, listing_selector, detail_selector, pagination_param, city_param, enabled, handler_class, login_required

**Feature Requests Tab:**
- Anzeigen neuer Feature Requests
- Status ändern: pending → in_progress → completed
- Erstellen neuer Requests

**Ratings Tab:**
- Bewertungen verwalten (Platzhalter)

**System Tab:**
- **Scraper Steuerung**: Manueller Start, Status Anzeige
- Datenbank Status
- LLM Service Status

## 🧪 Tests

```bash
# Alle Tests
pytest tests/ -v

# Spezifische Tests
pytest tests/test_feature_request_workflow.py -v
pytest tests/test_scraper_config_crud.py -v

# Mit Coverage
pytest tests/ --cov=core --cov=api -v
```

**Test Coverage:**
- Feature Request Workflow (9 Tests)
- Scraper Config CRUD (12 Tests)
- Integration Scrape/LLM/DB (bestehend)

## 📁 Projekt Struktur

```
KatzenSuchApp/
├── api/                          # FastAPI Application
│   ├── main.py                   # App Entry Point
│   ├── routers/                  # Route Handlers
│   │   ├── admin.py             # Admin CRUD
│   │   ├── listings.py          # Listing Query
│   │   ├── scraper.py           # Scraper Control
│   │   └── auth.py              # Authentication
│   ├── models/schemas.py        # Pydantic Models
│   └── dependencies.py          # DI & Auth Guards
│
├── core/                        # Domain Layer
│   ├── domain/                  # Entities
│   │   ├── listing.py
│   │   ├── config.py
│   │   ├── feature_request.py
│   │   └── classification.py
│   ├── repositories/            # Data Access
│   │   ├── listing_repository.py
│   │   ├── platform_repository.py
│   │   └── ...
│   └── services/               # Business Logic
│       ├── listing_service.py
│       ├── scraper_service.py
│       ├── classification_service.py
│       └── ...
│
├── flet_app/                   # Flet UI
│   ├── main.py                 # Flet App Entry
│   ├── custom_app.py           # App Wrapper
│   ├── services/api_client.py  # API Client
│   └── ui/
│       ├── dashboard.py        # Main Dashboard
│       ├── login_api.py        # Login Page
│       └── admin/
│           └── admin_page.py   # Admin Interface
│
├── modules/                    # Legacy & Utilities
│   ├── db_utils.py             # SQLite Helpers
│   ├── Mhandle_log.py          # Logging
│   ├── scraper/                # Platform Scrapers
│   │   ├── base.py
│   │   ├── tierheimhelden.py
│   │   └── ...
│   └── services/
│       ├── orchestrator.py     # Scraper Loop
│       └── scraper_service.py  # Legacy Service
│
├── classes/
│   └── Cconfig.py              # Configuration Loader
│
└── tests/                      # Test Suite
    ├── test_feature_request_workflow.py
    ├── test_scraper_config_crud.py
    └── test_integration_scrape_llm_db.py
```

## 🔧 Entwicklung

### Domain Layer erweitern

**Neue Entity:**
```python
# core/domain/new_entity.py
class NewEntity:
    def __init__(self, ...):
        ...
```

**Repository:**
```python
# core/repositories/new_repository.py
from core.repositories.base_repository import BaseRepository
```

**Service:**
```python
# core/services/new_service.py
from core.repositories.new_repository import new_repository
```

**API Router:**
```python
# api/routers/new.py
from fastapi import APIRouter
router = APIRouter()
```

### Config Management

Config wird aus `.env` geladen:
```python
from classes.Cconfig import Config
config = Config()
config.cities  # List of cities
config.platform_configs  # Platform configurations
config.api_base_url  # API URL
```

### Logging
```python
from modules.Mhandle_log import get_logger
log = get_logger(__name__)
log.info("Message")
```

## 🔍 Debugging

### Scraper Probleme
```bash
# Logs
tail -f logs/katzensuchapp.log
journalctl -u katzensuchapp-api -f

# Status check
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/scraper/status
```

### LLM Erreichbarkeit
```bash
curl http://home-ai:11434/api/tags
```

### DB Inspektion
```bash
sqlite3 gesehen.db
.tables
SELECT * FROM listings LIMIT 10;
```

## 📊 Datenfluss

1. **Scraping**: Orchestrator → Platform Scraper → SQLite `seen_urls`
2. **Classification**: `ClassificationService` → LLM via Ollama → `llm_classification` Cache
3. **Filtering**: `ListingService` mit Server-Side Filtern → API Response
4. **UI**: Flet UI via `api_client` → REST API → Service Layer → Repository → DB

## 🚧 Bekannte Limitationen

Aus `FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md`:

- **Umgebungsvariablen**: Teilweise inkonsistent zwischen `.env`, `.env.local`, `flet.toml`
- **Echtzeit-Updates**: Keine WebSockets, nur Polling/Pull
- **Scraper Frontend**: Keine Plattform/City Auswahl im Admin UI Trigger

## 📈 Roadmap

- [ ] Umgebungsvariablen konsolidieren
- [ ] WebSocket für Echtzeit-Updates
- [ ] Scraper Trigger mit Plattform/City Auswahl im UI
- [ ] Fortschrittsanzeige für Scraping Jobs
- [ ] Log Viewer im Admin UI
- [ ] Tests erweitern auf 80%+ Coverage
- [ ] Docker Compose Setup
- [ ] CI/CD Pipeline

## 🤝 Contributing

1. Branch erstellen: `git checkout -b feature/xxx`
2. Changes implementieren
3. Tests hinzufügen
4. `pytest tests/` ausführen
5. PR erstellen

## 📄 Lizenz

Private Projekt

## 📞 Support

- Logs: `logs/katzensuchapp.log`
- Dokumentation: `README.md`, `ROADMAP.md`, `FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md`
- API Docs: http://localhost:5000/docs

---

**Stand**: 2026-10-01  
**Version**: Post-Refactoring mit Service Layern
