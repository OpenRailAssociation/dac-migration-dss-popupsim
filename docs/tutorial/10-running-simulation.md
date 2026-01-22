# Chapter 10: Running Your Simulation

## Running PopUpSim

Now that you understand all configuration files, let's run the simulation and analyze results.

## Basic Execution

### Command Syntax

```bash
uv run python popupsim/backend/src/main.py --scenario <scenario_path> --output <output_path>
```

### Running ten_trains_two_days

```bash
cd dac-migration-dss-popupsim
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days/ --output output/tutorial/
```

**Parameters:**
- `--scenario`: Path to scenario directory containing configuration files
- `--output`: Path where results will be saved

## Viewing Results

### Using the Dashboard

PopUpSim includes a web-based dashboard for interactive result visualization.

**Start the dashboard (in a separate terminal):**

**Windows:**
```bash
run_dashboard.bat
```

**Linux/macOS:**
```bash
uv run streamlit run popupsim/frontend/streamlit_dashboard.py
```

The dashboard opens at http://localhost:8501

**Dashboard Tabs:**

1. **📊 Overview** - High-level KPIs and operational dashboard
   - Total wagons, retrofitted count, completion rate
   - Wagon flow visualization
   - Locomotive activity breakdown
   - Workshop bay utilization

2. **🚃 Wagon Flow** - Detailed wagon journey analysis
   - Gantt charts showing wagon movements over time
   - Status distribution (retrofitted, parked, rejected)
   - Track occupancy visualization
   - Individual wagon journey timelines

3. **🏭 Workshop Performance** - Workshop efficiency metrics
   - Utilization percentages per workshop
   - Throughput (wagons/hour)
   - Workshop comparison table

4. **🚂 Locomotive Operations** - Shunting resource analysis
   - Activity breakdown (moving, parking, coupling, decoupling)
   - Utilization percentages
   - Time distribution charts

5. **🛤️ Track Capacity** - Track usage analysis
   - Utilization per track (color-coded: green < 70%, yellow 70-85%, red > 85%)
   - Capacity charts

6. **❌ Rejected Wagons** - Analysis of wagons that couldn't be processed
   - Rejection reasons (loaded, no retrofit needed, track full)
   - Detailed rejection list

7. **🔍 Event Log** - Searchable simulation event viewer
   - Filter by event type
   - Search functionality

8. **📋 Process Log** - Detailed process execution log
   - Filter by process type
   - Search functionality

**Important:** Run the dashboard in a separate terminal window so you can continue running simulations while viewing results.

### Using Output Files

Alternatively, analyze results directly from the output files.

## Execution Process

### 1. Configuration Loading

PopUpSim loads and validates all configuration files:

```
Loading scenario: Data/examples/ten_trains_two_days/
├─ Reading scenario.json
├─ Loading topology.json
├─ Loading tracks.json
├─ Loading workshops.json
├─ Loading process_times.json
├─ Loading locomotive.json
├─ Loading routes.json
└─ Loading train_schedule.csv
```

**Validation checks:**
- File existence
- JSON/CSV syntax
- Required fields
- Data types
- Cross-references between files

### 2. Simulation Initialization

Creates simulation environment:

```
Initializing simulation...
├─ Creating 224 wagons
├─ Setting up 2 workshops (4 retrofit stations)
├─ Configuring 15 parking tracks
├─ Initializing 1 locomotive
└─ Building route network (33 routes)
```

### 3. Simulation Execution

Runs discrete event simulation:

```
Running simulation...
Simulation time: 2025-12-01 00:00:00 to 2025-12-20 00:00:00
├─ Processing train arrivals
├─ Managing wagon movements
├─ Executing retrofit operations
├─ Tracking resource utilization
└─ Collecting metrics
```

**Progress indicators:**
- Current simulation time
- Events processed
- Wagons completed

### 4. Results Generation

Creates output files and visualizations:

```
Generating results...
├─ Writing CSV reports
├─ Creating visualizations
└─ Saving summary statistics
```

## Output Files

### Directory Structure

```
output/tutorial/
├── metrics/
│   ├── wagon_metrics.csv
│   ├── workshop_metrics.csv
│   └── locomotive_metrics.csv
├── visualizations/
│   ├── throughput_over_time.png
│   ├── workshop_utilization.png
│   └── wagon_flow.png
└── summary.json
```

### Wagon Metrics (wagon_metrics.csv)

Detailed information for each wagon:

| Column | Description |
|--------|-------------|
| wagon_id | Unique wagon identifier |
| arrival_time | When wagon arrived |
| retrofit_start | When retrofit began |
| retrofit_end | When retrofit completed |
| departure_time | When wagon left system |
| total_time | Total time in system |
| waiting_time | Time spent waiting |
| retrofit_time | Time spent in retrofit |

**Use for:**
- Individual wagon analysis
- Identifying delays
- Calculating statistics

### Workshop Metrics (workshop_metrics.csv)

Workshop performance data:

| Column | Description |
|--------|-------------|
| workshop_id | Workshop identifier |
| total_wagons | Wagons processed |
| utilization | Percentage of time busy |
| avg_queue_length | Average wagons waiting |
| max_queue_length | Maximum wagons waiting |

**Use for:**
- Capacity analysis
- Bottleneck identification
- Utilization optimization

### Locomotive Metrics (locomotive_metrics.csv)

Locomotive performance data:

| Column | Description |
|--------|-------------|
| locomotive_id | Locomotive identifier |
| total_movements | Number of wagon movements |
| utilization | Percentage of time busy |
| total_distance | Total distance traveled |
| idle_time | Time spent idle |

**Use for:**
- Resource planning
- Utilization analysis
- Capacity requirements

### Summary Statistics (summary.json)

High-level simulation results:

```json
{
  "scenario_id": "test_scenario_01",
  "simulation_duration": "19 days",
  "total_wagons": 224,
  "wagons_retrofitted": 220,
  "avg_throughput": 11.6,
  "avg_wagon_time": 1234.5,
  "workshop_utilization": 0.78,
  "locomotive_utilization": 0.65
}
```

## Analyzing Results

### Key Performance Indicators

#### Throughput

**Wagons per day:**
```
throughput = wagons_retrofitted / simulation_days
```

**Target:** Depends on scenario requirements

**ten_trains_two_days expected:** ~110 wagons/day (220 wagons / 2 days)

#### Workshop Utilization

**Percentage of time workshops are busy:**
```
utilization = busy_time / total_time
```

**Interpretation:**
- < 60%: Under-utilized (excess capacity)
- 60-80%: Well-balanced
- 80-95%: High utilization (efficient)
- > 95%: Bottleneck (consider expansion)

#### Average Wagon Time

**Total time wagon spends in system:**
```
avg_time = sum(departure_time - arrival_time) / wagon_count
```

**Components:**
- Waiting time (queuing)
- Movement time (shunting)
- Retrofit time (workshop)

**Target:** Minimize while maintaining throughput

#### Locomotive Utilization

**Percentage of time locomotives are busy:**
```
utilization = (movement_time + coupling_time) / total_time
```

**Interpretation:**
- < 50%: Over-capacity
- 50-70%: Well-balanced
- 70-90%: High utilization
- > 90%: Bottleneck (add locomotives)

### Bottleneck Identification

#### Workshop Bottleneck

**Symptoms:**
- Workshop utilization > 90%
- Long wagon waiting times
- Growing retrofit queue
- Idle parking capacity

**Solutions:**
1. Add retrofit stations (workshops.json)
2. Add more workshops
3. Optimize workshop selection strategy

#### Locomotive Bottleneck

**Symptoms:**
- Locomotive utilization > 85%
- Long movement queues
- Idle workshops waiting for wagons
- Delayed wagon distributions

**Solutions:**
1. Optimize route durations (routes.json)
2. Reduce coupling/decoupling times (process_times.json)
3. Improve locomotive placement
4. **⚠️ Add more locomotives (locomotive.json) - EXPERIMENTAL, not fully tested**

#### Track Capacity Bottleneck

**Symptoms:**
- Parking tracks at capacity
- Collection tracks blocking
- Wagons waiting for track space

**Solutions:**
1. Add more parking tracks (topology.json, tracks.json)
2. Increase track lengths (topology.json)
3. Optimize track selection strategy
4. Improve wagon distribution

## Optimization Workflow

### 1. Baseline Run

Run with default configuration:

```bash
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days/ --output output/baseline/
```

**Analyze:**
- Identify bottlenecks
- Note utilization rates
- Record throughput

### 2. Targeted Improvements

Modify configuration based on bottlenecks:

**If workshop bottleneck:**
```json
// workshops.json
"retrofit_stations": 3  // Was 2
```

**If locomotive bottleneck:**
```json
// routes.json - optimize travel times
{"id": "track_19_collection1", "duration": 0.5, "path": ["track_19", "collection1"]}
```

**Note:** Adding locomotives is not recommended (experimental feature, not fully tested)

### 3. Comparison Run

Run with modifications:

```bash
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days/ --output output/improved/
```

**Compare:**
- Throughput change
- Utilization improvements
- Cost vs. benefit

### 4. Iteration

Repeat until targets met:
- Adjust parameters
- Run simulation
- Analyze results
- Refine configuration

## Common Scenarios

### Scenario 1: Increase Throughput

**Goal:** Process 300 wagons in 2 days (150/day)

**Approach:**
1. Calculate required capacity: 300 wagons × 60 min / 2880 min = 6.25 stations
2. Add workshop capacity (workshops.json): 3 workshops × 2 stations = 6 stations
3. Add parking tracks for increased volume
4. Optimize route durations if locomotive utilization is high
5. Run and verify throughput

### Scenario 2: Reduce Costs

**Goal:** Minimize resources while maintaining throughput

**Approach:**
1. Run baseline with current configuration
2. Identify over-utilized resources (utilization < 60%)
3. Reduce excess capacity
4. Verify throughput maintained
5. Calculate cost savings

### Scenario 3: Handle Peak Loads

**Goal:** Process burst of 100 wagons arriving simultaneously

**Approach:**
1. Modify train_schedule.csv with simultaneous arrivals
2. Increase collection track capacity
3. Add temporary parking capacity
4. Run simulation
5. Verify no blocking or excessive delays

## Troubleshooting

### Simulation Errors

#### "No route found"

**Error:** Cannot find route from track A to track B

**Solution:** Add missing route in routes.json:
```json
{"id": "A_to_B", "duration": 1.0, "path": ["A", "Mainline", "B"]}
```

#### "Track capacity exceeded"

**Error:** Too many wagons for track length

**Solution:** 
- Increase track length in topology.json
- Add more tracks
- Improve wagon distribution

#### "Invalid arrival time"

**Error:** Train arrival outside scenario timeframe

**Solution:** Adjust arrival_time in train_schedule.csv or extend scenario dates

### Performance Issues

#### Slow Simulation

**Causes:**
- Very large scenarios (> 1000 wagons)
- Complex route networks
- Long simulation duration

**Solutions:**
- Reduce simulation timeframe
- Simplify route network
- Use faster hardware

#### High Memory Usage

**Causes:**
- Many wagons
- Detailed metrics collection

**Solutions:**
- Process in batches
- Reduce metric granularity
- Increase available RAM

## Best Practices

### Configuration Management

1. **Version control:** Use git for configuration files
2. **Naming conventions:** Clear, consistent file and ID naming
3. **Documentation:** Comment complex configurations
4. **Backups:** Keep baseline configurations

### Experimentation

1. **One change at a time:** Isolate variable effects
2. **Document changes:** Track what was modified
3. **Compare results:** Use consistent output directories
4. **Validate results:** Sanity-check metrics

### Reporting

1. **Save all outputs:** Keep complete result sets
2. **Screenshot visualizations:** Document key findings
3. **Export metrics:** Use CSV for further analysis
4. **Summarize findings:** Create executive summaries

## Next Steps

### Further Learning

- Explore other example scenarios (demo, ten_trains_two_days)
- Read [Architecture Documentation](../mvp/architecture/README.md)
- Review [Development Guide](../mvp/development/README.md)

### Creating Your Own Scenarios

1. Copy an existing scenario as template
2. Modify configuration files for your use case
3. Start with small scale for testing
4. Gradually increase complexity
5. Validate results against expectations

### Contributing

- Share your scenarios with the community
- Report issues on GitHub
- Suggest improvements
- Contribute code enhancements

## Conclusion

You now understand how to:
- Configure all PopUpSim input files
- Run simulations with different parameters
- Analyze results and identify bottlenecks
- Optimize configurations for better performance

**Happy simulating!**

---

**Tutorial Complete**

Return to [Tutorial Home](README.md) for overview and navigation.
