# FletBase Refactoring & Modularisierung

**Stand:** 2026-09-30  
**Ziel:** FletBase als plugin-basiertes, modulares Framework erweitern für maximale Wiederverwendbarkeit zwischen WebUI und API

## 1. Aktuelle FletBase-Architektur

### Bestehende Komponenten
- `BaseApp` mit Routing, Auth, Session-Timeout
- `Plugin-System` mit `BasePlugin`, `PluginManager`, `plugins.toml`
- `Auth-System` mit User/Group Management, JWT-ähnliche Sessions
- `Shell UI` mit Sidebar, TopBar
- `DB-Layer` für Auth-Datenbank

### Aktuelle Nutzung in KatzenSuchApp
KatzenSuchApp nutzt aktuell nur: Auth, Routing, Shell, DB – **Plugin-System wird nicht genutzt**

## 2. Modularisierung durch Plugin-System

### Zielarchitektur
```
flet_app/plugins/
├── plugin_scraper.py          # Scraper-Steuerung als Plugin
├── plugin_listings.py         # Listings-Ansicht als Plugin  
├── plugin_admin.py            # Admin-Bereich als Plugin
└── plugin_analytics.py        # Statistiken/Reports als Plugin
```

### Vorteile
- Jede Funktionalität ist eigenständig start/stopp-bar
- Plugins können unterschiedliche Permissions haben
- Plugins lassen sich versionsunabhängig entwickeln/testen
- Für API-Refactoring: Plugins können eigenständige API-Router bereitstellen

## 3. Konkrete Erweiterungen für FletBase

### 3.1 Plugin-System aktiv nutzen

**FletBase Erweiterung:**
- `plugin.py` um `get_api_routes()` Methode erweitern
- Plugin Manager registriert API-Router automatisch
- Plugin-Dependency Management

**Erweitertes Plugin-Metadaten-Schema:**
```python
metadata = {
    "name": "scraper",
    "version": "1.0.0",
    "dependencies": ["db", "auth"],
    "api_routes": ["/scraper", "/platforms"],
    "ui_routes": ["/scraper"],
    "permissions": ["scraper.admin"],
    "provides": ["scraper_service"]
}
```

### 3.2 Service-Provider Pattern

**Neue Datei:** `flet_base/core/services.py`
```python
class ServiceContainer:
    def register(self, name, factory)
    def get(self, name)
```

**Nutzen für KatzenSuchApp:**
- `DatabaseService`, `ScraperService`, `LLMService` als registrierte Services
- Flet UI und API können die gleichen Services nutzen
- Lazy Loading, Singleton Management
- Testbar durch Mock-Services

**Vorteil für Modularität:** Services sind vollständig von UI entkoppelt

### 3.3 Event-Bus System

**Neue Datei:** `flet_base/core/events.py`
```python
class EventBus:
    def subscribe(event_type, handler)
    def publish(event_type, data)
```

**Nutzen für KatzenSuchApp:**
- Scraper beendet → Event `scraping.completed` → Dashboard aktualisiert sich automatisch
- LLM Klassifikation fertig → Event `classification.done` → Notifications
- Plugin-Kommunikation ohne direkte Abhängigkeiten
- Entkoppelt UI von Background-Jobs

### 3.4 Konfigurations-Module

**Erweiterung:** Pro Plugin/Modul Konfiguration
```toml
[plugins.scraper]
enabled = true
cities = ["Berlin", "Hamburg"]
interval_minutes = 15

[plugins.listings]
enabled = true
default_filters = {age_min = 2}
```

**Vorteil:** Unterschiedliche Deployments mit unterschiedlichen Features

### 3.5 UI-Components Registry

**Erweiterung:** Wiederverwendbare UI-Komponenten als Registry
```python
# Plugin kann UI-Components bereitstellen
def register_components(self, registry):
    registry.register("listing_card", ListingCard)
    registry.register("filter_panel", FilterPanel)
```

**Vorteil:** Components werden zu UI-Building-Blocks, Plugins können eigene Components beisteuern

### 3.6 Multi-Page Controller Pattern

**Idee:** FletBase um Page-Controller erweitern

```python
class ListingsController:
    def __init__(self, db_service, llm_service):
        self.db = db_service
        self.llm = llm_service
    
    def get_filtered_listings(self, filters): ...
    def mark_processed(self, id): ...

class DashboardPage(ft.UserControl):
    def __init__(self, controller):
        self.controller = controller  # Injektion
```

**Vorteil:** Testbar, wiederverwendbar für API und UI

### 3.7 Background Job Plugin

**Idee:** Plugin für Background-Job-Management

FletBase könnte ein Core-Plugin für Jobs bereitstellen:
- Job-Queue Management
- Cron-Scheduler
- Job-State in DB persistieren
- UI für Job-Monitoring

**Nutzen für KatzenSuchApp:**
- Scraper als Background-Job statt Orchestrator
- LLM Klassifikation als Job-Queue
- Gemeinsame Job-UI für alle Plugins

### 3.8 Theming und Layout Plugins

**Idee:** UI-Theming als Plugin-System
```python
class ThemePlugin(BasePlugin):
    def get_themes(self):
        return [{"name": "dark", "mode": "dark"}]
    
    def get_layouts(self):
        return [{"name": "compact", "sidebar_width": 200}]
```

**Vorteil:** Verschiedene UI-Varianten ohne Code-Duplikation

## 4. FletBase + API Abstraktion für APK

### Frage: Sollte FletBase für API-Abfragen der APK erweitert werden?

**Antwort: Nein, nicht direkt in FletBase.**

**Begründung:**
- FletBase ist UI-Library, keine API-Library
- APK hat eigene Networking-Stack (Retrofit/OkHttp in Kotlin, etc.)
- API-Logik gehört in `modules/api/`, nicht in UI-Layer

**Stattdessen: FletBase als Plugin-basiertes Framework erweitern**

### Architektur
```
libs/flet_base/          # UI Framework
modules/api/             # API Layer (FastAPI)
modules/services/        # Business Logic (gemeinsam)
flet_app/plugins/        # UI Plugins
```

FletBase wird um Plugin-API-Unterstützung erweitert:
- Plugins können optional `get_api_routes()` implementieren
- Plugin Manager hält Referenz auf FastAPI App
- Beim Laden wird `plugin.get_api_routes(app)` aufgerufen
- Plugins können sowohl Flet-Controls als auch FastAPI-Router definieren

**Vorteil:** Plugins werden dual-use:
- Desktop-WebUI nutzt Flet-Plugin
- Mobile APK nutzt gleiche Plugin-Logik über API
- Kein Code-Duplikation
- Feature-Flag gesteuert

**Konkrete Umsetzung:**
1. FletBase Plugin-Interface um `get_api_routes()` erweitern
2. Plugin Manager registriert Routes bei FastAPI
3. Services sind über Service Container geteilt
4. Event-Bus für lose Kopplung

Das ist **sauberer** als FletBase zum "API-Client" zu machen. FletBase bleibt UI, die Plugins werden dual-use.

## 5. Empfohlene Architektur nach Refactoring

```
libs/flet_base/
├── core/
│   ├── app.py              # BaseApp
│   ├── plugin.py           # Plugin Interface + API Support
│   ├── services.py         # Service Container (NEU)
│   └── events.py           # Event Bus (NEU)
└── plugins/...

modules/
├── api/                    # FastAPI App
│   ├── main.py
│   └── routers/...
├── services/               # Gemeinsame Business Logic
│   ├── db_service.py
│   ├── scraper_service.py
│   └── llm_service.py
└── core/                   # Models, Filters

flet_app/
├── plugins/                # Flet-Plugins
│   ├── plugin_listings.py  # UI + API Routes
│   └── plugin_scraper.py
└── main.py                 # Flet App Bootstrapping

mobile_app/                 # Android APK
└── api_client/             # Retrofit Client für /api/v1
```

## 6. Priorisierte Empfehlungen

**Kurzfristig umsetzbar & hoher Nutzen:**
1. **Service-Provider Pattern** – Entkoppelt Business-Logik von UI, Vorbereitung für API
2. **Event-Bus** – Löst Scraper → UI Kommunikation, reduziert Kopplung
3. **Plugin-Metadaten erweitern** – Für spätere API-Integration

**Mittelfristig:**
4. **Background Job Plugin** – Ersetzt Orchestrator durch modulares Job-System
5. **UI-Components Registry** – Für Wiederverwendbarkeit

**Für maximale Modularität:**
Plugin-System ist bereits vorhanden, aber **nicht genutzt**. Größter Hebel wäre, bestehende Features von KatzenSuchApp **in Plugins zu überführen** statt sie direkt in `flet_app/` zu halten.

## 7. Fazit

FletBase sollte **nicht** direkt für APK-API-Abfragen erweitert werden. FletBase ist UI-Library.

**Stattdessen:**
- FletBase als plugin-basiertes Framework erweitern
- Plugins können optional API-Router bereitstellen
- Service-Container für gemeinsame Business-Logik
- Event-Bus für lose Kopplung

**Ergebnis:** Maximale Modularität, keine Flet-Abhängigkeit für mobile App, Plugin-System als gemeinsame Brücke zwischen WebUI und API.

Die Investition lohnt sich langfristig für Erweiterbarkeit, Wartbarkeit und Multi-Platform Support.
