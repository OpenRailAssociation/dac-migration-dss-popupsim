# Chapter 10: Running Your Simulation

## Running PopUpSim

Now that you understand all configuration files, let's run the simulation and analyze results.

## Basic Execution

### Command Syntax

```bash
uv run python popupsim/backend/src/main.py run --scenario <scenario_path> --output <output_path>
```

### Running ten_trains_two_days_baseline

```bash
cd dac-migration-dss-popupsim
uv run python popupsim/backend/src/main.py run --scenario Data/examples/ten_trains_two_days_baseline/ --output output/tutorial/
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
uv run streamlit run popupsim/frontend/dashboard.py
```

The dashboard opens at http://localhost:8501

**Dashboard Tabs:**

1. **📊 Overview** - High-level KPIs and operational summary
   - Total wagons, retrofitted count, completion rate
   - Per-workshop performance breakdown
   - Locomotive activity and workshop utilization

2. **⚙️ Scenario Config** - The input configuration for the loaded run
   - Trains, workshops, tracks, locomotives, and process times
   - Capacity vs. demand overview

3. **🚃 Wagons** - Wagon flow analysis
   - Final wagon status distribution (retrofitted, parked, rejected)
   - Location changes over the run
   - Individual wagon journeys

4. **🚂 Locomotives** - Shunting resource analysis
   - Activity breakdown (moving, parking, coupling, decoupling)
   - Utilization percentages and activity timeline

5. **🏭 Workshops** - Workshop performance analysis
   - Utilization per workshop
   - Throughput and utilization over time

6. **🛤️ Track Capacity** - Track usage analysis
   - Track configuration and utilization per track
   - Capacity charts

7. **🚧 Bottleneck Analysis** - Where the process is constrained
   - Process flow heatmap
   - Resource utilization overview

8. **🎬 Animation** - Animated playback of the run on a schematic yard

**Important:** Run the dashboard in a separate terminal window so you can continue running simulations while viewing results.

### Using Output Files

Alternatively, analyze results directly from the output files.

## Execution Process

### 1. Configuration Loading

PopUpSim loads and validates all configuration files:

```
Loading scenario: Data/examples/ten_trains_two_days_baseline/
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
└─ Building route network (49 routes)
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

Writes CSV/JSON output files (visualization happens later, in the dashboard):

```
Generating outputs...
├─ Writing event and journey CSVs
├─ Writing resource/state CSVs
└─ Writing summary_metrics.json
```

## Output Files

All output is written directly into the `--output` directory as CSV and JSON files
(there are no `metrics/` or `visualizations/` subfolders, and no PNG charts — charts are
rendered on demand by the dashboard). The input scenario is also copied into a `scenario/`
subfolder for reference.

### Directory Structure

```
output/tutorial/
├── scenario/                     # Copy of the input scenario files
├── summary_metrics.json          # Aggregated KPIs (see below)
├── wagon_journey.csv             # Per-wagon lifecycle events
├── rejected_wagons.csv           # Wagons that could not be processed
├── locomotive_movements.csv      # Locomotive movement events
├── locomotive_journey.csv        # Detailed locomotive activity (incl. coupling)
├── locomotive_time_breakdown.csv # Per-locomotive time split by activity
├── locomotive_utilization.csv    # Locomotive busy/available over time
├── workshop_metrics.csv          # Per-workshop retrofit summary
├── workshop_utilization.csv      # Workshop bay utilization over time
├── track_capacity.csv            # Track capacity/occupancy changes over time
├── timeline.csv                  # Per-minute snapshot (tracks, workshops, locos)
├── events.csv                    # All events in chronological order
├── resource_states.csv           # Dual-stream: resource state changes
├── resource_locations.csv        # Dual-stream: resource location changes
├── resource_processes.csv        # Dual-stream: process events
├── events.log                    # Human-readable event log
└── process.log                   # Detailed process execution log
```

> **Note:** Exact columns are defined by the exporter in
> `contexts/retrofit_workflow/infrastructure/exporters/`. The most useful files for manual
> analysis are described below.

### Wagon journey (wagon_journey.csv)

One row per wagon lifecycle event (arrival, on retrofit track, retrofit start/complete,
parked, rejected):

| Column | Description |
|--------|-------------|
| timestamp | Simulation time (minutes from start) |
| datetime | Wall-clock timestamp derived from the scenario start date |
| wagon_id | Wagon identifier |
| train_id | Arriving train identifier |
| event | Event type (`ARRIVED`, `ON_RETROFIT_TRACK`, `RETROFIT_STARTED`, `RETROFIT_COMPLETED`, `PARKED`, `REJECTED`) |
| track_id | Location at the time of the event |
| status | Wagon status |
| rejection_reason / rejection_description | Populated only for `REJECTED` events |

### Rejected wagons (rejected_wagons.csv)

Rows for wagons that could not be processed:

| Column | Description |
|--------|-------------|
| timestamp / datetime | When the wagon was rejected |
| wagon_id / train_id | Identifiers |
| rejection_type | `WAGON_LOADED`, `NO_RETROFIT_NEEDED`, or `TRACK_FULL` |
| detailed_reason | Longer explanation |
| track_id | Track involved, if applicable |

### Workshop metrics (workshop_metrics.csv)

Per-workshop summary:

| Column | Description |
|--------|-------------|
| workshop_id | Workshop identifier |
| completed_retrofits | Wagons retrofitted |
| total_retrofit_time | Total time spent retrofitting (minutes) |
| total_waiting_time | Total wagon waiting time (minutes) |
| throughput_per_hour | Retrofits per hour |
| utilization_percent | Percentage of time bays were busy |

### Summary metrics (summary_metrics.json)

Aggregated KPIs for the run. Example (values from the baseline scenario):

```json
{
  "trains_arrived": 10,
  "total_wagons": 224,
  "wagons_eligible": 220,
  "wagons_processable": 209,
  "wagons_arrived": 70,
  "wagons_parked": 70,
  "retrofits_completed": 70,
  "wagons_rejected": 154,
  "rejected_no_retrofit": 4,
  "rejected_loaded": 11,
  "rejected_track_full": 139,
  "completion_rate": 0.33,
  "throughput_rate_per_hour": 0.38,
  "workshop_utilization": 10.14,
  "simulation_duration_minutes": 14400.0
}
```

The file also contains nested `workshop_statistics`, `locomotive_statistics`, and
`locomotive_time_breakdown` objects, plus `event_counts`. The `run` command prints a
summary of these values to the console when the simulation finishes.

## Analyzing Results

### Key Performance Indicators

#### Throughput

**Wagons per day:**
```
throughput = wagons_retrofitted / simulation_days
```

**Target:** Depends on scenario requirements.

Note the difference between *demand* and *capacity*: the baseline receives 220 retrofit-eligible
wagons, but with 4 stations at 60 min each the workshops can only process ~4 wagons/hour. In the
baseline run the workshops are the bottleneck, so completed wagons are well below the arriving
demand — inspect `summary_metrics.json` (`completion_rate`, `throughput_rate_per_hour`) for the
actual figures.

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
4. **Add more locomotives (locomotive.json) - experimental, not fully tested**

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
uv run python popupsim/backend/src/main.py run --scenario Data/examples/ten_trains_two_days_baseline/ --output output/baseline/
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
uv run python popupsim/backend/src/main.py run --scenario Data/examples/ten_trains_two_days_baseline/ --output output/improved/
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

- Explore other example scenarios in `Data/examples/` (baseline plus variants var1–var6 and priority_dispatch)
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
