# Example Scenarios

## Overview

PopUpSim includes real example scenarios in `Data/examples/`. These scenarios demonstrate different configurations and use cases.

**Location:** `Data/examples/`

---

## Available Scenarios

### Small Scenarios

#### two_trains
- **Purpose:** Minimal test scenario
- **Configuration:** 2 trains, basic workshop setup
- **Files:** JSON format (scenario.json, tracks.json, workshops.json, trains.csv)
- **Use case:** Quick functionality testing

#### seven_wagons_two_locos
- **Purpose:** Test locomotive allocation
- **Configuration:** 7 wagons, 2 locomotives
- **Files:** JSON format
- **Use case:** Resource management testing

#### seven_wagons_two_workshops
- **Purpose:** Test workshop distribution
- **Configuration:** 7 wagons, 2 workshops
- **Files:** JSON format
- **Use case:** Workshop scheduling testing

### Medium Scenarios

#### medium_scenario
- **Purpose:** Standard workshop simulation
- **Configuration:** Multiple trains, realistic workshop
- **Files:** JSON + CSV (scenario.json, train_schedule.csv, routes.csv, workshop_tracks.csv)
- **Use case:** Capacity assessment
- **README:** See `Data/examples/medium_scenario/README.md`

#### ten_trains_two_days
- **Purpose:** Multi-day simulation
- **Configuration:** 10 trains over 2 days
- **Files:** JSON format
- **Use case:** Throughput estimation

### Large Scenarios

#### large_scenario
- **Purpose:** High-volume testing
- **Configuration:** Many trains, complex workshop
- **Files:** JSON + CSV
- **Use case:** Stress testing, bottleneck identification
- **README:** See `Data/examples/large_scenario/README.md`

### Special Test Scenarios

#### retrofit_overflow
- **Purpose:** Test retrofit track overflow handling
- **Configuration:** Designed to exceed retrofit track capacity
- **Use case:** Capacity limit testing

#### ten_trains_two_days_collection_track_overflow
- **Purpose:** Test collection track overflow
- **Configuration:** Designed to exceed collection track capacity
- **Use case:** Queue management testing

#### csv_scenario
- **Purpose:** Demonstrate CSV-based configuration
- **Configuration:** All configuration in CSV files
- **Files:** CSV format (scenario.csv, trains.csv, wagons.csv, tracks.csv, workshops.csv, locomotives.csv, routes.csv)
- **Use case:** CSV import testing
- **README:** See `Data/examples/csv_scenario/README.md`

---

## Running Examples

### Basic Usage

```bash
# Run small scenario
uv run python popupsim/backend/src/main.py --config Data/examples/two_trains/

# Run medium scenario
uv run python popupsim/backend/src/main.py --config Data/examples/medium_scenario/

# Run large scenario
uv run python popupsim/backend/src/main.py --config Data/examples/large_scenario/
```

### With Custom Output

```bash
# Specify output directory
uv run python popupsim/backend/src/main.py \
  --config Data/examples/medium_scenario/ \
  --output results/medium_test/
```

---

## Scenario Structure

### JSON-based Scenarios

Typical structure:
```
scenario_name/
├── scenario.json          # Main configuration
├── tracks.json            # Track definitions
├── workshops.json         # Workshop configuration
├── locomotives.json       # Locomotive fleet
├── routes.json            # Route definitions
├── topology.json          # Network topology
├── process_times.json     # Timing parameters
└── trains.csv             # Train schedule
```

### CSV-based Scenarios

Alternative structure:
```
csv_scenario/
├── scenario.csv           # Main configuration
├── tracks.csv             # Track definitions
├── workshops.csv          # Workshop configuration
├── locomotives.csv        # Locomotive fleet
├── routes.csv             # Route definitions
├── trains.csv             # Train schedule
└── wagons.csv             # Wagon details
```

---

## Creating Custom Scenarios

### 1. Copy Existing Scenario

```bash
cp -r Data/examples/medium_scenario/ Data/examples/my_scenario/
```

### 2. Edit Configuration

Edit `scenario.json`:
```json
{
  "id": "my_scenario",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-02T00:00:00",
  "tracks_file": "tracks.json",
  "workshops_file": "workshops.json",
  "locomotives_file": "locomotives.json",
  "routes_file": "routes.json",
  "trains_file": "trains.csv"
}
```

### 3. Adjust Parameters

- **workshops.json**: Change retrofit_stations count
- **trains.csv**: Modify arrival times and wagon counts
- **tracks.json**: Adjust track capacities

### 4. Run Simulation

```bash
uv run python popupsim/backend/src/main.py --config Data/examples/my_scenario/
```

---

## Scenario Documentation

Each major scenario includes a README.md with:
- Scenario description
- Configuration details
- Expected behavior
- Known issues (if any)

**Example READMEs:**
- `Data/examples/small_scenario/README.md`
- `Data/examples/medium_scenario/README.md`
- `Data/examples/large_scenario/README.md`
- `Data/examples/csv_scenario/README.md`

---

## Testing Scenarios

All scenarios are used in automated tests:

```bash
# Run all scenario tests
uv run pytest popupsim/backend/tests/

# Run specific scenario test
uv run pytest popupsim/backend/tests/ -k "test_medium_scenario"
```

---

## Performance Benchmarks

Performance varies by scenario size:

| Scenario | Trains | Wagons | Typical Runtime |
|----------|--------|--------|-----------------|
| two_trains | 2 | ~7 | < 1 second |
| medium_scenario | ~4 | ~160 | < 5 seconds |
| large_scenario | ~10 | ~500 | < 30 seconds |

**Note:** Actual performance depends on hardware and configuration.

---

## Troubleshooting

### Scenario Won't Load

Check:
1. All referenced files exist
2. JSON syntax is valid
3. CSV files have correct headers
4. File paths in scenario.json are correct

### Validation Errors

Common issues:
- Missing required fields
- Invalid date formats
- Track references don't exist
- Workshop has no retrofit stations

### Simulation Errors

Check:
- Sufficient track capacity
- Locomotives available
- Routes defined between all tracks
- Process times are positive

---

## Further Reading

- **[File Formats](07-mvp-file-formats.md)** - Detailed format specifications
- **[Configuration Validation](configuration-validation.md)** - Validation rules
- **[Architecture](../architecture/README.md)** - System architecture

---
