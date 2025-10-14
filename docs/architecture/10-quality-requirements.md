# 10. Qualitätsanforderungen (MVP)

## 10.1 MVP Qualitätsziele

### MVP Qualitäts-Prioritäten

| Priorität | Qualitätsziel | MVP Szenario | Messbarkeit |
|-----------|---------------|--------------|-------------|
| **1** | **Schnelle Entwicklung** | MVP in 4-5 Wochen entwickelbar | Funktionsfähiger Prototyp |
| **2** | **Determinismus** | Gleiche Eingaben → identische Ergebnisse | Reproduzierbare Simulationsläufe |
| **3** | **Einfachheit** | Keine komplexe Installation | Single Python Script |
| **4** | **Testbarkeit** | Business Logic isoliert testbar | Unit Tests möglich |
| **5** | **Erweiterbarkeit** | Migration zur Vollversion | Saubere Architektur-Basis |

## 10.2 MVP Performance-Anforderungen

### MVP Performance-Ziele

```mermaid
graph TB
    subgraph "MVP Performance Ziele"
        subgraph "Ausführungszeit"
            Config[Konfiguration laden<br/>< 1 Sekunde]
            Setup[Werkstatt konfigurieren<br/>< 1 Sekunde]
            Sim[Simulationsausführung<br/>< 60 Sekunden für 1000 Wagen]
            Output[Ausgabe generieren<br/>< 5 Sekunden]
        end

        subgraph "Ressourcennutzung"
            Memory[Speicherverbrauch<br/>< 100 MB]
            CPU[CPU Auslastung<br/>< 80% während Simulation]
            Disk[Speicherplatz<br/>< 50 MB gesamt]
        end

        subgraph "Skalierbarkeit"
            Small[100 Wagen<br/>< 5 Sekunden]
            Medium[1000 Wagen<br/>< 30 Sekunden]
            Large[5000 Wagen<br/>< 2 Minuten]
        end
    end

    classDef time fill:#e3f2fd
    classDef resource fill:#e8f5e8
    classDef scale fill:#fff3e0

    class Config,Setup,Sim,Output time
    class Memory,CPU,Disk resource
    class Small,Medium,Large scale
```

### MVP Performance-Messungen

| Metrik | MVP Ziel | Messmethode | Akzeptanzkriterium |
|--------|----------|-------------|-------------------|
| **Startzeit** | < 2 Sekunden | `time python main.py --help` | Unter 2s auf Standard-Laptop |
| **Konfiguration laden** | < 1 Sekunde | Logging-Timestamps | JSON/CSV Parsing |
| **Simulationsgeschwindigkeit** | 1000 Wagen < 30s | SimPy-Profiling | Discrete Event Processing |
| **Arbeitsspeicherverbrauch** | < 100 MB | `psutil` Monitoring | Maximaler Speicherverbrauch |
| **Ausgabegenerierung** | < 5 Sekunden | Dateierstellungszeit | CSV + PNG Generierung |

## 10.3 MVP Usability-Anforderungen

### MVP Benutzerfreundlichkeit

```mermaid
graph TB
    subgraph "MVP Usability Ziele"
        subgraph "Benutzerfreundlichkeit"
            Install[Einfache Installation<br/>uv sync]
            Config[Einfache Konfiguration<br/>JSON/CSV Dateien]
            Run[Einfache Ausführung<br/>uv run python main.py]
        end

        subgraph "Fehlerbehandlung"
            Clear[Klare Fehlermeldungen<br/>Umsetzbare Rückmeldungen]
            Recovery[Graceful Degradation<br/>Teilergebnisse bei Fehler]
            Help[Eingebaute Hilfe<br/>--help Parameter]
        end

        subgraph "Ausgabequalität"
            Readable[Lesbare Ausgabe<br/>CSV Format]
            Visual[Visualisierung<br/>Matplotlib PNG]
            Logs[Detaillierte Logs<br/>Debugging-Informationen]
        end
    end

    classDef ease fill:#4caf50,stroke:#2e7d32
    classDef error fill:#ff9800,stroke:#e65100
    classDef output fill:#2196f3,stroke:#1565c0

    class Install,Config,Run ease
    class Clear,Recovery,Help error
    class Readable,Visual,Logs output
```

### MVP Usability-Kriterien

| Aspekt | MVP Anforderung | Messkriterium |
|--------|-----------------|---------------|
| **Installation** | < 5 Minuten Einrichtung | Dokumentierte Schritte |
| **Konfiguration** | Beispieldateien verfügbar | Template-Dateien |
| **Ausführung** | Ein Kommando startet Simulation | `uv run python main.py` |
| **Fehlermeldungen** | Verständliche Beschreibungen | Keine technischen Details |
| **Hilfe** | Integrierte Dokumentation | `--help` Parameter |

## 10.4 MVP Reliability-Anforderungen

### MVP Zuverlässigkeit

```mermaid
graph TB
    subgraph "MVP Reliability"
        subgraph "Fehlertoleranz"
            InputErrors[Eingabevalidierung<br/>Fehlerhafte Daten abfangen]
            RuntimeErrors[Laufzeitstabilität<br/>Keine Abstürze während Simulation]
            OutputErrors[Ausgaberobustheit<br/>Teilergebnisse bei Fehler]
        end

        subgraph "Determinismus"
            Reproducible[Reproduzierbare Ergebnisse<br/>Gleiche Eingabe → gleiche Ausgabe]
            Seeded[Seeded Random<br/>Kontrollierte Zufälligkeit]
            Consistent[Konsistentes Verhalten<br/>Plattformübergreifend]
        end

        subgraph "Wiederherstellung"
            Logging[Umfassendes Logging<br/>Debug-Informationen]
            Cleanup[Ressourcen-Bereinigung<br/>Keine Speicherlecks]
            Restart[Einfacher Neustart<br/>Keine persistenten Zustandsprobleme]
        end
    end

    classDef tolerance fill:#e3f2fd
    classDef determinism fill:#e8f5e8
    classDef recovery fill:#fff3e0

    class InputErrors,RuntimeErrors,OutputErrors tolerance
    class Reproducible,Seeded,Consistent determinism
    class Logging,Cleanup,Restart recovery
```

### MVP Reliability-Metriken

| Kategorie | MVP Ziel | Messmethode |
|-----------|----------|-------------|
| **Absturzrate** | < 1% bei gültigen Eingaben | Automatisierte Tests |
| **Determinismus** | 100% identische Ergebnisse | Wiederholte Ausführung |
| **Fehlerbehandlung** | Graceful Handling aller Eingabefehler | Negative Tests |
| **Speicherlecks** | Keine Speicherlecks | Memory Profiling |

## 10.5 MVP Maintainability-Anforderungen

### MVP Wartbarkeit

```python
# MVP Code Quality Standards
class CodeQualityMetrics:
    MAX_FUNCTION_LENGTH = 50      # Zeilen pro Funktion
    MAX_CLASS_LENGTH = 200        # Zeilen pro Klasse
    MAX_COMPLEXITY = 10           # Zyklomatische Komplexität
    MIN_TEST_COVERAGE = 70        # Prozent
    MAX_DEPENDENCIES = 5          # Pro Modul
```

### MVP Wartbarkeits-Ziele

| Aspekt | MVP Ziel | Messmethode |
|--------|----------|-------------|
| **Code Coverage** | > 70% für Business Logic | pytest-cov |
| **Dokumentation** | Alle öffentlichen APIs dokumentiert | Docstring-Coverage |
| **Komplexität** | Zyklomatische Komplexität < 10 | radon |
| **Abhängigkeiten** | < 10 externe Pakete | pyproject.toml |
| **Refactoring** | Einfache Erweiterung möglich | Architektur-Review |

## 10.6 MVP Portability-Anforderungen

### MVP Plattform-Unterstützung

```mermaid
graph TB
    subgraph "MVP Platform Support"
        subgraph "Betriebssysteme"
            Windows[Windows 10+<br/>Primäres Ziel]
            MacOS[macOS 10.15+<br/>Sekundäres Ziel]
            Linux[Ubuntu 20.04+<br/>Sekundäres Ziel]
        end

        subgraph "Python-Versionen"
            Python311[Python 3.11<br/>Minimum]
            Python312[Python 3.12<br/>Empfohlen]
        end

        subgraph "Hardware"
            Laptop[Standard Laptop<br/>4GB RAM, 2 Cores]
            Desktop[Desktop PC<br/>8GB RAM, 4 Cores]
        end
    end

    classDef primary fill:#4caf50,stroke:#2e7d32
    classDef secondary fill:#ff9800,stroke:#e65100
    classDef hardware fill:#2196f3,stroke:#1565c0

    class Windows,Python312,Desktop primary
    class MacOS,Linux,Python311,Laptop secondary
```

### MVP Portability-Tests

| Plattform | Teststatus | Kritische Features |
|----------|-------------|-------------------|
| **Windows 10** | ✅ Primär | Dateipfade, CSV-Encoding |
| **macOS** | ✅ Primär | Pfadtrenner, matplotlib |
| **Ubuntu 20.04** | ✅ Primär | Abhängigkeiten, Dateiberechtigungen |

## 10.7 MVP Security-Anforderungen

### MVP Sicherheits-Ziele

```mermaid
graph TB
    subgraph "MVP Security"
        subgraph "Eingabesicherheit"
            Validation[Eingabevalidierung<br/>Pydantic Models]
            Sanitization[Pfadbereinigung<br/>Kein Directory Traversal]
            Limits[Ressourcenlimits<br/>Dateigröße, Speicher]
        end

        subgraph "Datensicherheit"
            NoCredentials[Keine Credentials<br/>Keine sensiblen Daten gespeichert]
            LocalOnly[Lokale Verarbeitung<br/>Keine Netzwerkkommunikation]
            TempFiles[Sichere Temp-Dateien<br/>Ordnungsgemäße Bereinigung]
        end

        subgraph "Fehlersicherheit"
            NoLeakage[Kein Information Leakage<br/>Sichere Fehlermeldungen]
            Logging[Sicheres Logging<br/>Keine sensiblen Daten in Logs]
        end
    end

    classDef input fill:#e3f2fd
    classDef data fill:#e8f5e8
    classDef error fill:#fff3e0

    class Validation,Sanitization,Limits input
    class NoCredentials,LocalOnly,TempFiles data
    class NoLeakage,Logging error
```

### MVP Security-Maßnahmen

| Bereich | MVP Maßnahme | Implementierung |
|---------|--------------|-----------------|
| **Eingabevalidierung** | Pydantic Models | Automatische Typ-Validierung |
| **Dateizugriff** | Nur relative Pfade | Pfadbereinigung |
| **Fehlerbehandlung** | Sichere Fehlermeldungen | Keine Systempfade in Fehlern |
| **Logging** | Keine sensiblen Daten | Gefiltertes Logging |
| **Abhängigkeiten** | Nur bekannte Pakete | pyproject.toml mit Versionen |

## 10.8 MVP Testability-Anforderungen

### MVP Test-Strategie

```mermaid
graph TB
    subgraph "MVP Testing Strategy"
        subgraph "Unit Tests"
            Models[Domain Models<br/>Business Logic]
            Services[Service-Klassen<br/>Isoliertes Testen]
            Utils[Hilfsfunktionen<br/>Pure Functions]
        end

        subgraph "Integrationstests"
            FileIO[File I/O<br/>JSON/CSV-Verarbeitung]
            SimPy[SimPy Integration<br/>Simulation Engine]
            EndToEnd[End-to-End<br/>Vollständige Szenarien]
        end

        subgraph "Manuelle Tests"
            Scenarios[Testszenarien<br/>Reale Konfigurationen]
            Performance[Performance-Tests<br/>Große Datensätze]
            Platforms[Plattformtests<br/>Plattformübergreifend]
        end
    end

    classDef unit fill:#4caf50,stroke:#2e7d32
    classDef integration fill:#ff9800,stroke:#e65100
    classDef manual fill:#9e9e9e,stroke:#616161

    class Models,Services,Utils unit
    class FileIO,SimPy,EndToEnd integration
    class Scenarios,Performance,Platforms manual
```

### MVP Test-Metriken

| Test-Typ | MVP Ziel | Automatisierung |
|----------|----------|-----------------|
| **Unit Tests** | > 80% Coverage | ✅ pytest |
| **Integrationstests** | Alle Hauptpfade | ✅ pytest |
| **Performance-Tests** | Benchmark-Szenarien | ⚠️ Manuell |
| **Plattformtests** | Windows + Linux + MacOs | ⚠️ Manuell |
Die Plattformtests können ggf. direkt in der GitHub Pipeline automatisiert werden. Z.B. ein Matrix Job, der nicht über Python-Versionen läuft sondern über unterschiedliche Beriebssysteme.

---

**Navigation:** [← MVP Architekturentscheidungen](09-architecture-decisions.md) | [MVP Risiken →](11-risks-technical-debt.md)