# Small Scenario Example

This directory contains a minimal simulation scenario for PopUp-Sim, designed for testing and demonstration purposes.

## Scenario Description

- **Trains:** 2 inbound trains, each with 10 wagons
- **Workshop:** 1 workshop track
- **Purpose:** Illustrates a simple DAC migration case with limited operational complexity

## Files

- `scenario.json`: Defines the scenario configuration, including infrastructure, rolling stock, and simulation parameters.
- `train_schedule.csv`: Specifies the arrival times and composition of the two trains.
- `workshop_config.csv`: Details the workshop track layout and processing capabilities.

## Usage

To run this scenario, point the PopUp-Sim backend to this directory's data files. Example:

```sh
uv run python popupsim/backend/src/main.py --scenario Data/examples/small_scenario/
```

## File Details

- **scenario.json**
  Contains the main scenario configuration (infrastructure, trains, simulation settings).

- **train_schedule.csv**
  Lists each train's arrival time, train ID, and wagon composition.

- **workshop_config.csv**
  Describes the available workshop track(s) and their properties.

---

This scenario is intended for quick tests and as a template for creating more complex cases.
