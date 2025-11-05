# 7. MVP File Formats

## Overview

**Note:** See actual implementation in `popupsim/backend/src/configuration/` for Pydantic models.

This document defines all input and output file formats for the MVP.

## Input Files

### 1. scenario.json

**Purpose**: Main configuration for simulation scenario

**Example**:
```json
{
  "scenario_id": "demo_scenario",
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "function": "WERKSTATTGLEIS",
        "capacity": 5,
        "retrofit_time_min": 30
      }
    ]
  },
  "train_schedule_file": "train_schedule.csv"
}
```

**Validation**: Pydantic ScenarioConfig model

### 2. workshop_tracks.csv

**Purpose**: Tabular definition of workshop tracks

**Format**:
```csv
track_id,function,capacity,retrofit_time_min
TRACK01,WERKSTATTGLEIS,5,30
TRACK02,WERKSTATTGLEIS,3,45
TRACK03,WERKSTATTZUFUEHRUNG,2,0
```

**Track Functions**:
- `werkstattgleis`: Main retrofit tracks where DAC installation happens
- `sammelgleis`: Collection tracks for grouping trains
- `parkgleis`: Parking tracks for temporary storage
- `werkstattzufuehrung`: Feeder tracks leading to workshop
- `werkstattabfuehrung`: Exit tracks leaving workshop
- `bahnhofskopf`: Station head tracks

### 3. train_schedule.csv

**Purpose**: Explicit definition of all train arrivals

**Format**:
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-01-01,08:00,WAGON001_01,15.5,true,true
TRAIN001,2025-01-01,08:00,WAGON001_02,15.5,false,true
TRAIN002,2025-01-01,10:30,WAGON002_01,18.0,true,true
```

**Columns**:
- `train_id`: Unique train identifier
- `arrival_date`: Date (YYYY-MM-DD)
- `arrival_time`: Time (HH:MM)
- `wagon_id`: Unique wagon identifier
- `length`: Wagon length in meters
- `is_loaded`: Boolean (true/false)
- `needs_retrofit`: Boolean (true/false)

### 4. routes.csv (Optional)

**Purpose**: Route definitions for shunting locomotives

**Format**:
```csv
route_id,from_function,to_function,track_sequence,distance_m,time_min
ROUTE01,WERKSTATTZUFUEHRUNG,WERKSTATTGLEIS,"TRACK03,TRACK01",120,2
```

## Output Files

### 1. results/summary.csv

**Purpose**: KPI summary

**Format**:
```csv
metric,value,unit
scenario_id,demo_scenario,
duration_hours,8.0,hours
total_wagons_processed,75,wagons
throughput_per_hour,9.375,wagons/hour
average_waiting_time,12.5,minutes
track_utilization,0.78,ratio
```

### 2. results/wagons.csv

**Purpose**: Detailed wagon information

**Format**:
```csv
wagon_id,train_id,track_id,arrival_time,retrofit_start_time,retrofit_end_time,waiting_time,retrofit_duration
WAGON001_01,TRAIN001,TRACK01,60.0,60.0,90.0,0.0,30.0
WAGON001_02,TRAIN001,TRACK02,60.0,65.0,110.0,5.0,45.0
```

### 3. results/track_metrics.csv

**Purpose**: Metrics per workshop track

**Format**:
```csv
track_id,wagons_processed,utilization,average_retrofit_time,idle_time_hours
TRACK01,28,0.82,30.5,1.44
TRACK02,22,0.75,45.2,2.00
```

### 4. results/events.csv

**Purpose**: Chronological event log

**Format**:
```csv
timestamp,event_type,wagon_id,train_id,track_id,data
60.0,train_arrival,,TRAIN001,,"{""wagon_count"": 10}"
60.0,retrofit_start,WAGON001_01,TRAIN001,TRACK01,"{""waiting_time"": 0.0}"
90.0,retrofit_complete,WAGON001_01,TRAIN001,TRACK01,"{""retrofit_duration"": 30.0}"
```

**Event Types**:
- `train_arrival`: Train arrives
- `wagon_queued`: Wagon enters queue
- `retrofit_start`: Retrofit begins
- `retrofit_complete`: Retrofit completed
- `track_occupied`: Track becomes occupied
- `track_free`: Track becomes free

### 5. results/results.json

**Purpose**: Complete results in structured format

**Format**:
```json
{
  "scenario_id": "demo_scenario",
  "duration_hours": 8.0,
  "kpis": {
    "total_wagons_processed": 75,
    "throughput_per_hour": 9.375,
    "average_waiting_time": 12.5,
    "track_utilization": 0.78
  },
  "metadata": {
    "simulation_start": "2025-01-01T10:00:00",
    "simulation_end": "2025-01-01T10:05:30"
  }
}
```

### 6. results/charts/

**Purpose**: Visualizations as PNG files

**Files**:
- `throughput.png`: Throughput over time (line chart)
- `waiting_times.png`: Waiting time distribution (histogram)
- `utilization.png`: Track utilization (bar chart)

**Specifications**:
- Format: PNG
- Resolution: 1920x1080
- DPI: 150

## Directory Structure

### Input
```
config/
└── examples/
    ├── small_scenario/
    │   ├── scenario.json
    │   ├── train_schedule.csv
    │   └── README.md
    └── medium_scenario/
        ├── scenario.json
        ├── train_schedule.csv
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
    └── utilization.png
```

## Validation

### Input Validation

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date

class ScenarioConfig(BaseModel):
    scenario_id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$')
    start_date: date
    end_date: date
    workshop: Workshop
    train_schedule_file: str

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
```

### Output Validation

```python
from pathlib import Path

def validate_output_files(output_path: Path) -> None:
    """Check if all output files exist"""
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

    # Check charts
    chart_path = output_path / "charts"
    if not chart_path.exists():
        raise FileNotFoundError("Missing charts directory")
```

## Example Scenarios

### Small Scenario (20 wagons)
- 1 track, capacity 3
- 4 trains, 5 wagons each
- Expected throughput: ~2 wagons/hour

### Medium Scenario (80 wagons)
- 2 tracks, capacity 5 and 3
- 8 trains, 10 wagons each
- Expected throughput: ~10 wagons/hour

### Large Scenario (720 wagons)
- 4 tracks, capacity 8, 6, 5, 4
- 48 trains, 15 wagons each
- Expected throughput: ~30 wagons/hour
