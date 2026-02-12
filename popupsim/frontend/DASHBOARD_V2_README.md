# PopUpSim Dashboard V2

## Overview

Dashboard V2 is a clean, modular rewrite of the PopUpSim visualization dashboard with enhanced scenario configuration analysis and bottleneck identification.

## Architecture

The dashboard follows SOLID principles with a modular component-based architecture:

```
dashboard_v2.py                 # Main application entry point
dashboard_v2_components/
├── __init__.py                 # Package initialization
├── data_loader.py              # Data loading (SRP)
├── scenario_analyzer.py        # Scenario analysis logic (SRP)
├── scenario_tab.py             # Scenario configuration visualization
├── overview_tab.py             # Simulation results overview
└── bottleneck_tab.py           # Bottleneck analysis
```

### Design Principles

- **Single Responsibility Principle (SRP)**: Each module has one clear purpose
- **Separation of Concerns**: Data loading, analysis, and visualization are separate
- **Modularity**: Easy to add new tabs or analysis components
- **Clean Code**: Type hints, docstrings, minimal complexity

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

## Running the Dashboard

### Option 1: Batch File (Windows)
```bash
run_dashboard_v2.bat
```

### Option 2: Command Line
```bash
streamlit run popupsim/frontend/dashboard_v2.py
```

### Option 3: Python
```python
import streamlit.web.cli as stcli
import sys

sys.argv = ["streamlit", "run", "popupsim/frontend/dashboard_v2.py"]
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

1. Create new tab module in `dashboard_v2_components/`:
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

## Comparison with Dashboard V1

| Feature | V1 | V2 |
|---------|----|----|
| Architecture | Monolithic | Modular (SOLID) |
| Scenario Config | ❌ | ✅ |
| Bottleneck Analysis | Limited | Enhanced |
| Code Organization | Single file | Component-based |
| Extensibility | Difficult | Easy |
| Type Hints | Partial | Complete |

## Future Enhancements

- [ ] Wagon flow Gantt charts
- [ ] Workshop utilization heatmap
- [ ] Locomotive movement timeline
- [ ] Scenario comparison (side-by-side)
- [ ] PDF export functionality
- [ ] Interactive track diagram (clickable)
- [ ] Real-time simulation monitoring

## Dependencies

- streamlit
- pandas
- matplotlib
- (all standard PopUpSim dependencies)

## License

Apache 2.0 (same as PopUpSim project)
