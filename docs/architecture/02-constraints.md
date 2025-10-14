# 2. Randbedingungen (MVP)

## 2.1 MVP Technische Randbedingungen

### Verpflichtende MVP Technologien

| Randbedingung | Erläuterung | MVP Begründung |
|---------------|-------------|----------------|
| **Python Backend** | SimPy Framework erfordert Python 3.11+ | Discrete Event Simulation Standard |
| **SimPy Framework** | Deterministische Ereignissgesteuerte Simulation | Bewährtes Framework für MVP |
| **Matplotlib** | Graphische Ausgabe von KPIs und Metriken | Einfache Visualisierung ohne Web-Frontend |
| **CSV/JSON Files** | Dateibasierte Datenhaltung | Keine Datenbank-Installation erforderlich |

### MVP Ausgeschlossene Technologien

| Technologie | Grund für Ausschluss | Vollversion |
|-------------|---------------------|-------------|
| **Web-Frontend** | Zu komplex für MVP | ✅ Vue.js geplant |
| **Event Bus** | Direkte Aufrufe einfacher | ✅ Event-driven geplant |
| **WebSocket** | Kein Real-time erforderlich | ✅ Real-time Updates geplant |

### MVP Hardware-Anforderungen

| Komponente | MVP Minimum | MVP Empfohlen | Begründung |
|------------|-------------|---------------|------------|
| **CPU** | Intel i3 / AMD Ryzen 3 | Intel i5 / AMD Ryzen 5 | Vereinfachte Simulation |
| **RAM** | 4 GB | 8 GB | Kleinere Simulationen (1k Wagen) |
| **Storage** | 1 GB frei | 2 GB frei | Nur lokale Dateien |
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Aktuelle Versionen | Cross-Platform Python |

## 2.2 MVP Organisatorische Randbedingungen

### MVP Ressourcen-Beschränkungen

| Bereich | MVP Beschränkung | MVP Mitigation |
|---------|------------------|----------------|
| **Entwicklungszeit** | Maximal 5 Wochen | 3 Contexts statt 7 |
| **Team-Größe** | 3 Backend-Entwickler | Kein Frontend-Entwickler |
| **Komplexität** | Einfachste Lösung | Direkte Service-Aufrufe |
| **Features** | Nur Kern-Funktionalität | Keine Nice-to-have Features |

## 2.3 MVP Konventionen

### MVP Architektur-Konventionen

| Bereich | MVP Konvention | Vollversion |
|---------|----------------|-------------|
| **Architekturstil** | Layered Architecture mit DDD | Hexagonal + Event-Driven |
| **Contexts** | 3 Bounded Contexts | 7 Bounded Contexts |
| **Integration** | Direkte Service-Aufrufe | Event-driven Communication |
| **Datenhaltung** | File-based (CSV/JSON) | Database + Event Store |

### MVP Programmier-Konventionen

| Sprache | MVP Standard | Tools |
|---------|--------------|-------|
| **Python** | PEP 8, Type Hints | Ruff, MyPy |
| **JSON** | Pydantic Models | Pydantic Validation |
| **CSV** | Pandas DataFrames | Pandas |

### MVP Dokumentations-Konventionen

| Typ | MVP Standard | Format |
|-----|--------------|--------|
| **Architektur** | arc42 MVP Template | Markdown |
| **Code** | Docstrings, Type Hints | Python Standard |
| **Konfiguration** | JSON Schema | JSON |

## 2.4 MVP Qualitäts-Randbedingungen

### MVP Nicht-funktionale Anforderungen

| Kategorie | MVP Anforderung | Messbarkeit |
|-----------|-----------------|-------------|
| **Performance** | 1.000 Wagen in < 30 Sekunden | Einfache Benchmarks |
| **Usability** | Konfiguration via JSON-Dateien | Dokumentierte Beispiele |
| **Maintainability** | Saubere Architektur für Ausbau | Code-Review |
| **Portability** | Python Cross-Platform | Lokale Tests |

### MVP Sicherheits-Randbedingungen

| Bereich | MVP Anforderung | Begründung |
|---------|-----------------|------------|
| **Datenschutz** | Keine personenbezogenen Daten | DSGVO Compliance |
| **Vertraulichkeit** | Lokale Datenhaltung | Keine Cloud-Services |
| **Integrität** | Deterministische Ergebnisse | Planungssicherheit |
| **Verfügbarkeit** | Offline-Betrieb | Keine Netzwerk-Abhängigkeiten |

## 2.5 MVP Rechtliche Randbedingungen

### MVP Lizenzierung

| Komponente | Lizenz | MVP Kompatibilität |
|------------|--------|--------------------|
| **PopUpSim MVP** | Apache 2.0 | ✅ Open Source |
| **SimPy** | MIT License | ✅ Apache 2.0 kompatibel |
| **Matplotlib** | PSF License | ✅ Apache 2.0 kompatibel |
| **Pandas** | BSD License | ✅ Apache 2.0 kompatibel |

## 2.6 MVP Deployment-Randbedingungen

### MVP Deployment-Modell

| Aspekt | MVP Anforderung | Begründung |
|--------|-----------------|------------|
| **Installation** | Python Script + Requirements | Einfache Entwicklung |
| **Abhängigkeiten** | Nur Python Packages | Pip Install |
| **Konfiguration** | JSON/CSV Dateien | Einfache Anpassung |
| **Ausgabe** | Matplotlib PNG + CSV | Keine Web-UI erforderlich |

### MVP zu Vollversion Migration

| Aspekt | MVP → Vollversion | Vorbereitung |
|--------|-------------------|--------------|
| **Architektur** | Layered → Hexagonal | Saubere Domain Logic |
| **Integration** | Direct Calls → Events | Event-Interface vorbereiten |
| **UI** | Matplotlib → Web | JSON-API für Frontend |
| **Datenhaltung** | Files → Database | Repository Pattern |

## 2.7 MVP Entwicklungsstrategie

### Team-Aufteilung (3 Entwickler)

| Developer | MVP Verantwortung | Zeitaufwand |
|-----------|-------------------|-------------|
| **Dev 1** | Configuration Context + File I/O | 4-5 Wochen |
| **Dev 2** | Workshop Context + SimPy Integration | 4-5 Wochen |
| **Dev 3** | Simulation Control + Analytics/Matplotlib | 4-5 Wochen |

### MVP Meilensteine

| Woche | Meilenstein | Deliverable |
|-------|-------------|-------------|
| **1-2** | Grundarchitektur | Configuration Context funktionsfähig |
| **2-3** | Simulation Logic | Workshop Context + SimPy Integration |
| **3-4** | Integration | Simulation Control orchestriert alles |
| **4-5** | Analytics | Matplotlib Ausgabe + CSV Export |

### MVP Erfolgskriterien

| Kriterium | Definition | Messbarkeit |
|-----------|------------|-------------|
| **Funktionalität** | Grundlegende Simulation läuft | Demo möglich |
| **Ausgabe** | KPIs werden berechnet und visualisiert | Matplotlib Charts |
| **Erweiterbarkeit** | Saubere Architektur für Vollversion | Code-Review |
| **Dokumentation** | MVP-Architektur dokumentiert | arc42 MVP komplett |

---

**Navigation:** [← MVP Einführung](01-introduction-goals.md) | [MVP Kontextabgrenzung →](03-context.md)