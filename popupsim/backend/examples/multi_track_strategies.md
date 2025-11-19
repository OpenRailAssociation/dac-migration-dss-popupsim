# Multi-Track Selection Strategies Demo

## Overview
Demonstration of 3 collection tracks, 2 retrofit tracks, and 2 locomotives with configurable selection strategies.

## Configuration

### Tracks
- **Collection Tracks**: 3 tracks with different capacities
  - collection_1: 100m → 75m capacity (75% fill)
  - collection_2: 120m → 90m capacity (75% fill)
  - collection_3: 80m → 60m capacity (75% fill)

- **Retrofit Tracks**: 2 tracks with different capacities
  - retrofit_1: 150m → 112.5m capacity (75% fill)
  - retrofit_2: 130m → 97.5m capacity (75% fill)

### Resources
- **Locomotives**: 2 locos (loco_1, loco_2) starting at parking track
- **Wagons**: 12 wagons @ 20m each = 240m total

## Selection Strategies

Both collection and retrofit track selection support 4 strategies:

### 1. LEAST_OCCUPIED (Default)
Selects track with lowest occupancy percentage. Balances load across tracks.

**Example Result:**
- retrofit_1: 100m (88.9%) - 6 wagons
- retrofit_2: 80m (82.1%) - 4 wagons

### 2. ROUND_ROBIN
Cycles through available tracks in order. Simple rotation.

### 3. FIRST_AVAILABLE
Always picks first track with available capacity. Fills tracks sequentially.

### 4. RANDOM
Randomly selects from available tracks. Unpredictable distribution.

## Usage

```python
scenario = Scenario(
    scenario_id="multi_track_demo",
    track_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,  # For collection tracks
    retrofit_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,  # For retrofit tracks
    # ... other fields
)
```

## Process Flow

1. **Train Arrival**: 12 wagons arrive and are distributed to collection tracks using `track_selection_strategy`
2. **Wagon Pickup**: Locomotives pick up wagons from collection tracks
3. **Retrofit Selection**: Each wagon is assigned to a retrofit track using `retrofit_selection_strategy`
4. **Delivery**: Locomotives deliver wagons to their assigned retrofit tracks
5. **Return**: Locomotives return to parking

## Key Features

- **Independent Strategies**: Collection and retrofit tracks use separate strategies
- **Capacity Aware**: Only selects tracks with available capacity
- **Multi-Loco Support**: 2 locomotives work in parallel
- **Dynamic Distribution**: Wagons distributed based on real-time capacity

## Running the Demo

```bash
cd popupsim/backend
uv run python examples/multi_track_demo.py
```

## Output

The demo shows:
- Collection track capacities and usage
- Retrofit track capacities and usage
- Wagon distribution across retrofit tracks
- Final locomotive status
