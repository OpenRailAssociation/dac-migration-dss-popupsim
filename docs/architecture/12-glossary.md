# 12. Glossar (MVP)

## 12.1 MVP Fachbegriffe

### Bahnbetrieb (MVP)

| Begriff | MVP Definition | Beispiel |
|---------|----------------|----------|
| **DAK** | Digitale Automatische Kupplung - Neue Kupplungstechnologie | Ersetzt Schraubkupplung |
| **Pop-Up-Werkstatt** | Temporäre Umrüstungswerkstatt für DAK-Migration | Mehrere Umrüstplätze auf einem Werkstattgleis, 3 Wochen Betrieb |
| **Retrofit** | Umrüstung von Schraubkupplung auf DAK | 40-50 Minuten pro Wagen |
| **Parkgleis** | Gleis auf denen Wagen geparkt werden| Kapazität: Gesamtlänge-25m |
| **Werkstattgleis** | Gleis auf denen die Wagen umgerüstet werden| Kapazität: Entspricht Anzahl Umrüststationen und eine Lok |
| **Werkstattgleis** | Gleis auf denen die Wagen umgerüstet werden| Kapazität: Entspricht Anzahl Umrüststationen und eine Lok |
| **Sammelgleis** | Gleis zur Zwischenlagerung von Wagen | Kapazität: 20-50 Wagen |
| **Umrüststation** | Arbeitsplatz für DAK-Umrüstung | 1-2 Arbeiter pro Station |
| **Wagen** | Güterwagen (Eisenbahnfahrzeug) | Verschiedene Typen, unterschiedliche Umrüstzeiten |
| **Wagengruppe** | Mehrere gekuppelte Güterwagen (Eisenbahnfahrzeug) | Wagengruppe aus 3 Wagen |
| **Zug** | Zusammenstellung mehrerer Wagen | 10-30 oder mehr Wagen pro Zug |

### Simulation (MVP)

| Begriff | MVP Definition | Verwendung |
|---------|----------------|------------|
| **Discrete Event Simulation** | Ereignisgesteuerte Simulation mit SimPy | Zeitsprünge zwischen Events |
| **SimPy** | Python-Framework für Discrete Event Simulation | Kern der MVP-Simulation |
| **Event** | Simulationsereignis (Ankunft, Start, Ende) | `TrainArrival`, `RetrofitComplete` |
| **Process** | SimPy-Prozess für Geschäftslogik | `retrofit_process()` |
| **Environment** | SimPy-Simulationsumgebung | Zeitsteuerung und Event-Queue |
| **Determinismus** | Reproduzierbare Simulationsergebnisse | Gleicher Random-Seed → gleiche Ergebnisse |

## 12.2 MVP Architektur-Begriffe

### Layered Architecture (MVP)

| Begriff | MVP Definition | Layer |
|---------|----------------|-------|
| **Presentation Layer** | CLI und File Output | Oberste Schicht |
| **Business Logic Layer** | Domain Services und Geschäftslogik | Kern-Schicht |
| **Data Access Layer** | File I/O (JSON/CSV) | Daten-Schicht |
| **Infrastructure Layer** | SimPy, Matplotlib, File System | Unterste Schicht |
| **Service** | Geschäftslogik-Komponente | `ConfigurationService`, `WorkshopService` |
| **Model** | Datenmodell/Entity | `Workshop`, `Station`, `Wagon` |

### Bounded Context (MVP)

| Begriff | MVP Definition | Verantwortung |
|---------|----------------|---------------|
| **Configuration Context** | JSON/CSV Import und Validierung | Szenario-Setup |
| **Workshop Context** | DAK-Umrüstung und SimPy-Integration | Kern-Geschäftslogik |
| **Simulation Control Context** | Orchestrierung und Output-Generierung | Gesamtsteuerung |
| **Context** | Fachlicher Abschnitt mit klaren Grenzen | Bounded Context nach DDD |
| **Domain Model** | Fachliches Datenmodell eines Context | Entities, Value Objects |

## 12.3 MVP Technische Begriffe

### Python/SimPy (MVP)

| Begriff | MVP Definition | Verwendung |
|---------|----------------|------------|
| **Pydantic** | Python-Library für Datenvalidierung | Configuration Models |
| **Matplotlib** | Python-Library für Diagramme | Chart-Generierung |
| **Pandas** | Python-Library für Datenverarbeitung | CSV-Verarbeitung (optional) |
| **Type Hints** | Python-Typisierung | Code-Dokumentation und IDE-Support |
| **Dataclass** | Python-Decorator für Datenklassen | Domain Models |
| **Virtual Environment** | Isolierte Python-Umgebung | Dependency Management |

### File Formats (MVP)

| Begriff | MVP Definition | Struktur |
|---------|----------------|----------|
| **JSON** | JavaScript Object Notation | Konfigurationsdateien |
| **CSV** | Comma-Separated Values | Tabellarische Daten |
| **PNG** | Portable Network Graphics | Matplotlib-Charts |
| **uv.lock** | Python uv Lockfile | Lockfile |

## 12.4 MVP Qualitätsbegriffe

### Performance (MVP)

| Begriff | MVP Definition | Zielwert |
|---------|----------------|----------|
| **Durchsatz** | Verarbeitete Wagen pro Stunde | 20-40 Wagen/h |
| **Latenz** | Zeit bis Simulationsstart | < 2 Sekunden |
| **Speicherverbrauch** | Speicherverbrauch der Anwendung | < 100 MB |
| **Ausführungszeit** | Gesamte Simulationsdauer | < 30 Sekunden für 1000 Wagen |
| **Skalierbarkeit** | Maximale Szenario-Größe | 5000 Wagen |

### Testing (MVP)

| Begriff | MVP Definition | Tool |
|---------|----------------|------|
| **Unit Test** | Test einzelner Funktionen/Klassen | pytest |
| **Integration Test** | Test von Komponenten-Zusammenspiel | pytest |
| **End-to-End Test** | Test kompletter Simulationsläufe | Manual |
| **Test Coverage** | Prozent getesteter Code-Zeilen | pytest-cov |
| **Mock** | Simulierte Abhängigkeit für Tests | unittest.mock |

## 12.5 MVP Prozess-Begriffe

### Entwicklung (MVP)

| Begriff | MVP Definition | Dauer |
|---------|----------------|-------|
| **MVP** | Minimum Viable Product | 4-5 Wochen |
| **Sprint** | Entwicklungsiteration | 1 Woche |
| **Milestone** | Wichtiger Entwicklungsschritt | Ende jeder Woche |
| **Code Review** | Peer-Review von Code-Änderungen | Kontinuierlich |
| **Refactoring** | Code-Verbesserung ohne Funktionsänderung | Bei Bedarf |

### Migration (MVP)

| Begriff | MVP Definition | Aufwand |
|---------|----------------|---------|
| **Technische Schulden** | Bewusste Vereinfachungen für Geschwindigkeit | Dokumentiert |
| **Migration Pfad** | Weg von MVP zur Vollversion | Geplant |
| **Interface-Vorbereitung** | Vorbereitung für Architektur-Migration | Während MVP |
| **Hexagonal Architecture** | Ziel-Architektur der Vollversion | Post-MVP |
| **Event-driven Architecture** | Ziel-Integration der Vollversion | Post-MVP |

## 12.6 MVP KPI-Begriffe

### Simulation KPIs (MVP)

| Begriff | MVP Definition | Berechnung |
|---------|----------------|------------|
| **Durchsatz** | Umgerüstete Wagen pro Zeiteinheit | `wagons_processed / simulation_hours` |
| **Auslastung** | Prozentuale Nutzung der Stationen | `busy_time / total_time * 100` |
| **Wartezeit** | Durchschnittliche Wartezeit der Wagen | `sum(waiting_times) / wagon_count` |
| **Warteschlangenlänge** | Anzahl wartender Wagen | `wagons_in_queue` |
| **Engpass** | Ressource mit höchster Auslastung | Station mit `max(utilization)` |

### Output KPIs (MVP)

| Begriff | MVP Definition | Format |
|---------|----------------|--------|
| **CSV Export** | Strukturierte KPI-Daten | `simulation_results.csv` |
| **Chart** | Visualisierte KPI-Daten | `kpi_charts.png` |
| **Log** | Ereignis-Timeline | `simulation_log.json` |
| **Summary** | Zusammenfassung der Ergebnisse | Console Output |

## 12.7 MVP Fehler-Begriffe

### Error Handling (MVP)

| Begriff | MVP Definition | Behandlung |
|---------|----------------|------------|
| **Configuration Error** | Fehler beim Laden der Konfiguration | Sofortiger Exit mit Fehlermeldung |
| **Validation Error** | Ungültige Eingabedaten | Liste aller Validierungsfehler |
| **Simulation Error** | Laufzeitfehler während Simulation | Graceful Degradation |
| **Output Error** | Fehler bei Ergebnis-Generierung | Weiter ohne fehlgeschlagene Ausgabe |
| **Graceful Degradation** | Teilweise Funktionalität bei Fehlern | Partial Results |

## 12.8 MVP Abkürzungen

### Technische Abkürzungen

| Abkürzung | Vollform | Kontext |
|-----------|----------|---------|
| **MVP** | Minimum Viable Product | Entwicklungsphase |
| **DDD** | Domain-Driven Design | Architektur-Ansatz |
| **CLI** | Command Line Interface | Benutzeroberfläche |
| **I/O** | Input/Output | Datei-Operationen |
| **API** | Application Programming Interface | Schnittstelle |
| **JSON** | JavaScript Object Notation | Datenformat |
| **CSV** | Comma-Separated Values | Datenformat |
| **PNG** | Portable Network Graphics | Bildformat |

### Fachliche Abkürzungen

| Abkürzung | Vollform | Kontext |
|-----------|----------|---------|
| **DAK** | Digitale Automatische Kupplung | Bahntechnik |
| **KPI** | Key Performance Indicator | Leistungskennzahl |
| **SLA** | Service Level Agreement | Qualitätsziel |
| **ROI** | Return on Investment | Wirtschaftlichkeit |

---

**Navigation:** [← MVP Risiken](11-risks-technical-debt.md) | [MVP README ↑](README.md)

---

**MVP Glossar Status:** ✅ Vollständig | **Begriffe:** 80+ | **Kategorien:** 8