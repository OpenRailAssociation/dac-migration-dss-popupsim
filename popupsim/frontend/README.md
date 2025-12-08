# PopUpSim Streamlit Dashboard

Comprehensive web-based dashboard to visualize PopUpSim simulation results.

## Quick Start

1. **Install Streamlit**:
   ```bash
   uv pip install streamlit pillow pandas
   ```

2. **Run a simulation** to generate output files:
   ```bash
   uv run python popupsim/backend/src/main_new.py --scenario Data/examples/small_scenario --output output
   ```

3. **Start the dashboard**:
   ```bash
   streamlit run popupsim/frontend/streamlit_dashboard.py
   ```
   
   Or use the legacy simple dashboard:
   ```bash
   streamlit run popupsim/frontend/streamlit_app.py
   ```

4. **View results**: Browser opens automatically at `http://localhost:8501`

## Features

### Comprehensive Dashboard (streamlit_dashboard.py)

- **Overview Tab**: KPI cards, generated charts (KPI status, flow analysis, operational dashboard)
- **Wagon Flow Tab**: State distribution, event timeline with filtering
- **Workshop Tab**: Performance comparison, utilization charts, throughput analysis
- **Locomotive Tab**: Utilization breakdown, activity distribution charts
- **Track Capacity Tab**: Color-coded utilization grid, capacity charts
- **Bottlenecks Tab**: Bottleneck detection summary and detailed analysis
- **Event Log Tab**: Searchable and filterable event viewer
- **Process Log Tab**: Searchable and filterable process log viewer

### Legacy Dashboard (streamlit_app.py)

- **Overview Tab**: View generated charts
- **Charts Tab**: Timeline metrics visualization
- **Process Log Tab**: Search and filter process logs
- **Event Log Tab**: Search and filter event logs

## Dashboard Data Files

The comprehensive dashboard uses these files exported by `DashboardExporter`:

### Required Files (from analytics context)
- `comprehensive_metrics.json` - Complete metrics snapshot ✅
- `events.csv` - Temporal event stream ✅
- `process.log` - Resource state changes ✅
- `locomotive_utilization.csv` - Per-locomotive time breakdown ✅
- `workshop_metrics.csv` - Per-workshop performance ✅
- `bottlenecks.csv` - Detected bottlenecks ✅
- `track_capacity.csv` - Track capacity utilization ✅

### Optional Files (visualizations)
- `kpi_status.png` - KPI visualization
- `flow_analysis.png` - Flow analysis chart
- `operational_dashboard.png` - Operational dashboard
- `events.log` - Event log (legacy format)

## Architecture Integration

The dashboard integrates with the backend through:

1. **DashboardExporter** (`contexts/analytics/infrastructure/exporters/dashboard_exporter.py`)
   - Exports all required data files from analytics context
   - Called via `analytics_context.export_dashboard_data(output_dir)`

2. **AnalyticsContext** (`contexts/analytics/application/analytics_context.py`)
   - Collects metrics during simulation
   - Provides `export_dashboard_data()` method
   - Aggregates data from all bounded contexts

3. **Main CLI** (`main_new.py`)
   - Runs simulation
   - Calls `analytics.export_dashboard_data(output_path)`
   - Generates all dashboard files automatically

## Usage Tips

### Overview Tab
- View high-level KPIs and completion rates
- Check generated visualization charts
- Quick assessment of simulation success

### Wagon Flow Tab
- Analyze wagon state distribution
- Filter events by type to track specific operations
- Identify wagon processing patterns

### Workshop Tab
- Compare workshop performance metrics
- Identify underutilized or overutilized workshops
- Analyze throughput rates

### Locomotive Tab
- Review locomotive activity breakdown
- Identify idle time and utilization issues
- Compare locomotive efficiency

### Track Capacity Tab
- Monitor track utilization with color coding:
  - 🟢 Green: < 70% (healthy)
  - 🟡 Yellow: 70-85% (high)
  - 🔴 Red: > 85% (critical)
- Identify capacity bottlenecks

### Bottlenecks Tab
- Review detected bottlenecks by resource type
- Prioritize optimization efforts
- Understand threshold violations

### Event/Process Logs
- Search for specific wagons, trains, or resources
- Filter by event/process type
- Debug simulation behavior

## Future Enhancements

- [ ] Time-series charts with interactive timeline
- [ ] Wagon journey Gantt chart visualization
- [ ] Sankey diagram for wagon flow
- [ ] Track occupancy heatmap over time
- [ ] Compare multiple simulation runs side-by-side
- [ ] Export filtered data subsets
- [ ] Real-time simulation monitoring mode
