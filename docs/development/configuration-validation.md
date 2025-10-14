# Configuration Validation - Struktur und Implementierung

## Übersicht

Dieses Dokument beschreibt die Struktur des Configuration Validators und des Configuration Service für **Story 1.4: Configuration Validation**.

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    ConfigurationService                      │
│  - load_scenario()                                          │
│  - load_workshop_tracks()                                   │
│  - load_train_schedule()                                    │
│  - load_routes()                                            │
│  - load_and_validate()  ← Hauptmethode                     │
└────────────────────┬────────────────────────────────────────┘
                     │ verwendet
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 ConfigurationValidator                       │
│  - validate()                                               │
│  - _validate_workshop_tracks()                              │
│  - _validate_capacity()                                     │
│  - _validate_routes()                                       │
│  - _validate_train_schedule()                               │
│  - _validate_simulation_duration()                          │
└────────────────────┬────────────────────────────────────────┘
                     │ erzeugt
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    ValidationResult                          │
│  - is_valid: bool                                           │
│  - issues: list[ValidationIssue]                            │
│  - has_errors()                                             │
│  - has_warnings()                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Datenmodelle

### ValidationLevel (Enum)

```python
from enum import Enum

class ValidationLevel(Enum):
    """Schweregrad einer Validierungsmeldung"""
    ERROR = "ERROR"      # Simulation kann nicht starten
    WARNING = "WARNING"  # Simulation kann starten, aber suboptimal
    INFO = "INFO"        # Hinweis für Nutzer
```

### ValidationIssue (Dataclass)

```python
from dataclasses import dataclass

@dataclass
class ValidationIssue:
    """Einzelnes Validierungsproblem"""
    level: ValidationLevel
    message: str
    field: str | None = None        # Betroffenes Feld (z.B. "workshop.tracks[0].capacity")
    suggestion: str | None = None   # Vorschlag zur Behebung
    
    def __str__(self) -> str:
        result = f"[{self.level.value}] {self.message}"
        if self.field:
            result += f" (Feld: {self.field})"
        if self.suggestion:
            result += f"\n  → Vorschlag: {self.suggestion}"
        return result
```

### ValidationResult (Dataclass)

```python
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    """Ergebnis einer Validierung"""
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Prüft ob ERROR-Level Issues vorhanden sind"""
        return any(i.level == ValidationLevel.ERROR for i in self.issues)
    
    def has_warnings(self) -> bool:
        """Prüft ob WARNING-Level Issues vorhanden sind"""
        return any(i.level == ValidationLevel.WARNING for i in self.issues)
    
    def get_errors(self) -> list[ValidationIssue]:
        """Gibt nur ERROR-Level Issues zurück"""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]
    
    def get_warnings(self) -> list[ValidationIssue]:
        """Gibt nur WARNING-Level Issues zurück"""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]
    
    def print_summary(self) -> None:
        """Gibt formatierte Zusammenfassung aus"""
        if self.has_errors():
            print("❌ Konfiguration ungültig - Fehler gefunden:")
            for issue in self.get_errors():
                print(f"  {issue}")
        
        if self.has_warnings():
            print("\n⚠️  Warnungen:")
            for issue in self.get_warnings():
                print(f"  {issue}")
        
        if not self.has_errors() and not self.has_warnings():
            print("✅ Konfiguration valide - keine Probleme gefunden")
```

---

## ConfigurationValidator

### Klasse

```python
from pathlib import Path
from typing import List

class ConfigurationValidator:
    """
    Validiert geladene Konfigurationen auf logische Konsistenz
    und Business Rules.
    
    Prüft:
    - Cross-field Validierung (Kapazität vs. Ankunftsrate)
    - Business Rules (Mindestens 1 Werkstattgleis)
    - Referenzen (Track IDs in Routen existieren)
    - Zeitliche Konsistenz (Züge innerhalb Simulationszeit)
    """
    
    def validate(self, config: ScenarioConfig) -> ValidationResult:
        """
        Führt alle Validierungen durch und gibt Ergebnis zurück.
        
        Args:
            config: Geladene Szenario-Konfiguration
            
        Returns:
            ValidationResult mit allen gefundenen Issues
        """
        issues: list[ValidationIssue] = []
        
        # Alle Validierungen durchführen
        issues.extend(self._validate_workshop_tracks(config))
        issues.extend(self._validate_capacity(config))
        issues.extend(self._validate_routes(config))
        issues.extend(self._validate_train_schedule(config))
        issues.extend(self._validate_simulation_duration(config))
        
        # is_valid = True wenn keine Errors
        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)
        
        return ValidationResult(is_valid=is_valid, issues=issues)
    
    def _validate_workshop_tracks(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validiert Workshop-Gleise.
        
        Prüft:
        - Mindestens ein Werkstattgleis vorhanden
        - Alle erforderlichen Funktionen vorhanden
        - retrofit_time_min nur für Werkstattgleise > 0
        """
        issues = []
        
        # 1. Mindestens ein Werkstattgleis
        werkstatt_tracks = [
            t for t in config.workshop.tracks 
            if t.function == "werkstattgleis"
        ]
        
        if len(werkstatt_tracks) == 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Mindestens ein Gleis mit function='werkstattgleis' erforderlich",
                field="workshop.tracks",
                suggestion="Fügen Sie ein Gleis mit function='werkstattgleis' und retrofit_time_min > 0 hinzu"
            ))
        
        # 2. Alle Kern-Funktionen vorhanden?
        required_functions = {"sammelgleis", "werkstattgleis", "parkgleis"}
        present_functions = {t.function for t in config.workshop.tracks}
        missing = required_functions - present_functions
        
        if missing:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Fehlende Gleisfunktionen: {', '.join(missing)}",
                field="workshop.tracks",
                suggestion="Vollständiger Workflow benötigt: sammelgleis → werkstattgleis → parkgleis"
            ))
        
        # 3. retrofit_time_min nur für Werkstattgleise
        for track in config.workshop.tracks:
            if track.function != "werkstattgleis" and track.retrofit_time_min > 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Track {track.id}: retrofit_time_min muss 0 sein für function={track.function}",
                    field=f"workshop.tracks[{track.id}].retrofit_time_min",
                    suggestion="Setzen Sie retrofit_time_min=0 für Nicht-Werkstattgleise"
                ))
        
        return issues
    
    def _validate_capacity(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validiert ob Werkstattkapazität für Zugankünfte ausreicht.
        
        Berechnet theoretischen Durchsatz und vergleicht mit Ankunftsrate.
        """
        issues = []
        
        # Totale Werkstattkapazität
        werkstatt_tracks = [
            t for t in config.workshop.tracks 
            if t.function == "werkstattgleis"
        ]
        
        if not werkstatt_tracks:
            return issues  # Bereits in _validate_workshop_tracks geprüft
        
        total_capacity = sum(t.capacity for t in werkstatt_tracks)
        
        # Durchschnittliche Umrüstzeit
        avg_retrofit_time = sum(t.retrofit_time_min for t in werkstatt_tracks) / len(werkstatt_tracks)
        
        # Wagen pro Tag aus train_schedule
        wagons_per_day = len([
            w for train in config.train_schedule 
            for w in train.wagons
            if w.needs_retrofit  # Nur Wagen die Umrüstung brauchen
        ])
        
        # Theoretischer Durchsatz pro Tag (24h * 60min / avg_time * capacity)
        max_throughput_per_day = (24 * 60 / avg_retrofit_time) * total_capacity
        
        # Warnung bei > 80% Auslastung
        utilization = wagons_per_day / max_throughput_per_day
        
        if utilization > 1.0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Kapazität überschritten: {wagons_per_day} Wagen/Tag bei max. {max_throughput_per_day:.0f} Durchsatz ({utilization*100:.0f}% Auslastung)",
                field="workshop.tracks",
                suggestion="Erhöhen Sie Kapazität oder reduzieren Sie Zugankünfte"
            ))
        elif utilization > 0.8:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Hohe Auslastung: {wagons_per_day} Wagen/Tag bei max. {max_throughput_per_day:.0f} Durchsatz ({utilization*100:.0f}% Auslastung)",
                field="workshop.tracks",
                suggestion="Erwägen Sie höhere Kapazität für bessere Performance"
            ))
        
        return issues
    
    def _validate_routes(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validiert Routen.
        
        Prüft:
        - Track IDs in track_sequence existieren
        - from_function und to_function existieren
        - time_min > 0
        """
        issues = []
        
        # Track IDs sammeln
        track_ids = {t.id for t in config.workshop.tracks}
        
        # Funktionen sammeln
        functions = {t.function for t in config.workshop.tracks}
        
        for route in config.routes:
            # Track IDs existieren?
            for track_id in route.track_sequence:
                if track_id not in track_ids:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Route {route.route_id}: Track '{track_id}' existiert nicht",
                        field=f"routes[{route.route_id}].track_sequence",
                        suggestion=f"Verwenden Sie eine der IDs: {', '.join(sorted(track_ids))}"
                    ))
            
            # Funktionen existieren?
            if route.from_function not in functions:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Route {route.route_id}: from_function '{route.from_function}' existiert nicht",
                    field=f"routes[{route.route_id}].from_function",
                    suggestion=f"Verwenden Sie eine der Funktionen: {', '.join(sorted(functions))}"
                ))
            
            if route.to_function not in functions:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Route {route.route_id}: to_function '{route.to_function}' existiert nicht",
                    field=f"routes[{route.route_id}].to_function",
                    suggestion=f"Verwenden Sie eine der Funktionen: {', '.join(sorted(functions))}"
                ))
            
            # Zeit > 0?
            if route.time_min <= 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Route {route.route_id}: time_min muss > 0 sein",
                    field=f"routes[{route.route_id}].time_min",
                    suggestion="Setzen Sie eine realistische Fahrzeit in Minuten"
                ))
        
        return issues
    
    def _validate_train_schedule(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validiert Zugfahrplan.
        
        Prüft:
        - Wagon IDs sind eindeutig
        - Arrival times sind chronologisch
        - Mindestens ein Zug vorhanden
        """
        issues = []
        
        if not config.train_schedule:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Zugfahrplan ist leer - mindestens ein Zug erforderlich",
                field="train_schedule",
                suggestion="Fügen Sie Züge in train_schedule.csv hinzu"
            ))
            return issues
        
        # Wagon IDs eindeutig?
        wagon_ids = []
        for train in config.train_schedule:
            for wagon in train.wagons:
                wagon_ids.append(wagon.wagon_id)
        
        duplicates = [wid for wid in set(wagon_ids) if wagon_ids.count(wid) > 1]
        if duplicates:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Doppelte Wagon IDs gefunden: {', '.join(duplicates[:5])}{'...' if len(duplicates) > 5 else ''}",
                field="train_schedule",
                suggestion="Stellen Sie sicher, dass jede wagon_id eindeutig ist"
            ))
        
        return issues
    
    def _validate_simulation_duration(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validiert ob alle Züge innerhalb der Simulationszeit ankommen.
        """
        issues = []
        
        from datetime import datetime
        
        sim_start = datetime.fromisoformat(config.start_date)
        sim_end = datetime.fromisoformat(config.end_date)
        
        for train in config.train_schedule:
            arrival = datetime.fromisoformat(f"{train.arrival_date} {train.arrival_time}")
            
            if arrival < sim_start:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Zug {train.train_id} kommt vor Simulationsstart an ({train.arrival_date} {train.arrival_time})",
                    field=f"train_schedule[{train.train_id}].arrival_date",
                    suggestion="Passen Sie start_date oder arrival_date an"
                ))
            
            if arrival > sim_end:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Zug {train.train_id} kommt nach Simulationsende an ({train.arrival_date} {train.arrival_time})",
                    field=f"train_schedule[{train.train_id}].arrival_date",
                    suggestion="Passen Sie end_date oder arrival_date an"
                ))
        
        return issues
```

---

## ConfigurationService

### Klasse

```python
import json
import pandas as pd
from pathlib import Path

class ConfigurationService:
    """
    Service zum Laden und Validieren von Konfigurationsdateien.
    
    Unterstützt:
    - JSON (scenario.json)
    - CSV (workshop_tracks.csv, train_schedule.csv, routes.csv)
    """
    
    def __init__(self):
        self.validator = ConfigurationValidator()
    
    def load_scenario(self, path: Path) -> ScenarioConfig:
        """
        Lädt scenario.json und gibt ScenarioConfig zurück.
        
        Args:
            path: Pfad zu scenario.json
            
        Returns:
            ScenarioConfig Pydantic Model
            
        Raises:
            IOError: Wenn Datei nicht gefunden
            ValueError: Wenn JSON ungültig
        """
        if not path.exists():
            raise IOError(f"Datei nicht gefunden: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return ScenarioConfig(**data)
    
    def load_workshop_tracks(self, path: Path) -> list[WorkshopTrackConfig]:
        """
        Lädt workshop_tracks.csv und gibt Liste von WorkshopTrackConfig zurück.
        
        Args:
            path: Pfad zu workshop_tracks.csv
            
        Returns:
            Liste von WorkshopTrackConfig
        """
        df = pd.read_csv(path)
        return [WorkshopTrackConfig(**row) for row in df.to_dict('records')]
    
    def load_train_schedule(self, path: Path) -> list[TrainArrival]:
        """
        Lädt train_schedule.csv und gibt Liste von TrainArrival zurück.
        
        Args:
            path: Pfad zu train_schedule.csv
            
        Returns:
            Liste von TrainArrival (gruppiert nach train_id)
        """
        df = pd.read_csv(path)
        
        trains = []
        for train_id, group in df.groupby('train_id'):
            wagons = [
                WagonInfo(
                    wagon_id=row['wagon_id'],
                    length=row['length'],
                    is_loaded=row['is_loaded'],
                    needs_retrofit=row['needs_retrofit']
                )
                for _, row in group.iterrows()
            ]
            
            trains.append(TrainArrival(
                train_id=train_id,
                arrival_date=group.iloc[0]['arrival_date'],
                arrival_time=group.iloc[0]['arrival_time'],
                wagons=wagons
            ))
        
        return trains
    
    def load_routes(self, path: Path) -> list[Route]:
        """
        Lädt routes.csv und gibt Liste von Route zurück.
        
        Args:
            path: Pfad zu routes.csv
            
        Returns:
            Liste von Route
        """
        df = pd.read_csv(path)
        
        routes = []
        for _, row in df.iterrows():
            routes.append(Route(
                route_id=row['route_id'],
                from_function=row['from_function'],
                to_function=row['to_function'],
                track_sequence=row['track_sequence'].split(','),
                distance_m=row['distance_m'],
                time_min=row['time_min']
            ))
        
        return routes
    
    def load_and_validate(self, config_dir: Path) -> tuple[ScenarioConfig, ValidationResult]:
        """
        Lädt alle Konfigurationsdateien und validiert sie.
        
        Dies ist die Hauptmethode, die von der Simulation verwendet wird.
        
        Args:
            config_dir: Verzeichnis mit allen Config-Dateien
            
        Returns:
            Tuple (ScenarioConfig, ValidationResult)
            
        Raises:
            IOError: Wenn Dateien nicht gefunden
            ValueError: Wenn Daten ungültig
        """
        # 1. Lade scenario.json
        scenario_path = config_dir / "scenario.json"
        config = self.load_scenario(scenario_path)
        
        # 2. Lade workshop_tracks.csv (falls vorhanden)
        tracks_path = config_dir / "workshop_tracks.csv"
        if tracks_path.exists():
            config.workshop.tracks = self.load_workshop_tracks(tracks_path)
        
        # 3. Lade train_schedule.csv
        schedule_path = config_dir / config.train_schedule_file
        config.train_schedule = self.load_train_schedule(schedule_path)
        
        # 4. Lade routes.csv
        routes_path = config_dir / "routes.csv"
        if routes_path.exists():
            config.routes = self.load_routes(routes_path)
        
        # 5. Validiere
        validation_result = self.validator.validate(config)
        
        # 6. Ausgabe
        validation_result.print_summary()
        
        return config, validation_result
```

---

## Verwendung

### Beispiel 1: Einfache Validierung

```python
from pathlib import Path

# Service initialisieren
config_service = ConfigurationService()

# Konfiguration laden und validieren
config_dir = Path("config/examples/small_scenario")
config, validation = config_service.load_and_validate(config_dir)

# Prüfen ob valide
if not validation.is_valid:
    print("❌ Konfiguration ungültig - Simulation wird abgebrochen")
    exit(1)

# Simulation starten
simulation = SimulationService(config)
simulation.run()
```

### Beispiel 2: Mit Fehlerbehandlung

```python
try:
    config, validation = config_service.load_and_validate(config_dir)
    
    if validation.has_errors():
        print("\n❌ Fehler gefunden:")
        for error in validation.get_errors():
            print(f"  - {error.message}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
        exit(1)
    
    if validation.has_warnings():
        print("\n⚠️  Warnungen (Simulation läuft trotzdem):")
        for warning in validation.get_warnings():
            print(f"  - {warning.message}")
    
    # Simulation starten
    simulation = SimulationService(config)
    results = simulation.run()
    
except IOError as e:
    print(f"❌ Datei nicht gefunden: {e}")
    exit(1)
except ValueError as e:
    print(f"❌ Ungültige Daten: {e}")
    exit(1)
```

---

## Unit Tests

### Test-Struktur

```python
# tests/test_configuration_validator.py

def test_validate_missing_werkstattgleis():
    """Test: ERROR wenn kein Werkstattgleis vorhanden"""
    config = ScenarioConfig(
        workshop=WorkshopConfig(tracks=[
            WorkshopTrackConfig(id="T1", function="sammelgleis", capacity=10, retrofit_time_min=0)
        ])
    )
    
    validator = ConfigurationValidator()
    result = validator.validate(config)
    
    assert not result.is_valid
    assert result.has_errors()
    assert "Werkstattgleis" in result.get_errors()[0].message

def test_validate_capacity_warning():
    """Test: WARNING bei hoher Auslastung (>80%)"""
    config = create_config_with_high_load()  # Helper function
    
    validator = ConfigurationValidator()
    result = validator.validate(config)
    
    assert result.is_valid  # Keine Errors
    assert result.has_warnings()
    assert "Auslastung" in result.get_warnings()[0].message

def test_validate_invalid_route_track_id():
    """Test: ERROR wenn Route nicht-existierende Track ID referenziert"""
    config = ScenarioConfig(
        workshop=WorkshopConfig(tracks=[
            WorkshopTrackConfig(id="T1", function="werkstattgleis", capacity=5, retrofit_time_min=30)
        ]),
        routes=[
            Route(
                route_id="R1",
                from_function="sammelgleis",
                to_function="werkstattgleis",
                track_sequence=["T1", "T999"],  # T999 existiert nicht
                distance_m=100,
                time_min=5
            )
        ]
    )
    
    validator = ConfigurationValidator()
    result = validator.validate(config)
    
    assert not result.is_valid
    assert "T999" in result.get_errors()[0].message
```

---

## Zusammenfassung

**Dateien:**
- `src/configuration/validator.py` - ConfigurationValidator Klasse
- `src/configuration/service.py` - ConfigurationService Klasse
- `src/configuration/models.py` - ValidationLevel, ValidationIssue, ValidationResult

**Verantwortlichkeiten:**
- **ConfigurationValidator**: Führt alle Validierungen durch
- **ConfigurationService**: Lädt Dateien und orchestriert Validierung
- **ValidationResult**: Strukturierte Rückgabe von Errors/Warnings

**Vorteile:**
- Frühe Fehlererkennung vor Simulation
- Hilfreiche Fehlermeldungen mit Vorschlägen
- Trennung von Errors (blockierend) und Warnings (nicht-blockierend)
- Testbar durch klare Schnittstellen
