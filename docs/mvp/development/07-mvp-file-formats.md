# 7. MVP File Formats

## Overview

PopUpSim supports JSON and CSV configuration files. See actual examples in `Data/examples/`.

## JSON Format

### scenario.json

```json
{
  "id": "demo_scenario",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-02T00:00:00",
  "tracks_file": "tracks.json",
  "workshops_file": "workshops.json",
  "locomotives_file": "locomotives.json",
  "routes_file": "routes.json",
  "trains_file": "trains.csv",
  "process_times_file": "process_times.json"
}
```

### tracks.json

```json
[
  {
    "track_id": "T001",
    "track_type": "collection",
    "length": 200.0,
    "fill_factor": 0.75
  }
]
```

### workshops.json

```json
[
  {
    "workshop_id": "W001",
    "track_id": "T002",
    "retrofit_stations": 3,
    "name": "Main Workshop"
  }
]
```

### locomotives.json

```json
[
  {
    "locomotive_id": "L001",
    "status": "available"
  }
]
```

### routes.json

```json
[
  {
    "route_id": "R001",
    "from_track_id": "T001",
    "to_track_id": "T002",
    "duration": 5.0
  }
]
```

### process_times.json

```json
{
  "coupling_time": 2.0,
  "decoupling_time": 2.0,
  "retrofit_time_per_wagon": 30.0,
  "train_preparation_time": 5.0
}
```

## CSV Format

### trains.csv

```csv
train_id,arrival_time,wagon_id,length,needs_retrofit
T001,60.0,W001,15.5,true
T001,60.0,W002,15.5,true
T002,120.0,W003,18.0,true
```

## Validation

All files are validated by Pydantic models. See [configuration-validation.md](configuration-validation.md) for details.

## Examples

Real examples available in:
- `Data/examples/two_trains/` - JSON format
- `Data/examples/medium_scenario/` - JSON + CSV
- `Data/examples/csv_scenario/` - CSV format

See [examples.md](examples.md) for complete list.

---
