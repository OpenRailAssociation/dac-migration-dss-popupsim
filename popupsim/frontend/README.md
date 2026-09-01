# PopUpSim Dashboard

## Overview

PopUpSim Dashboard is a visualization dashboard showing the scenario
configuration analysis, resource utilizations and bottleneck identification.

## Features

### 1. Scenario Configuration Tab ⚙️

Visualizes input scenario configuration before simulation:

- **Overview Cards**: Scenario ID, trains, wagons, workflow mode
- **Strategy Configuration**: All selection strategies and thresholds
- **Infrastructure Layout**: Schematic diagram of yard tracks with capacities
- **Resource Capacity**: Workshops, locomotives, process times
- **Train Schedule**: Arrival timeline histogram
- **Capacity Analysis**: Capacity vs demand with bottleneck identification

### 2. Overview Tab 📊

Simulation results summary:

- KPI cards (wagons, completion rate, duration)
- Workshop performance metrics
- Locomotive operations statistics

### 3. Bottleneck Analysis Tab 🚧

Timeline-based bottleneck identification:

- Per-track queue lengths over time
- Workshop bay utilization
- Locomotive usage
- Interactive timeline visualization

### 4. Animation Tab 🎬

Animated playback of a simulation run on a schematic yard:

- Wagons and locomotives move along their recorded routes over time
- Wagons are **blue** until retrofitted, then turn **green** (color-blind-safe Okabe-Ito palette);
  locomotives are distinct dark squares
- **Coupled consists**: locomotives are matched to the wagons they haul and the consist travels as
  one rigid, spaced train, with the locomotive always on the throat side (so it pulls on the way
  out and pushes on the way in, never overlapping its wagons)
- Three-zone layout (local yard · Mainline corridor · remote storage) when routes span the Mainline
- Wagons pack flush to the far end (away from the throat) as a **stack (LIFO)**, re-compacted every
  frame so there are never holes (a departing wagon makes the rest slide); adjacent wagons alternate
  fill shade plus a border so they stay countable
- Workshops drawn as labeled buildings showing their bay count; wagons always render inside the box
- **Live statistics** that update as the clock advances (above the layout):
  - wagons still to retrofit currently in the system
  - wagons retrofitted currently in the system, and the cumulative retrofitted total
  - cumulative rejected wagons
  - per-track capacity usage (Σ real wagon lengths ÷ real track length, Mainline excluded)
- Native Plotly play/pause + time slider (client-side, smooth scrubbing), with **⏮ / ⏭ buttons**
  underneath that step a single frame at a time — fully in-browser, staying in sync with play and
  the slider (the figure is embedded as HTML and loads Plotly from a CDN, so first paint needs
  internet)
- User-selectable resolution on a quadratic scale (**200 up to 10,000 frames**), animation length,
  and playback speed

## Running the Dashboard

### Option 1: Batch File (Windows)
```bash
run_dashboard.bat
```

### Option 2: Command Line
```bash
streamlit run popupsim/frontend/dashboard.py
```

### Option 3: Python
```python
import streamlit.web.cli as stcli
import sys

sys.argv = ["streamlit", "run", "popupsim/frontend/dashboard.py"]
sys.exit(stcli.main())
```

## Usage

1. Run simulation to generate output data
2. Launch dashboard V2
3. Enter output directory path (e.g., `output/test0`)
4. Navigate through tabs to analyze results

## Data Requirements

The dashboard expects the following structure:

```
output/
└── test0/
    ├── scenario/                    # Copied scenario configuration
    │   ├── scenario.json
    │   ├── topology.json
    │   ├── tracks.json
    │   ├── workshops.json
    │   ├── locomotive.json
    │   ├── process_times.json
    │   └── train_schedule.csv
    ├── summary_metrics.json         # Simulation results
    ├── wagon_journey.csv
    ├── timeline.csv                 # Bottleneck analysis data
    ├── track_capacity.csv
    ├── workshop_utilization.csv
    └── ...
```

## Extending the Dashboard

### Adding a New Tab

1. Create new tab module in `dashboard_components/`:
```python
# my_new_tab.py
def render_my_new_tab(data: dict) -> None:
    st.header('My New Analysis')
    # Your visualization code
```

2. Import and add to main dashboard:
```python
# dashboard_v2.py
from dashboard_v2_components.my_new_tab import render_my_new_tab

tabs = st.tabs(['...', '🆕 My New Tab'])
with tabs[X]:
    render_my_new_tab(data)
```

### Adding New Analysis

1. Extend `ScenarioAnalyzer` with new method:
```python
# scenario_analyzer.py
def get_my_analysis(self) -> dict:
    # Analysis logic
    return results
```

2. Use in tab component:
```python
analyzer = ScenarioAnalyzer(config)
results = analyzer.get_my_analysis()
# Visualize results
```

## License

Apache 2.0 (same as PopUpSim project)
