# Medium Scenario Example

> 📖 **Main Documentation:** [PopUp-Sim Backend README](../../../popupsim/backend/README.md)

This directory contains a medium-sized simulation scenario for PopUp-Sim, designed for testing and demonstration purposes.

## Scenario Overview

- **Scenario ID:** `medium`
- **Duration:** January 15-17, 2025 (2 days)
- **Trains:** 4 inbound trains, each with 40 wagons (160 wagons total)
- **Workshop:** 2 workshop tracks with capacity 5 each
- **Purpose:** Illustrates a medium-scale DAC migration case with moderate operational complexity

## Required Files

This scenario uses external file references for modular configuration:

### 1. `scenario.json` (Main Configuration)
Defines the scenario parameters and references to other data files:
```json
{
  "scenario_id": "medium",
  "start_date": "2025-01-15",
  "end_date": "2025-01-17",
  "random_seed": 42,
  "train_schedule_file": "train_schedule.csv",
  "routes_file": "routes.csv",
  "workshop_tracks_file": "workshop_tracks.csv"
}
```
#### scenario.json Fields
- `scenario_id`: Unique identifier for the scenario
- `start_date` / `end_date`: Simulation time window (YYYY-MM-DD)
- `random_seed`: For reproducible simulations (optional)
- `train_schedule_file`: Reference to train schedule CSV
- `routes_file`: Reference to routes CSV (optional, defaults to `routes.csv`)
- `workshop_tracks_file`: Reference to workshop tracks CSV (optional, defaults to `workshop_tracks.csv`)


### 2. `train_schedule.csv` (Train Arrivals)
Specifies arrival times and wagon composition for all trains:
- **Columns:** `train_id`, `arrival_date`, `arrival_time`, `wagon_id`, `length`, `is_loaded`, `needs_retrofit`
- **Total Wagons:** 160 wagons across 4 trains

#### train_schedule.csv Format
```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-01-15,08:00,WAGON001_01,15.5,true,true
```

### 3. `workshop_tracks.csv` (Workshop Configuration)
Defines workshop track layout and processing capabilities:
- **Columns:** `track_id`, `function`, `capacity`, `retrofit_time_min`, `current_wagons`
- **Tracks:** 2 tracks (TRACK01, TRACK02) with capacity 5 each

#### workshop_tracks.csv Format
```csv
track_id,function,capacity,retrofit_time_min,current_wagons
TRACK01,werkstattgleis,5,30,
```

### 4. `routes.csv` (Route Network)
Describes the route network between tracks:
- **Columns:** `route_id`, `from_track`, `to_track`, `track_sequence`, `distance_m`, `time_min`
- **Purpose:** Defines movement paths and travel times between locations

#### routes.csv Format
```csv
route_id;from_track;to_track;track_sequence;distance_m;time_min
ROUTE01;TRACK_A;TRACK_B;TRACK_A,TRACK_B;1000;60
```

## Usage

Run this scenario using the PopUp-Sim backend:

```bash
# From project root
python popupsim/backend/src/main.py --scenarioPath Data/examples/medium_scenario/scenario.json --outputPath Data/results/medium_scenario
```

## Notes

- All CSV files must be in the same directory as `scenario.json` with relative file references
- This scenario is intended for medium-scale tests and as a template for creating more complex cases
- The modular file structure allows easy modification of individual components

---

**Need help?** See the [main backend documentation](../../../popupsim/backend/README.md) for setup and development instructions.
