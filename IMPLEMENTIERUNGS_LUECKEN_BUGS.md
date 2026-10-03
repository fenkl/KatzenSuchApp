# KatzenSuchApp - Implementierungslücken und Potenzielle Bugs

**Hinweis:** Dieses Dokument ist konsolidiert in `FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md`.  
Verweise bitte auf dieses Dokument für den aktuellen Stand.


**Erstellt:** 2026-09-30
**Letztes Update:** 2026-10-02 12:34 +02:00
**Status:** Aktualisiert und konsolidiert - siehe FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md
**Working Directory:** /home/cesco/PycharmProjects/KatzenSuchApp

## Überblick

## Aktueller Status (Stand 2026-10-02)

### Erledigte Items
- ✅ Dashboard lädt echte Daten aus DB
- ✅ Integration Tests: Happy Path Test für Scraping → LLM → DB erstellt
- ✅ Scraper persistiert Detail-Daten in scraped_listings
- ✅ Playwright Context Cleanup implementiert
- ✅ LLM-Integration im Scraping-Fluss implementiert
- ✅ URL Hash Konsistenz Problem
- ✅ Admin UI Scraper Config funktional
- ✅ Playwright Manager Singleton

### Teilweise erledigt

### Offene Items

---

Nach Analyse des aktuellen Codebases wurden mehrere fehlende Implementierungen, unvollständige Features und potenzielle Bugs identifiziert. Diese Dokumentation listet sie detailliert auf und bewertet die Auswirkungen.

---

## 1. Kritische Implementierungslücken

### 1.1 Dashboard Datenquelle fehlt vollständig

**Schweregrad:** Hoch
**Standort:** `flet_app/ui/dashboard.py` L.106-128

**Problem:**
```python
def _load_listings(self):
    """Load listings from database - placeholder implementation"""
    # In real implementation, this would query seen_urls and llm_classification
    # For now, use mock data
    self.listings = [
        {"url": f"https://example.com/cat/{i}", ...}
        for i in range(25)
    ]
```

**Auswirkung:** Dashboard zeigt ausschließlich Mock-Daten. Echte Scraping-Ergebnisse werden nicht angezeigt.

**Fehlende Funktion:**
- Kein Query der `seen_urls` Tabelle
- Kein Join mit `llm_classification`
- Keine Filterung auf `processed = 0`
- Keine Mapping von Plattform/Namen auf echte Daten

**Empfohlene Umsetzung:**
```python
def _load_listings(self):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.url, s.platform, lc.* 
        FROM seen_urls s
        LEFT JOIN llm_classification lc ON s.url_hash = sha256(s.url)
        WHERE s.processed = 0
    """)
    ...
```

**Status:** Aktualisiert und konsolidiert - siehe FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md

### 1.2 Scraper Ergebnisse werden nicht persistiert

**Schweregrad:** Hoch
**Standort:** `modules/scraper/base.py` L.95-108

**Problem:**
Detail-Daten werden extrahiert, URL gespeichert, aber **die extrahierten Daten (title, description, age) werden nicht in DB gespeichert**.

```python
detail = await self.extract_detail(detail_page)
detail["url"] = url
detail["platform"] = self.platform_name
detail["city"] = city
self.save_url(url)  # Nur URL, keine Daten!
results.append(detail)
```

**Auswirkung:** Scraping läuft, aber Ergebnisse sind verloren nach dem Run. Dashboard kann nichts anzeigen.

**Fehlende Tabelle:** Keine Tabelle für Roh-Scraping-Ergebnisse. Benötigt `scraped_listings` oder Erweiterung von `seen_urls`.

**Status:** Aktualisiert und konsolidiert - siehe FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md

### 1.3 `processed` Flag wird nie gesetzt

**Schweregrad:** Mittel
**Standort:** `modules/db_utils.py` L.52, `flet_app/ui/dashboard.py` L.160

**Problem:**
- Spalte `processed` existiert in `seen_urls`
- Dashboard UI hat `_mark_processed(url)` aber nutzt `save_url()` statt Update
- `save_url()` macht `INSERT OR IGNORE`, ändert `processed` nicht

**Auswirkung:** URLs werden nie als verarbeitet markiert, Dauerschleife.

**Fehlende Funktion:** `update_url_processed(url, platform, processed=True)`
**Status Check 2026-09-30:** ✅ TEILWEISE ERLEDIGT - mark_processed() existiert und wird von Dashboard genutzt, setzt processed Flag in seen_urls. Automatisches Setzen fehlt jedoch.
### 1.4 LLM Filter Service wird nie im Scraping-Fluss verwendet

**Schweregrad:** Hoch
**Standort:** Orchestrator → Scraper → LLM

**Problem:**
- `ApplicationOrchestrator.run_once()` ruft `scrape_platform_city()` auf
- Scraper gibt Roh-Daten zurück
- **Kein LLM-Call nach dem Scraping**
- LLM-Service existiert, wird aber nicht integriert

**Auswirkung:** Pre-Filter läuft lokal, aber LLM-Klassifikation findet nie statt.

**Fehlende Integration:**
```python
# In orchestrator.py nach scraping
from flet_app.services.llm_filter_service import llm_filter_service
for listing in results:
    classification = await llm_filter_service.classify_listing(...)
    cache_llm_classification(...)
```
**Status Check 2026-09-30:** ✅ ERLEDIGT - Orchestrator.run_once() integriert LLM-Service jetzt

**Umsetzung:**
- LLM Filter Service wird in `ApplicationOrchestrator.__init__` initialisiert (mit graceful fallback)
- In `run_once()` wird nach dem Scraping automatisch `classify_listing()` für alle neuen Listings aufgerufen
- Klassifikationsergebnisse werden über Service in `llm_classification` Tabelle gecached
- Listings erhalten `_llm_classification` Metadata für Weiterverarbeitung
- Integration erfolgt asynchron in Haupt-Scraping-Fluss
### 1.5 Admin-Seite Scraper Config UI ist nicht funktional

**Status Check 2026-09-30:** ✅ ERLEDIGT - _load_scraper_configs() implementiert, _get_scraper_configs() liefert vollständige Spalten, UI zeigt alle Felder an

**Schweregrad:** Mittel
**Standort:** `flet_app/ui/admin/admin_page.py` L.89-98

**Problem:**
```python
configs = get_scraper_configs()
return [
    {
        "id": c[0],
        "platform_name": c[1],
        "base_url": c[2] or "",
        "enabled": "Ja" if c[7] else "Nein",  # c[7] ist enabled
        "handler_class": c[8] or ""
    }
    for c in configs
]
```

**Problem:** `get_scraper_configs()` gibt 11 Spalten zurück (inkl. leere created_at/updated_at), Index-Offset falsch. Handler ist c[8], aber in Query ist Position 8 richtig? Siehe db_utils L.85.

**Zusätzlich:** `_load_scraper_configs()` ist leer (`pass`)

### 1.6 Playwright Page/ Kontext Cleanup fehlt

**Schweregrad:** Hoch (Resource Leak)
**Standort:** `modules/scraper/base.py` L.95-120

**Problem:**
```python
detail_page, detail_context = await self.pm.new_context_page()
try:
    await detail_page.goto(...)
    ...
except:
    ...
finally:
    await self.pm.close_page(detail_page)  # Kontext wird nicht geschlossen!
```

**Auswirkung:** Browser-Kontexte bleiben offen, Speicherleck, irgendwann Crash.

**Fehlend:** `await context.close()` im finally-Block

**Status:** Aktualisiert und konsolidiert - siehe FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md

---

## 2. Potenzielle Bugs

### 2.1 URL Hash Inkonsistenz

**Schweregrad:** Hoch
**Standort:** `modules/db_utils.py` L.175, `modules/db_utils.py` L.195

**Problem:**
```python
# cache_llm_classification
url_hash = hashlib.sha256(url.encode()).hexdigest()
cur.execute("INSERT ... INTO llm_classification (url_hash, ...)")

# get_llm_classification
url_hash = hashlib.sha256(url.encode()).hexdigest()
cur.execute("SELECT * FROM llm_classification WHERE url_hash = ?", (url_hash,))
```

**ABER:** In `dashboard.py` `_load_listings` würde vermutlich Join machen mit `sha256(s.url)` – **SQLite hat keine native sha256 Funktion in default build!**

**Auswirkung:** Hash-Matching funktioniert nur wenn Python-Seite macht den Hash, aber SQL-Join unmöglich.

**Lösung:** Hash in `seen_urls` speichern bei Insert, oder Python-Seite für jeden URL separat query.

### 2.2 Playwright Manager Singleton Problem

**Schweregrad:** Mittel
**Standort:** `modules/scraper/base.py` L.33

```python
self.pm = PlaywrightManager()
```

**Problem:** Jeder Scraper-Instanz hat eigenen Manager → jeder startet eigenen Browser. Bei 3 Plattformen = 3 Browser-Instanzen.

**Auswirkung:** Hoher Speicherverbrauch, Konflikte.

**Empfehlung:** Manager als Singleton, oder Dependency Injection.

**Status:** Aktualisiert und konsolidiert - siehe FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md

### 2.3 `_build_url` Pagination Bug

**Schweregrad:** Mittel
**Standort:** `modules/scraper/base.py` L.37-56

**Problem:**
```python
if pagination_param:
    query_params[pagination_param] = [str(page)]
```

**Problem:** Wenn `base_url` bereits Query-Parameter hat, wird `page` überschrieben. Wenn `page` schon vorhanden, wird es dupliziert.

**Zusätzlich:** `city_param` kann `None` sein (Shelta, LeipzigerLand) → `query_params[None]` würde KeyError erzeugen? Nein, Prüfung existiert aber...

### 2.4 Pre-Filter Logik inkonsistent

**Schweregrad:** Niedrig
**Standort:** `modules/scraper/base.py` L.150-180, `flet_app/services/llm_filter_service.py` L.210-225

**Problem:**
- BaseScraper.pre_filter nutzt Regex für Alter
- LLMFilterService._pre_filter_pass nutzt gleiche Regex
- Doppelter Code, unterschiedliche Defaults

**Zusätzlich:** `pre_filter` in BaseScraper wird **nie aufgerufen**! Scraper führt ihn nicht aus.

### 2.5 Config Reload Problem

**Schweregrad:** Niedrig
**Standort:** `classes/Cconfig.py` L.13-25

**Problem:** `Config()` wird bei jedem Import neu instanziiert. `Config` Objekt hat keinen Cache. `db_utils._get_db_path()` erstellt bei jedem Call neue Config-Instanz.

**Auswirkung:** Performance, aber auch: wenn `.env` sich ändert während Laufzeit, wird es nicht neu geladen.

### 2.6 Exception Service Setup Race Condition

**Schweregrad:** Niedrig
**Standort:** `modules/services/exception_service.py` L.17-22

```python
loop = asyncio.get_event_loop()
loop.set_exception_handler(...)
```

**Problem:** `get_event_loop()` kann in neuer Python Version deprecated sein, und wenn kein Loop existiert, Fehler.

### 2.7 Scraper Service vs Orchestrator Doppelung

**Schweregrad:** Mittel
**Standort:** `modules/services/scraper_service.py`, `modules/services/orchestrator.py`

**Problem:** Beide haben ähnliche Logik für City-Rotation. ScraperService delegiert an Orchestrator, aber Orchestrator hat eigenen City-Index.

**Auswirkung:** Inkonsistenter Zustand wenn beide genutzt werden.

### 2.8 `get_scraper_configs` Return Format Bug

**Schweregrad:** Mittel
**Standort:** `modules/db_utils.py` L.84-95

```python
cur.execute("""
    SELECT id, platform_name, base_url, listing_selector, detail_selector,
           pagination_param, city_param, enabled, handler_class, login_required,
           '' as created_at, '' as updated_at
    FROM scraper_configs
""")
```

**Problem:** `created_at`/`updated_at` Spalten existieren in Tabelle nicht! `scraper_configs` hat keine Timestamps laut `init_db()` L.31-42.

**Auswirkung:** SQL Error bei Query?

**Test:** Spaltenliste stimmt nicht mit Tabelle überein.

### 2.9 Auth DB Pfad Inkonsistenz

**Schweregrad:** Mittel
**Standort:** `classes/Cconfig.py` L.16, `flet_app/main.py` L.22

**Problem:** Config default für `auth_db_path` ist `flet_app/data/auth.db` relativ. Wenn `ft.run()` aus Projektroot gestartet wird, ok. Wenn aus `flet_app` gestartet, Pfad falsch.

**Zusätzlich:** `flet_base.core.config.configure(db_path=config.auth_db_path, ...)` – aber FletBase erwartet absoluten Pfad? Unklar.

### 2.10 ListingCard Komponente existiert, wird aber nicht mit Daten gefüllt

**Schweregrad:** Niedrig
**Standort:** `flet_app/ui/components/listing_card.py`

**Problem:** Komponente existiert, aber Dashboard baut Cards manuell ohne Component-Init? Code zeigt `ListingCard(listing=listing, ...)`

**Aber:** Komponenten-Definition prüfen:
```python
# Angenommen ListingCard erwartet bestimmte Struktur
```

**Unklar:** Ob `ListingCard` `llm_classification` korrekt anzeigt.

---

## 3. Unvollständige Features

### 3.1 Ratings System

**Standort:** `modules/db_utils.py` L.76-85, DB Tabelle `ratings`

**Problem:** Tabelle existiert, keine UI, keine API, keine Integration.

**Fehlend:**
- Rating Eingabe UI
- Rating Anzeige
- Aggregation

### 3.2 Feature Request Status Workflow

**Standort:** `modules/db_utils.py` Tabelle `feature_requests`

**Problem:** `status` Feld existiert, aber kein Workflow zur Aktualisierung.

**Fehlend:**
- Admin UI zum Status ändern
- Benachrichtigung
- Integration mit Scraper Config Erzeugung

### 3.3 Cleanup Service nicht aktiv

**Standort:** `modules/services/cleanup_service.py`

**Problem:** Service instanziiert sich beim Import (`cleanup_service = CleanupService()`), registriert atexit-Handler. Aber wird nie explizit aufgerufen.

**Fehlend:**
- Regelmäßige Cleanup-Aufgaben (alte Logs, veraltete URLs)
- Konfigurierbare Schedules

### 3.4 Scraper Konfiguration via DB nicht vollständig

**Standort:** `modules/db_utils.py` L.98-113

**Problem:** `add_scraper_config` nutzt `INSERT OR REPLACE`, aber keine `updated_at` Spalte. Keine Versionshistorie.

**Fehlend:**
- Migrations-System
- Config Validation
- Test-Scrape für neue Config

### 3.5 Logging Rotation nicht getestet

**Standort:** `modules/Mhandle_log.py` L.19-25

**Problem:** `RotatingFileHandler` mit 10MB/5 Backups konfiguriert, aber:
- Logger wird pro Modul neu geholt via `get_logger(name)`
- Handler wird nur beim ersten Import hinzugefügt (`if not logger.handlers`)
- **ABER:** `logging.getLogger(name)` gibt child-logger – parent handler wird geerbt? Ja, aber...

**Potenziel:** Mehrfache Handler falls `Mhandle_log` mehrfach importiert?

---

## 4. Sicherheits- / Stabilitätsprobleme

### 4.1 Playwright Browser Installation während Runtime

**Schweregrad:** Hoch
**Standort:** `modules/playwright_browser.py` L.28-35

**Problem:** Wenn Firefox fehlt, wird Installation via `subprocess`/`asyncio.create_subprocess_exec` versucht **während Scraping**.

**Auswirkung:** Blocking, Permission-Probleme, unklar ob in Container funktioniert.

**Besser:** Installations-Check beim Start, nicht während Laufzeit.

### 4.2 Keine Rate Limiting

**Schweregrad:** Mittel
**Standort:** `modules/scraper/base.py` L.75-120

**Problem:** Scraping ohne Delays zwischen Requests. `wait_for_timeout(2000)` ist fix, aber kein respect für robots.txt, kein exponential backoff.

**Auswirkung:** IP Bans, Blockierung.

### 4.3 SQL Injection Risiko

**Schweregrad:** Niedrig
**Standort:** `modules/db_utils.py` generell

**Problem:** Alle Queries nutzen Parameter Binding – gut. Aber `add_scraper_config` nutzt `INSERT OR REPLACE` mit Platform-Namen – wenn Name Sonderzeichen enthält, ok.

**Aber:** `get_scraper_configs` baut Liste manuell, keine Gefahr.

### 4.4 Ollama URL ohne Health Check

**Schweregrad:** Mittel
**Standort:** `flet_app/services/llm_filter_service.py` L.95-110

**Problem:** `_query_ollama` macht POST, aber kein Timeout-Handling für DNS, kein Retry.

**Auswirkung:** Scraper blockiert wenn Ollama down.

---

## 5. Architektur-Probleme

### 5.1 Zirkuläre Abhängigkeiten

**Standort:** Mehrere Module

- `modules/db_utils.py` importiert `Config`
- `classes/Cconfig.py` ist clean
- `modules/services/*` importieren `db_utils` und `Config`

**Besser:** Dependency Injection, Config als Singleton.

### 5.2 Kein Testing

**Standort:** `tests/` leer

**Problem:** Keine Unit Tests, keine Integration Tests. ROADMAP.md listet Tests als pending.

**Auswirkung:** Bug-Risiko hoch.

### 5.3 Dokumentation fehlt

**Standort:** Code allgemein

**Problem:** Docstrings existieren, aber:
- Keine API-Dokumentation
- Keine Sequenzdiagramme
- `.env.example` fehlt
- README existiert (422 Zeilen), aber spezifische Setup-Anleitungen für Dev/Prod getrennt?

---

## 6. Zusammenfassung Prioritäten

### Sofort kritisch (P0)
1. Dashboard zeigt keine echten Daten
2. Scraping Ergebnisse werden nicht persistiert
3. LLM Service nicht in Scraping-Fluss integriert
4. Playwright Context Leak

### Hoch (P1)
5. `processed` Flag nicht gesetzt
6. URL Hash Inkonsistenz SQLite
7. Playwright Manager Singleton ✓

### Mittel (P2)
9. Rate Limiting fehlt
10. Keine Tests
11. Config Reload
12. Ratings System unvollständig

### Niedrig (P3)
13. Logging Duplikate potenziel
14. Pre-Filter Duplikation
15. Dokumentation ergänzen

---

## 7. Empfohlene nächste Schritte

1. **Playwright Manager Singleton:** Als Singleton implementieren um Ressourcenverschwendung zu vermeiden ✓ ERLEDIGT 2026-09-30 18:47 +02:00
2. **Integration Tests:** Happy Path Test für Scraping → LLM → DB erstellen ✓ ERLEDIGT 2026-09-30 19:17 +02:00
3. **Rate Limiting:** Implementierung für API Calls und Scraping
4. **Config Reload:** Hot-Reload für Scraper Configs ohne Restart
5. **Ratings System:** Vollständige Implementierung und Persistierung
6. **Dokumentation:** `.env.example` und Setup Guide ergänzen
---
*Diese Analyse basiert auf Code-Stand von 2026-09-30. Dokument aktualisiert am 2026-09-30 19:17 +02:00.*
