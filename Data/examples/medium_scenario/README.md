# Medium Scenario Example

This directory contains a medium-sized simulation scenario for PopUp-Sim, designed for testing and demonstration purposes.

## Scenario Description

- **Trains:** 4 inbound trains, each with 40 wagons
- **Workshop:** 2 workshop tracks
- **Purpose:** Illustrates a medium-scale DAC migration case with moderate operational complexity

## Files

- `scenario.json`: Defines the scenario configuration, including infrastructure, rolling stock, and simulation parameters.
- `train_schedule.csv`: Specifies the arrival times and composition of the four trains.
- `workshop_tracks.csv`: Details the workshop track layout and processing capabilities.

## Usage

To run this scenario, point the PopUp-Sim backend to this directory's data files. Example:

```sh
uv run python popupsim/backend/src/main.py --scenario Data/examples/medium_scenario/
```

## File Details

- **scenario.json**
  Contains the main scenario configuration (infrastructure, trains, simulation settings).

- **train_schedule.csv**
  Lists each train's arrival time, train ID, and wagon composition (160 wagons total).

- **workshop_tracks.csv**
  Describes the available workshop tracks and their properties (2 tracks with capacity 5 each).

---

This scenario is intended for medium-scale tests and as a template for creating more complex cases.
