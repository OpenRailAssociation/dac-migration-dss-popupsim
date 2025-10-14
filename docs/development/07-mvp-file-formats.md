# PopUpSim MVP - File Formats

## Übersicht

Diese Datei definiert alle Input- und Output-Dateiformate für den MVP mit JSON Schemas und Beispielen.

---

## Input Files

### 1. scenario.json

**Zweck:** Hauptkonfiguration für Simulationsszenario

**Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["scenario_id", "start_date", "end_date", "workshop", "train_schedule_file"],
  "properties": {
    "scenario_id": {
      "type": "string",
      "description": "Eindeutige Szenario-ID"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "description": "Simulationsstart (YYYY-MM-DD)"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "description": "Simulationsende (YYYY-MM-DD)"
    },
    "random_seed": {
      "type": "integer",
      "minimum": 0,
      "description": "Seed für Reproduzierbarkeit"
    },
    "workshop": {
      "type": "object",
      "required": ["tracks"],
      "properties": {
        "tracks": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/definitions/track"
          }
        }
      }
    },
    "train_schedule_file": {
      "type": "string",
      "description": "Pfad zur Zugfahrplan-Datei (CSV)"
    }
  },
  "definitions": {
    "track": {
      "type": "object",
      "required": ["id", "capacity", "retrofit_time_min"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^TRACK\\d{2}$",
          "description": "Track ID (z.B. TRACK01)"
        },
        "capacity": {
          "type": "integer",
          "minimum": 1,
          "maximum": 20,
          "description": "Maximale Anzahl Wagen gleichzeitig"
        },
        "retrofit_time_min": {
          "type": "integer",
          "minimum": 10,
          "maximum": 300,
          "description": "Umrüstzeit pro Wagen in Minuten"
        }
      }
    }
  }
}
```

**Beispiel:**
```json
{
  "scenario_id": "scenario_001",
  "start_date": "2025-10-15",
  "end_date": "2025-10-16",
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "capacity": 5,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK02",
        "capacity": 3,
        "retrofit_time_min": 45
      },
      {
        "id": "TRACK03",
        "capacity": 4,
        "retrofit_time_min": 35
      }
    ]
  },
  "train_schedule_file": "train_schedule.csv"
}
```

---

### 2. workshop_tracks.csv (Alternative zu JSON)

**Zweck:** Tabellarische Definition von Werkstattgleisen

**Format:**
```csv
track_id,capacity,retrofit_time_min
TRACK01,5,30
TRACK02,3,45
TRACK03,4,35
```

**Validierung:**
- `track_id`: Muss Pattern `TRACK\d{2}` entsprechen
- `capacity`: Integer, 1-20
- `retrofit_time_min`: Integer, 10-300

**Verwendung:**
```python
import pandas as pd

df = pd.read_csv("workshop_tracks.csv")
tracks = [
    WorkshopTrackConfig(**row)
    for row in df.to_dict('records')
]
```

---

### 3. train_schedule.csv

**Zweck:** Explizite Definition aller Zugankünfte mit Wageninformationen

**Format:**
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,08:00,WAGON001_01,15.5,true,true
TRAIN001,2024-01-15,08:00,WAGON001_02,15.5,false,true
TRAIN001,2024-01-15,08:00,WAGON001_03,15.5,true,false
TRAIN002,2024-01-15,10:30,WAGON002_01,18.0,true,true
TRAIN002,2024-01-15,10:30,WAGON002_02,18.0,true,true
```

**Validierung:**
- `train_id`: String, eindeutig pro Zug
- `arrival_date`: Date (YYYY-MM-DD)
- `arrival_time`: Time (HH:MM)
- `wagon_id`: String, eindeutig
- `length`: Float, > 0 (Meter)
- `is_loaded`: Boolean (true/false)
- `needs_retrofit`: Boolean (true/false)

**Verwendung:**
```python
import pandas as pd
from datetime import datetime

df = pd.read_csv("train_schedule.csv")
df['arrival_datetime'] = pd.to_datetime(
    df['arrival_date'] + ' ' + df['arrival_time']
)

# Gruppiere nach Zügen
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
```

---

## Output Files

### 1. results/summary.csv

**Zweck:** Zusammenfassung der KPIs

**Format:**
```csv
metric,value,unit
scenario_id,scenario_001,
duration_hours,8.0,hours
total_wagons_processed,75,wagons
throughput_per_hour,9.375,wagons/hour
average_waiting_time,12.5,minutes
max_waiting_time,45.0,minutes
min_waiting_time,0.0,minutes
track_utilization,0.78,ratio
average_queue_length,3.2,wagons
max_queue_length,12,wagons
simulation_start,2024-01-15T10:00:00,
simulation_end,2024-01-15T10:05:30,
```

**Verwendung:**
```python
import pandas as pd

df = pd.read_csv("results/summary.csv")
throughput = df[df['metric'] == 'throughput_per_hour']['value'].values[0]
```

---

### 2. results/wagons.csv

**Zweck:** Detaillierte Informationen zu jedem Wagen

**Format:**
```csv
wagon_id,train_id,track_id,arrival_time,retrofit_start_time,retrofit_end_time,waiting_time,retrofit_duration
WAGON0001_00,TRAIN0001,TRACK01,60.0,60.0,90.0,0.0,30.0
WAGON0001_01,TRAIN0001,TRACK02,60.0,65.0,110.0,5.0,45.0
WAGON0001_02,TRAIN0001,TRACK01,60.0,90.0,120.0,30.0,30.0
```

**Spalten:**
- `wagon_id`: Eindeutige Wagen-ID
- `train_id`: Zugehöriger Zug
- `track_id`: Verwendetes Gleis
- `arrival_time`: Ankunftszeit in Minuten
- `retrofit_start_time`: Start Umrüstung in Minuten
- `retrofit_end_time`: Ende Umrüstung in Minuten
- `waiting_time`: Wartezeit in Minuten
- `retrofit_duration`: Umrüstdauer in Minuten

---

### 3. results/track_metrics.csv

**Zweck:** Metriken pro Werkstattgleis

**Format:**
```csv
track_id,wagons_processed,utilization,average_retrofit_time,idle_time_hours
TRACK01,28,0.82,30.5,1.44
TRACK02,22,0.75,45.2,2.00
TRACK03,25,0.78,35.1,1.76
```

**Spalten:**
- `track_id`: Gleis-ID
- `wagons_processed`: Anzahl verarbeiteter Wagen
- `utilization`: Auslastung (0-1)
- `average_retrofit_time`: Durchschnittliche Umrüstzeit in Minuten
- `idle_time_hours`: Leerlaufzeit in Stunden

---

### 4. results/events.csv

**Zweck:** Chronologisches Event-Log

**Format:**
```csv
timestamp,event_type,wagon_id,train_id,track_id,data
60.0,train_arrival,,TRAIN0001,,"{""wagon_count"": 10}"
60.0,retrofit_start,WAGON0001_00,TRAIN0001,TRACK01,"{""waiting_time"": 0.0}"
90.0,retrofit_complete,WAGON0001_00,TRAIN0001,TRACK01,"{""retrofit_duration"": 30.0}"
60.0,track_occupied,,,TRACK01,"{""current_occupancy"": 1, ""capacity"": 5}"
90.0,track_free,,,TRACK01,"{""current_occupancy"": 0, ""capacity"": 5}"
```

**Event Types:**
- `train_arrival`: Zug kommt an
- `wagon_queued`: Wagen in Warteschlange
- `retrofit_start`: Umrüstung beginnt
- `retrofit_complete`: Umrüstung abgeschlossen
- `track_occupied`: Gleis wird belegt
- `track_free`: Gleis wird frei

---

### 5. results/results.json

**Zweck:** Vollständige Ergebnisse in strukturiertem Format

**Format:**
```json
{
  "scenario_id": "scenario_001",
  "duration_hours": 8.0,
  "kpis": {
    "total_wagons_processed": 75,
    "throughput_per_hour": 9.375,
    "average_waiting_time": 12.5,
    "max_waiting_time": 45.0,
    "min_waiting_time": 0.0,
    "track_utilization": 0.78,
    "average_queue_length": 3.2,
    "max_queue_length": 12
  },
  "track_metrics": [
    {
      "track_id": "TRACK01",
      "wagons_processed": 28,
      "utilization": 0.82,
      "average_retrofit_time": 30.5,
      "idle_time_hours": 1.44
    }
  ],
  "metadata": {
    "simulation_start": "2024-10-15T10:00:00",
    "simulation_end": "2024-10-15T10:05:30",
    "config_file": "config/examples/small_scenario/scenario.json",
    "random_seed": 42
  }
}
```

---

### 6. results/charts/

**Zweck:** Visualisierungen als PNG-Dateien

**Dateien:**
- `throughput.png`: Durchsatz über Zeit (Line Chart)
- `waiting_times.png`: Wartezeit-Verteilung (Histogram)
- `utilization.png`: Gleisauslastung (Bar Chart)
- `queue_length.png`: Warteschlangenlänge über Zeit (Area Chart)

**Spezifikationen:**
- Format: PNG
- Auflösung: 1920x1080 (Full HD)
- DPI: 150
- Schriftgröße: 12pt

---

## Verzeichnisstruktur

### Input
```
config/
└── examples/
    ├── small_scenario/
    │   ├── scenario.json
    │   └── README.md
    ├── medium_scenario/
    │   ├── scenario.json
    │   └── README.md
    └── large_scenario/
        ├── scenario.json
        └── README.md
```

### Output
```
results/
├── summary.csv
├── wagons.csv
├── track_metrics.csv
├── events.csv
├── results.json
└── charts/
    ├── throughput.png
    ├── waiting_times.png
    ├── utilization.png
    └── queue_length.png
```

---

## Beispiel-Szenarien

### Small Scenario (20 Wagen)
```json
{
  "scenario_id": "small_scenario",
  "start_date": "2024-10-15",
  "end_date": "2024-10-15",
  "random_seed": 42,
  "workshop": {
    "tracks": [
      {"id": "TRACK01", "capacity": 3, "retrofit_time_min": 30}
    ]
  },
  "train_schedule_file": "train_schedule_small.csv"
}
```

**train_schedule_small.csv:**
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,08:00,W001_01,15.5,true,true
TRAIN001,2024-01-15,08:00,W001_02,15.5,false,true
TRAIN002,2024-01-15,10:00,W002_01,18.0,true,true
TRAIN002,2024-01-15,10:00,W002_02,18.0,true,false
```

**Erwartete Ergebnisse:**
- Total Wagons: 4 (3 need retrofit)
- Throughput: ~2 wagons/hour
- Avg Waiting Time: ~5 minutes

---

### Medium Scenario (80 Wagen)
```json
{
  "scenario_id": "medium_scenario",
  "start_date": "2024-10-15",
  "end_date": "2024-10-15",
  "random_seed": 42,
  "workshop": {
    "tracks": [
      {"id": "TRACK01", "capacity": 5, "retrofit_time_min": 30},
      {"id": "TRACK02", "capacity": 3, "retrofit_time_min": 45}
    ]
  },
  "train_schedule_file": "train_schedule_medium.csv"
}
```

**train_schedule_medium.csv:** (Auszug)
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-10-15,08:00,W001_01,15.5,true,true
TRAIN001,2025-10-15,08:00,W001_02,15.5,false,true
...
TRAIN008,2025-10-15,15:00,W008_10,15.5,true,true
```

**Erwartete Ergebnisse:**
- Total Wagons: ~80
- Throughput: ~10 wagons/hour
- Avg Waiting Time: ~15 minutes

---

### Large Scenario (720 Wagen)
```json
{
  "scenario_id": "large_scenario",
  "start_date": "2025-10-15",
  "end_date": "2025-10-16",
  "random_seed": 42,
  "workshop": {
    "tracks": [
      {"id": "TRACK01", "capacity": 8, "retrofit_time_min": 25},
      {"id": "TRACK02", "capacity": 6, "retrofit_time_min": 30},
      {"id": "TRACK03", "capacity": 5, "retrofit_time_min": 35},
      {"id": "TRACK04", "capacity": 4, "retrofit_time_min": 40}
    ]
  },
  "train_schedule_file": "train_schedule_large.csv"
}
```

**train_schedule_large.csv:** (Auszug - 48 Züge mit je 15 Wagen)
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-10-15,00:30,W001_01,15.5,true,true
TRAIN001,2025-10-15,00:30,W001_02,15.5,false,true
...
TRAIN048,2025-10-16,23:30,W048_15,15.5,true,true
```

**Erwartete Ergebnisse:**
- Total Wagons: ~720
- Throughput: ~30 wagons/hour
- Avg Waiting Time: ~20 minutes

---

## Validierung

### Input Validation

```python
from pydantic import BaseModel, Field, validator
import json

class ScenarioConfig(BaseModel):
    scenario_id: str
    start_date: date
    end_date: date
    random_seed: int = Field(ge=0)
    workshop: WorkshopConfig
    train_schedule_file: str

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date muss nach start_date liegen')
        if 'start_date' in values and (v - values['start_date']).days > 7:
            raise ValueError('Simulation länger als 1 Woche nicht sinnvoll')
        return v

# Laden und Validieren
with open("scenario.json") as f:
    data = json.load(f)

try:
    config = ScenarioConfig(**data)
    print("✅ Configuration valid")
except ValidationError as e:
    print(f"❌ Configuration invalid: {e}")
```

### Output Validation

```python
def validate_output_files(output_path: Path):
    """Prüfe ob alle Output-Dateien existieren"""
    required_files = [
        "summary.csv",
        "wagons.csv",
        "track_metrics.csv",
        "events.csv",
        "results.json"
    ]

    for file in required_files:
        if not (output_path / file).exists():
            raise FileNotFoundError(f"Missing output file: {file}")

    # Prüfe Charts
    chart_path = output_path / "charts"
    if not chart_path.exists():
        raise FileNotFoundError("Missing charts directory")

    required_charts = [
        "throughput.png",
        "waiting_times.png",
        "utilization.png"
    ]

    for chart in required_charts:
        if not (chart_path / chart).exists():
            raise FileNotFoundError(f"Missing chart: {chart}")
```

---

## Error Handling

### Invalid Input
```python
# Beispiel: Ungültige Track ID
{
  "id": "INVALID",  # ❌ Muss TRACK\d{2} sein
  "capacity": 5,
  "retrofit_time_min": 30
}

# Fehler:
# ValidationError: 1 validation error for WorkshopTrackConfig
# id
#   string does not match regex "^TRACK\\d{2}$"
```

### Missing Required Fields
```python
# Beispiel: Fehlende capacity
{
  "id": "TRACK01",
  "retrofit_time_min": 30
}

# Fehler:
# ValidationError: 1 validation error for WorkshopTrackConfig
# capacity
#   field required
```

### Out of Range Values
```python
# Beispiel: Capacity zu groß
{
  "id": "TRACK01",
  "capacity": 100,  # ❌ Max 20
  "retrofit_time_min": 30
}

# Fehler:
# ValidationError: 1 validation error for WorkshopTrackConfig
# capacity
#   ensure this value is less than or equal to 20
```

---

## Migration Path (Post-MVP)

### Vollversion: Erweiterte Formate

**Zusätzliche Input-Dateien:**
- `wagon_types.csv`: Definition verschiedener Wagentypen
- `worker_shifts.csv`: Schichtpläne für Arbeiter
- `maintenance_schedule.csv`: Wartungsfenster

**Zusätzliche Output-Dateien:**
- `worker_metrics.csv`: Metriken pro Arbeiter
- `bottleneck_analysis.json`: Engpass-Analyse
- `optimization_suggestions.json`: Verbesserungsvorschläge

---

**Navigation:** [← Technology Stack](06-mvp-technology-stack.md) | [Testing Strategy →](08-mvp-testing-strategy.md)
