# Chapter 9: Train Schedule Configuration

## File: train_schedule.csv

The train_schedule.csv file defines when trains arrive, which wagons they contain, and wagon properties. This is the primary input for simulation workload.

## File Format

CSV file with semicolon (`;`) delimiter:

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T1;W0001;2025-12-01T06:00:00+00:00;15.9;False;True;collection
T1;W0002;2025-12-01T06:00:00+00:00;16.1;False;True;collection
T2;W0007;2025-12-01T10:48:00+00:00;18.8;False;True;collection
```

## Column Definitions

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `train_id` | string | Yes | Train identifier (groups wagons) |
| `wagon_id` | string | Yes | Unique wagon identifier |
| `arrival_time` | ISO 8601 datetime | Yes | When train arrives (UTC) |
| `length` | float | Yes | Wagon length in meters |
| `is_loaded` | boolean | Yes | Whether wagon carries cargo |
| `needs_retrofit` | boolean | Yes | Whether wagon requires DAC retrofit |
| `Track` | string | Yes | Track type for arrival (typically "collection") |

## Parameters Explained

### train_id

Identifier grouping wagons into trains:

```csv
train_id
T1
T1
T1
T2
T2
```

**Characteristics:**
- All wagons with same train_id arrive together
- Wagons are processed as a group initially
- Train_id must be unique per arrival time

**Naming Convention:**
- `T1`, `T2`, `T3`, ... for sequential numbering
- `TRAIN_001`, `TRAIN_002` for formal naming
- `NORTH_01`, `SOUTH_01` for location-based naming

**In ten_trains_two_days:** T1 through T10 (10 trains)

### wagon_id

Unique identifier for each wagon:

```csv
wagon_id
W0001
W0002
W0003
```

**Requirements:**
- Must be globally unique
- Used for tracking throughout simulation
- Appears in output reports

**Naming Convention:**
- `W0001`, `W0002`, ... for sequential numbering
- Zero-padded for sorting (W0001 vs W1)

**In ten_trains_two_days:** W0001 through W0224 (224 wagons)

### arrival_time

When the train arrives at the yard:

```csv
arrival_time
2025-12-01T06:00:00+00:00
2025-12-01T10:48:00+00:00
2025-12-02T06:00:00+00:00
```

**Format:** ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SS+00:00`)

**Requirements:**
- Must be within scenario start_date and end_date
- All wagons in same train have identical arrival_time
- Use UTC timezone (+00:00)

**Arrival Pattern in ten_trains_two_days:**
- Day 1: 5 trains (T1-T5) at 06:00, 10:48, 15:36, 20:24, 01:12
- Day 2: 5 trains (T6-T10) at 06:00, 10:48, 15:36, 20:24, 01:12
- Regular 4h 48min intervals

### length

Physical length of wagon in meters:

```csv
length
15.9
16.1
20.4
23.5
```

**Typical Values:**
- Short wagons: 15.0 - 17.0 m
- Medium wagons: 17.1 - 22.0 m
- Long wagons: 22.1 - 25.0 m

**Effect on Simulation:**
- Determines track capacity usage
- Affects how many wagons fit on tracks
- Realistic distribution improves accuracy

**In ten_trains_two_days:** Random distribution between 15.0 and 25.0 meters

### is_loaded

Whether wagon carries cargo:

```csv
is_loaded
False
False
True
False
```

**Values:**
- `True`: Wagon carries cargo (heavier, may affect operations)
- `False`: Empty wagon

**Current Implementation:**
- Tracked for future enhancements
- May affect retrofit time in future versions
- Currently informational only

**In ten_trains_two_days:** Mostly False, some True (realistic mix)

### needs_retrofit

Whether wagon requires DAC retrofit:

```csv
needs_retrofit
True
True
False
True
```

**Values:**
- `True`: Wagon needs retrofit (enters retrofit process)
- `False`: Wagon already has DAC (bypasses retrofit)

**Effect on Simulation:**
- `True`: Wagon goes through full retrofit process
- `False`: Wagon may go directly to parking or exit

**In ten_trains_two_days:** Mostly True (220/224 wagons need retrofit)

**Use Cases:**
- Model mixed fleets (some already retrofitted)
- Test partial retrofit scenarios
- Simulate phased migration

### Track

Track type where train arrives:

```csv
Track
collection
collection
collection
```

**Typical Value:** `"collection"`

**Purpose:**
- Indicates track type for arrival
- Usually "collection" for incoming trains
- Must match track type in tracks.json

**Current Implementation:** All trains arrive at "collection" tracks

## Train Composition Examples

### Small Train (6 wagons)

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T1;W0001;2025-12-01T06:00:00+00:00;15.9;False;True;collection
T1;W0002;2025-12-01T06:00:00+00:00;16.1;False;True;collection
T1;W0003;2025-12-01T06:00:00+00:00;20.4;False;True;collection
T1;W0004;2025-12-01T06:00:00+00:00;23.5;False;True;collection
T1;W0005;2025-12-01T06:00:00+00:00;18.4;False;True;collection
T1;W0006;2025-12-01T06:00:00+00:00;16.6;False;True;collection
```

**Total length:** 110.9 meters

### Large Train (32 wagons)

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T2;W0007;2025-12-01T10:48:00+00:00;18.8;False;True;collection
T2;W0008;2025-12-01T10:48:00+00:00;22.3;False;True;collection
...
T2;W0038;2025-12-01T10:48:00+00:00;21.7;False;True;collection
```

**Total length:** ~640 meters (32 wagons × ~20m average)

### Mixed Train (loaded and empty)

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T4;W0076;2025-12-01T20:24:00+00:00;24.5;True;True;collection
T4;W0077;2025-12-01T20:24:00+00:00;18.4;False;True;collection
T4;W0093;2025-12-01T20:24:00+00:00;19.1;True;True;collection
```

**Realistic:** Mix of loaded and empty wagons

### Partially Retrofitted Train

```csv
train_id;wagon_id;arrival_time;length;is_loaded;needs_retrofit;Track
T3;W0062;2025-12-01T15:36:00+00:00;18.4;False;False;collection
T3;W0063;2025-12-01T15:36:00+00:00;18.6;False;True;collection
T4;W0080;2025-12-01T20:24:00+00:00;19.7;False;False;collection
```

**Use case:** Some wagons already have DAC

## Arrival Schedule Analysis

### ten_trains_two_days Schedule

| Train | Arrival Time | Wagons | Avg Length | Loaded | Need Retrofit |
|-------|--------------|--------|------------|--------|---------------|
| T1 | Day 1, 06:00 | 6 | 18.5m | 0 | 6 |
| T2 | Day 1, 10:48 | 32 | 20.0m | 0 | 32 |
| T3 | Day 1, 15:36 | 27 | 20.2m | 0 | 26 |
| T4 | Day 1, 20:24 | 30 | 20.1m | 2 | 28 |
| T5 | Day 2, 01:12 | 9 | 18.6m | 2 | 9 |
| T6 | Day 2, 06:00 | 21 | 19.5m | 1 | 20 |
| T7 | Day 2, 10:48 | 28 | 20.3m | 2 | 28 |
| T8 | Day 2, 15:36 | 33 | 20.0m | 0 | 33 |
| T9 | Day 2, 20:24 | 32 | 20.2m | 2 | 32 |
| T10 | Day 3, 01:12 | 6 | 20.3m | 2 | 6 |

**Total:** 224 wagons, 220 need retrofit

### Arrival Pattern

**Interval:** 4 hours 48 minutes (288 minutes)

**Distribution:**
- Realistic irregular train sizes
- Mix of small (6-9) and large (30-33) trains
- Spread over 2 days

## Common Modifications

### Adding More Trains

Extend the schedule:

```csv
T11;W0225;2025-12-03T06:00:00+00:00;19.5;False;True;collection
T11;W0226;2025-12-03T06:00:00+00:00;20.1;False;True;collection
```

**Requirements:**
- Unique wagon IDs
- Arrival time within scenario timeframe
- Update scenario end_date if needed

### Changing Arrival Frequency

More frequent arrivals:

```csv
T1;W0001;2025-12-01T06:00:00+00:00;...
T2;W0007;2025-12-01T08:00:00+00:00;...  # 2 hours later
T3;W0039;2025-12-01T10:00:00+00:00;...  # 2 hours later
```

**Effect:** Higher workload, tests capacity limits

### Uniform Train Sizes

All trains with 20 wagons:

```csv
T1;W0001;...;20.0;False;True;collection
...
T1;W0020;...;20.0;False;True;collection
T2;W0021;...;20.0;False;True;collection
...
T2;W0040;...;20.0;False;True;collection
```

**Effect:** Predictable workload, easier analysis

### Peak Load Scenario

Multiple trains arriving simultaneously:

```csv
T1;W0001;2025-12-01T06:00:00+00:00;...
T2;W0007;2025-12-01T06:00:00+00:00;...  # Same time
T3;W0039;2025-12-01T06:00:00+00:00;...  # Same time
```

**Effect:** Stress test collection track capacity

## Validation Rules

- Wagon IDs must be unique across entire file
- Arrival times must be within scenario timeframe
- All wagons in same train must have identical arrival_time
- Length must be positive
- Boolean fields must be True or False
- Track type must match available track types

## Effect on Simulation

### Workload

Total wagons needing retrofit determines:
- Required workshop capacity
- Simulation duration
- Resource requirements

**Formula:**
```
min_duration = (wagons_needing_retrofit × retrofit_time) / (workshops × stations)
```

**ten_trains_two_days:**
- 220 wagons × 60 min / (2 workshops × 2 stations) = 3,300 minutes = 55 hours

### Arrival Pattern

Affects:
- Collection track utilization
- Parking track fill rate
- Workshop queue buildup

**Steady arrivals:** Consistent workload
**Burst arrivals:** Peak capacity testing
**Sparse arrivals:** Underutilization testing

### Train Size Distribution

Affects:
- Collection track capacity requirements
- Locomotive utilization patterns
- Wagon distribution complexity

## Creating Custom Schedules

### Using Spreadsheet Software

1. Open Excel/LibreOffice Calc
2. Create columns: train_id, wagon_id, arrival_time, length, is_loaded, needs_retrofit, Track
3. Fill in data
4. Save as CSV with semicolon delimiter

### Programmatic Generation

Python script example:

```python
import csv
from datetime import datetime, timedelta

with open('train_schedule.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['train_id', 'wagon_id', 'arrival_time', 'length', 'is_loaded', 'needs_retrofit', 'Track'])
    
    wagon_id = 1
    for train in range(1, 11):
        arrival = datetime(2025, 12, 1, 6, 0) + timedelta(hours=4.8 * (train - 1))
        for wagon in range(20):
            writer.writerow([
                f'T{train}',
                f'W{wagon_id:04d}',
                arrival.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
                round(15 + random.random() * 10, 1),
                'False',
                'True',
                'collection'
            ])
            wagon_id += 1
```

## Next Steps

Continue to [Chapter 10: Running Your Simulation](10-running-simulation.md) to learn how to execute and analyze results.
