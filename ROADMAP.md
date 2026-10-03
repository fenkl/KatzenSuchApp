# KatzenSuchApp Roadmap

Diese Roadmap beschreibt alle benötigten Schritte zur kompletten Neuerstellung der KatzensuchApp auf Basis des Submoduls `libs/flet_base`.

## Übersicht Checkliste

- [x] 1. Projektprüfung & Setup – Struktur prüfen, Submodul prüfen
- [x] 2. Datenbank & DB Utils – Schema + `modules/db_utils.py`
- [x] 3. Playwright Browser & Logging – `playwright_browser.py`, `Mhandle_log.py`, `Cconfig.py`
- [x] 4. Scraper Basis – `modules/scraper/` Basis + Handler TierheimHelden, Shelta, LeipzigerLand
- [x] 5. FletBase Integration – `flet_app/main.py` mit korrektem Import, Pages registriert
- [x] 6. UI Platzhalter – `DashboardPage`, `AdminPage` Grundgerüst
- [x] 7. Services Layer – Orchestrator mit Loop und Stadt-Rotation
- [x] 8. LLM Filter Service – Tailscale Client, Cache, Pre-Filter
- [x] 9. Flet UI vollständig – Dashboard & Admin Erweiterung, Components
- [x] 10. Config & Environment – `.env`, `pyproject.toml`
- [x] 11. Tests – Core Logik Tests

## Projektstruktur Ziel

```
KatzenSuchApp/
├── libs/
│   └── flet_base/          # bereits als Submodul hinzugefügt
├── flet_app/
│   ├── main.py
│   ├── ui/
│   │   ├── dashboard.py
│   │   ├── admin/
│   │   └── components/
│   ├── services/
│   │   ├── api_client.py
│   │   ├── db_bridge.py
│   │   └── llm_filter_service.py
│   └── config.py
├── modules/
│   ├── services/
│   │   ├── orchestrator.py
│   │   ├── scraper_service.py
│   │   ├── config_service.py
│   │   ├── cleanup_service.py
│   │   ├── exception_service.py
│   │   └── db_service.py
│   ├── scraper/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── tierheimhelden.py
│   │   ├── shelta.py
│   │   └── leipziger_land.py
│   ├── db_utils.py
│   ├── playwright_browser.py
│   └── Mhandle_log.py
├── classes/
│   └── Cconfig.py
├── tests/
├── .env
└── pyproject.toml
```

## 1. Projektprüfung & Setup ✅

### 1.1 Projektstruktur prüfen ✅
- Existierende Ordner `example_scraper`, `example_services` analysiert
- Submodul `libs/flet_base` geprüft, Anleitung gelesen

### 1.2 FletBase Integration vorbereiten ✅
- Pfad `libs/flet_base` in `sys.path` ✅
- `flet_base.core.config.configure` mit DB-Pfad, Session-Timeout, Theme ✅
- DB Initialisierung: `from flet_base.core.db import init_db, seed_defaults` ✅
- `BaseApp` mit Pages registriert ✅
- Keine eigene Auth implementiert ✅

## 2. Datenbank & DB Utils ✅

**Ziel:** SQLite `gesehen.db` mit CRUD ✅

**Tabellen:**
- `platforms(id, name, base_url, enabled)`
- `seen_urls(id, url, platform, first_seen, last_seen, processed, UNIQUE(url, platform))`
- `configs(key, value)`
- `scraper_configs(id, platform_name, base_url, listing_selector, detail_selector, pagination_param, city_param, enabled, handler_class, login_required)`
- `feature_requests(id, platform_name, start_url, example_listing_url, description, created_by, created_at, status)`
- `llm_classification(id, url_hash UNIQUE, url, platform, alter_ok, alter_jahre, alter_unsicher, einzelgaenger, einzelgaenger_unsicher, freigang_noetig, freigang_unsicher, kein_freigang_gewuenscht, confidence, reason, classified_at)`
- `ratings(id, url, platform, rating, comment, rated_by, rated_at)`

**Funktionen in `modules/db_utils.py` ✅**
- `init_db()` ✅
- `is_known(url, platform) -> bool` ✅
- `save_url(url, platform)` ✅
- `get_scraper_configs()` ✅
- `add_scraper_config(...)` ✅
- `get_platforms()` ✅
- `add_feature_request(...)` ✅
- `get_feature_requests(status=None)` ✅
- `cache_llm_classification(url, platform, result)` ✅
- `get_llm_classification(url) -> Optional[Dict]` ✅

## 3. Playwright Browser & Logging ✅

**`modules/playwright_browser.py` ✅**
- `PlaywrightManager` Klasse ✅
- Firefox starten mit fester User-Agent ✅
- Context/Page Management ✅
- Retry Mechanik ✅
- Sauberes Close ✅

**`modules/Mhandle_log.py` ✅**
- Logging Handler mit Rotation ✅
- Levels: DEBUG, INFO, WARNING, ERROR ✅

**`classes/Cconfig.py` ✅**
- Konfigurationsklasse für globale Einstellungen ✅
- Lade aus `.env` ✅

## 4. Scraper Basis ✅

**`modules/scraper/config.py` ✅**
- Städte Liste für Rotation ✅
- Pagination Parameter Maps ✅
- Selector Configs pro Plattform ✅

**`modules/scraper/base.py` ✅**
- `BaseScraper` ABC ✅
- `__init__(platform_name, config)` ✅
- `build_url(city, page, base_config)` ✅
- `should_filter_listing(listing_data) -> bool` ✅
- `scrape(city, max_pages)` ✅
- `extract_listings(page)` ✅
- `extract_detail(url)` ✅
- Deduplizierung via `db_utils.is_known` ✅
- PlaywrightManager Integration ✅

**Handler ✅**
- `modules/scraper/tierheimhelden.py` ✅
- `modules/scraper/shelta.py` ✅
- `modules/scraper/leipziger_land.py` ✅
Ableitung von `BaseScraper` mit plattformspezifischen Selektoren, Pagination Pattern und Login falls nötig ✅

## 5. Services Layer ✅

**`modules/services/config_service.py` ✅**
- Argument Parsing ✅
- Config Laden aus `.env` und DB ✅
- Umgebungsvariablen Validierung ✅

**`modules/services/db_service.py` ✅**
- Wrapper um `db_utils` ✅
- Transaktionsmanagement ✅

**`modules/services/scraper_service.py` ✅**
- Handler laden aus `scraper_configs` ✅
- Stadt-Rotation Logik ✅
- Nachtmodus / Rate Limiting ❌ Noch nicht
- Async Loop ✅

**`modules/services/cleanup_service.py` ✅**
- atexit Handler ✅
- PID Cleanup ✅
- Temp Files entfernen ✅

**`modules/services/exception_service.py` ✅**
- Global Exception Hooks ✅
- Logging ✅

**`modules/services/orchestrator.py` ✅**
- `ApplicationOrchestrator` Klasse ✅
- Services initialisieren ✅
- Main Loop starten ✅
- Scraper Service + LLM Filter + DB koordinieren ✅

## 6. LLM Filter Service ✅

**`flet_app/services/llm_filter_service.py`** ✅
- HTTP Client zu `http://home-ai:11434/api/chat` ✅
- Modell: Phi-4-mini 3.8B oder ähnlich ✅
- JSON Schema Prompting ✅
- Request Format:
```json
{
  "messages": [{"role": "user", "content": prompt}],
  "model": "phi-4-mini",
  "format": {"type": "json_schema", "schema": {...}}
}
```
- Response Parsing
- Cache Check via `db_utils.get_llm_classification`
- Cache Write via `db_utils.cache_llm_classification`
- Deterministischer Pre-Filter:
  - Alter 2-8 Jahre via Regex/Parse
  - Einzelgänger Keyword
  - Freigang nötig Detection

**Filter Logik:** ✅
1. Pre-Filter deterministisch ✅
2. Falls unsicher → LLM Call ✅
3. Ergebnis speichern ✅
4. Nur pass matches durchlassen ✅

## 7. Flet App UI

**`flet_app/config.py`**
- UI Config, API Endpoints
- Tailscale URL

**`flet_app/services/api_client.py`**
- REST Client für lokale Services
- Scraper Trigger, Status Abfrage

**`flet_app/services/db_bridge.py`**
- Verbindung zu `gesehen.db`
- Query Wrapper für UI

**`flet_app/ui/dashboard.py`** ✅
- `DashboardPage` Klasse ✅ Basis vorhanden
- Filter UI (Alter, Einzelgänger, Freigang) ✅
- Listings Grid mit Karten ✅
- Aktionen: Markieren als verarbeitet, Rating, Feature Dialog, manueller Scraper-Trigger ✅
- Nutzt FletBase Shell ✅

**`flet_app/ui/admin/admin_page.py`** ✅
- `AdminPage` Klasse ✅ Basis vorhanden
- Tabs: Plattformen & Scraper, Feature Requests, Ratings, System ✅
- Scraper Config CRUD mit Test Button ✅
- Feature Requests Verwaltung ✅
- User Management via FletBase ✅

**`flet_app/ui/components/`** ✅
- `listing_card.py` ✅
- `filter_panel.py` ✅
- `scraper_config_form.py` ✅
- `feature_request_dialog.py` ✅

## 8. Config & Environment ✅

**.env Beispiel** ✅
```
DB_PATH=./gesehen.db
AUTH_DB_PATH=./flet_app/data/auth.db
OLLAMA_URL=http://home-ai:11434/api/chat
OLLAMA_MODEL=phi-4-mini
OLLAMA_TIMEOUT=30
CITIES=Berlin,Hamburg,München,Köln,Frankfurt
SCRAPER_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
```

**`pyproject.toml`** ✅
- Dependencies: flet, playwright, requests, python-dotenv, bcrypt
- Scripts: `katzensuchapp-run`, `katzensuchapp-scraper`

## 9. Tests ✅

**`tests/`** ✅
- `test_db_utils.py` – DB Init, is_known, Cache ✅
- `test_scraper_base.py` – Base Scraper Logic, URL Building ✅
- `test_llm_filter_service.py` – Mock Ollama Client, Cache Hit/Miss ✅
- `test_orchestrator.py` – Service Wiring ✅
- `test_config_service.py` – .env Laden ✅

## 10. Integrations & Constraints

- **Keine eigene Auth** – FletBase übernimmt Login, Sidebar, TopBar, Admin User/Group Management
- **Keine Flask** – Reine Flet App
- **Priorität Android und Linux**
- **Linode wenig Power** – Kein LLM dort, nur Scraper
- **Tailscale nur für Linode → Home AI**
- **Keine Bearbeitung vorhandener example Dateien** – Nur als Richtlinie

## Ausführung Reihenfolge

1. ROADMAP.md erstellt ✅
2. `flet_app/main.py` mit korrekter FletBase Integration ✅
3. `modules/db_utils.py` + DB Init ✅
4. `modules/playwright_browser.py` + `Mhandle_log.py` + `classes/Cconfig.py` ✅
5. `modules/scraper/` Basis + Handler ✅
6. `modules/services/` Layer + Orchestrator ✅
7. `flet_app/services/llm_filter_service.py` ✅
8. Flet UI Pages + Components ✅ vollständig
9. Config/.env/pyproject.toml ✅
10. Tests ✅
