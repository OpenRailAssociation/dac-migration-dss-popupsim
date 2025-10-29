# Large Scenario Example

This directory contains a large-scale simulation scenario for PopUp-Sim, designed for testing and demonstration purposes.

## Scenario Description

- **Trains:** 10 inbound trains, each with 50 wagons
- **Workshop:** 2 workshop tracks
- **Purpose:** Illustrates a large-scale DAC migration case with high operational complexity

## Files

- `scenario.json`: Defines the scenario configuration, including infrastructure, rolling stock, and simulation parameters.
- `train_schedule.csv`: Specifies the arrival times and composition of the ten trains.
- `workshop_tracks.csv`: Details the workshop track layout and processing capabilities.

## Usage

To run this scenario, point the PopUp-Sim backend to this directory's data files. Example:

```sh
uv run python popupsim/backend/src/main.py --scenario Data/examples/large_scenario/
```

## File Details

- **scenario.json**
  Contains the main scenario configuration (infrastructure, trains, simulation settings).

- **train_schedule.csv**
  Lists each train's arrival time, train ID, and wagon composition (500 wagons total).

- **workshop_tracks.csv**
  Describes the available workshop tracks and their properties (2 tracks with capacity 6 each).

---

This scenario is intended for large-scale tests and performance evaluation.
