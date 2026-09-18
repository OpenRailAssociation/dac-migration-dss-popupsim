# 7. MVP File Formats

## Overview

A scenario is a directory of JSON files plus one CSV train schedule. The root
`scenario.json` points to the other files through a `references` map. The authoritative,
runnable examples live under `Data/examples/` (e.g. `ten_trains_two_days_baseline/`); the
snippets below are taken from there.

Field names are defined by the Pydantic input DTOs in
`contexts/configuration/application/dtos/` and the domain models in
`contexts/configuration/domain/models/`.

## JSON Format

### scenario.json

The root file. It carries the id/dates and selection strategies, and references the other
files by relative name via `references`:

```json
{
  "id": "test_scenario_01",
  "description": "DAC retrofit simulation with 2 locos, 2 collection tracks, 2 workshops with 2 bays",
  "version": "1.0.0",
  "start_date": "2025-12-01T00:00:00+00:00",
  "end_date": "2025-12-11T00:00:00+00:00",
  "collection_track_strategy": "first_available",
  "retrofit_selection_strategy": "least_occupied",
  "retrofitted_selection_strategy": "least_occupied",
  "workshop_selection_strategy": "least_occupied",
  "parking_selection_strategy": "least_occupied",
  "references": {
    "locomotives": "locomotive.json",
    "process_times": "process_times.json",
    "routes": "routes.json",
    "trains": "train_schedule.csv",
    "topology": "topology.json",
    "tracks": "tracks.json",
    "workshops": "workshops.json"
  }
}
```

Strategy fields accept `SelectionStrategy` values: `first_available`, `least_occupied`,
`round_robin`, `best_fit`, `random`. The scenario also supports additional optional fields
(parking thresholds, locomotive strategies, and a `task_priorities` map) — see `scenario.py`.

### topology.json

Defines the physical network: nodes and edges, where each edge has a length in meters:

```json
{
  "nodes": [1, 2],
  "edges": {
    "collection1": {"nodes": [1, 2], "length": 500.0},
    "track_19": {"nodes": [1, 2], "length": 169.0}
  }
}
```

### tracks.json

A `tracks` array. Each track has an `id`, optional `name`, the `edges` it occupies, and a
`type` (`collection`, `retrofit`, `retrofitted`, `parking`, `workshop`, `mainline`,
`rescource_parking`):

```json
{
  "tracks": [
    {"id": "collection1", "name": "Collection track", "edges": ["collection1"], "type": "collection"},
    {"id": "retrofit", "edges": ["retrofit"], "type": "retrofit"},
    {"id": "parking1", "name": "Parking track", "edges": ["parking1"], "type": "parking"}
  ]
}
```

### workshops.json

Optional `metadata` plus a `workshops` array. Each workshop has `id`, `name`,
`retrofit_stations` (number of bays), and the `track` it sits on:

```json
{
  "metadata": {"description": "Workshop configurations", "version": "1.0.0"},
  "workshops": [
    {"id": "WS_01", "name": "First workshop", "retrofit_stations": 2, "track": "track_WS1"}
  ]
}
```

### locomotive.json

Optional `metadata` plus a `locomotives` array. Each locomotive has `id`, `name`, and a
`home track`:

```json
{
  "metadata": {"description": "Locomotive configurations", "version": "1.0.0"},
  "locomotives": [
    {"id": "LOCO_01", "name": "Shunting loco", "home track": "track_19"}
  ]
}
```

### routes.json

A `routes` array. Each route has an `id`, a `duration` in minutes, and a `path` (ordered list
of edge/track ids the route traverses):

```json
{
  "routes": [
    {"id": "track_19_collection1", "duration": 60.0, "path": ["track_19", "Mainline", "collection1"]},
    {"id": "track_19_retrofit", "duration": 5.0, "path": ["track_19", "retrofit"]}
  ]
}
```

### process_times.json

Timing configuration (minutes) for operations, keyed by coupler type where relevant:

```json
{
  "wagon_retrofit_time": 60.0,
  "train_to_hump_delay": 0.0,
  "wagon_hump_interval": 0.0,
  "screw_coupling_time": 2.0,
  "screw_decoupling_time": 3.0,
  "dac_coupling_time": 0.5,
  "dac_decoupling_time": 0.5
}
```

## CSV Format

### train_schedule.csv

The train schedule has one row per wagon. The delimiter is auto-detected: if the header line
contains a semicolon the file is read as semicolon-delimited (as in the bundled examples),
otherwise comma-delimited. Arrival times are ISO 8601 timestamps (timezone-aware). Columns:

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T1;W0001;2025-12-01T06:00:00+00:00;15.9;False;True;collection
T1;W0002;2025-12-01T06:00:00+00:00;16.1;False;True;collection
T2;W0003;2025-12-01T08:00:00+00:00;20.4;False;True;collection
```

| Column | Description |
|--------|-------------|
| train_id | Identifier of the arriving train |
| wagon_id | Unique wagon identifier |
| arrival_time | ISO 8601 timestamp of arrival (timezone-aware) |
| length | Wagon length in meters |
| is_loaded | Whether the wagon is loaded (loaded wagons are rejected) |
| needs_retrofit | Whether the wagon needs DAC retrofit |
| Track | Arrival track type (e.g. `collection`) |

## Validation

All input files are parsed into Pydantic DTOs/models in the Configuration context and run
through the validation pipeline (see
[ADR-002](../architecture/decisions/ADR-002-4-layer-validation-framework.md)).

## Examples

Runnable examples are in the `Data/examples/` directory of the repository. The
[tutorial](../../tutorial/README.md) walks through each file using the
`ten_trains_two_days_baseline` scenario.

---
