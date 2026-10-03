# FEHLENDE_FUNKTIONEN_NACH_REFACTORING.md

## Übersicht
Dokumentation der noch fehlenden Funktionen nach dem Domain-Layer Refactoring.

**Stand: 2026-10-01**

---

## ✅ ABGESCHLOSSEN

### 1. Scraper Config CRUD
✅ **IMPLEMENTIERT**
- API-Endpunkte in `api/routers/admin.py` vorhanden
- Flet UI in `flet_app/ui/admin/admin_page.py` und `flet_app/ui/components/scraper_config_form.py` integriert
- CRUD-Operationen vollständig funktionsfähig

### 2. Feature Request Workflow
✅ **IMPLEMENTIERT**
- API-Endpunkte vorhanden
- UI-Integration in Admin-Oberfläche
- Tests bestanden

### 3. Server-Side Filtering
✅ **IMPLEMENTIERT**
- `api/routers/listings.py` mit Parametern: `age_min/age_max/einzelgaenger/freigang_noetig/min_confidence`
- `core/repositories/listing_repository.py find_all()` mit SQL-Filtern
- Client-seitiges Filtering entfernt

### 4. LLM-Integration
✅ **IMPLEMENTIERT**
- `modules/services/orchestrator.py _process_scraped_listings` mit `ClassificationService` und `llm_filter_service`
- Domain-Layer Services korrekt integriert

### 5. Mark-as-Processed
✅ **IMPLEMENTIERT**
- `POST /api/v1/listings/mark-processed` Endpunkt vorhanden

### 6. Direkte Scraper-Steuerung
✅ **IMPLEMENTIERT (2026-10-01)**
- API-Route `/api/v1/scraper/trigger` jetzt echt implementiert
- Nutzt `core.services.scraper_service.scraper_service.trigger_scraping()`
- Unterstützt Parameter: platform, city, max_pages, classify
- Optionale Background-Task Ausführung
- Scraper Status Endpoint `/api/v1/scraper/status` implementiert
- Admin-UI System-Tab erweitert mit:
  - Button "Scraper jetzt starten"
  - Button "Scraper Status anzeigen"
  - Status Dialog mit letzter Laufzeit, aktueller Stadt, aktiven Plattformen
- API-Client Methoden erweitert

---

## 🔴 HOHE PRIORITÄT

### 1. Umgebungsvariablen vereinheitlichen → Deployment-Risiko
⚠️ **TEILWEISE IMPLEMENTIERT**

**Problem:**
- `.env`, `.env.local`, `.env.example` existieren parallel
- `flet.toml` hardcodiert: `API_HOST=http://192.168.2.13`, `API_PORT=5000`
- `classes/Cconfig.py` lädt `.env.local` bevorzugt
- Inconsistent API-URLs zwischen Dateien

**Aktueller Stand:**
- Code lädt `.env.local` falls vorhanden, sonst `.env`
- `flet.toml` überschreibt nur Flet-App spezifische Werte

**Empfohlene Lösung:**
```python
# Single Source of Truth: .env Datei
# flet.toml sollte nur Flet-spezifische Settings enthalten
# Keine API_HOST/API_PORT in flet.toml
```
**TODO:** `flet.toml` bereinigen, API-Config nur über `.env` steuern

---

## 🟡 MITTLERE PRIORITÄT

### 1. Echtzeit-Updates → Bessere UX
❌ **NOCH NICHT IMPLEMENTIERT**

**Problem:** Dashboard zeigt veraltete Daten bis zum nächsten Pull

**Lösungsvorschlag:**
- WebSockets implementieren
- Polling alle 30s
- Server-Sent Events

---

## 📋 NÄCHSTE SCHRITTE

1. **HOCH:** Umgebungsvariablen konsolidieren
   - flet.toml bereinigen
   - Dokumentation aktualisieren

2. **MITTEL:** Echtzeit-Updates für Dashboard
   - WebSocket oder Polling implementieren

3. **NIEDRIG:** Scraper-Trigger erweitern
   - Plattform/City Auswahl im Admin-UI hinzufügen
   - Fortschrittsanzeige während Scraping
   - Logging/Log-Viewer für Scraper

---

## 📁 Betroffene Dateien

- `api/routers/scraper.py` - API-Routen für Scraper
- `api/routers/admin.py` - Admin CRUD Endpunkte
- `flet_app/ui/admin/admin_page.py` - Admin UI
- `flet_app/ui/components/scraper_config_form.py` - Config Form
- `flet_app/services/api_client.py` - API Client
- `core/services/scraper_service.py` - Scraper Service
- `modules/services/orchestrator.py` - Orchestrator
- `flet.toml`, `.env`, `.env.local`, `.env.example` - Config Dateien
- `classes/Cconfig.py` - Config Loader
