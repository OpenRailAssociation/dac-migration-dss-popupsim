# Demo Scenario - PopUpSim Usage Example

This scenario demonstrates a realistic PopUpSim configuration with comprehensive workshop operations.

## Scenario Overview

**Duration**: 10 hours (08:00 - 18:00)  
**Total Wagons**: 9 wagons across 3 trains  
**Workshop Capacity**: 6 retrofit stations (2 workshops × 3 stations each)

## Infrastructure Layout

### Collection Tracks (2)
- **T_COL1**: Collection Track 1 (300m capacity)
- **T_COL2**: Collection Track 2 (300m capacity)

### Retrofit Tracks (2)
- **T_RETRO1**: Retrofit Track 1 (200m capacity) → Workshop WS001
- **T_RETRO2**: Retrofit Track 2 (200m capacity) → Workshop WS002

### Retrofitted Tracks (2)
- **T_RETROFITTED1**: Retrofitted Track 1 (250m capacity)
- **T_RETROFITTED2**: Retrofitted Track 2 (250m capacity)

### Parking Tracks (8)
- **T_PARK1-8**: Parking Tracks 1-8 (150m capacity each)

### Locomotive Parking (1)
- **T_LOCO_PARK**: Dedicated locomotive parking (100m capacity)

## Train Schedule

### Train T001 (08:30 arrival)
- **3 wagons**: 2 loaded, 1 unloaded
- **Wagons**: W001 (loaded), W002 (unloaded), W003 (loaded)

### Train T002 (10:00 arrival)
- **2 wagons**: Both unloaded
- **Wagons**: W004 (unloaded), W005 (unloaded)

### Train T003 (12:00 arrival)
- **4 wagons**: 3 loaded, 1 unloaded
- **Wagons**: W006 (loaded), W007 (loaded), W008 (unloaded), W009 (loaded)

## Workshop Configuration

### Workshop WS001 (Track T_RETRO1)
- **Retrofit Stations**: 3
- **Workers**: 6
- **Processing Time**: 45 minutes per wagon

### Workshop WS002 (Track T_RETRO2)
- **Retrofit Stations**: 3
- **Workers**: 6
- **Processing Time**: 45 minutes per wagon

## Locomotive Operations

- **LOCO_001**: Single locomotive handling all train movements
- **Strategy**: Return to parking after each operation
- **Parking**: Dedicated track T_LOCO_PARK

## Usage

Run this scenario with PopUpSim:

```bash
uv run python popupsim/backend/src/main.py \
  --scenarioPath Data/examples/demo_scenario/scenario.json \
  --outputPath output/demo_results
```

## Expected Results

- **Total Processing Time**: ~4.5 hours (9 wagons × 45 min ÷ 6 stations)
- **Throughput**: ~2 wagons/hour
- **Workshop Utilization**: High during peak periods
- **Track Utilization**: Balanced across collection and retrofit tracks

This scenario demonstrates:
- Mixed wagon loads (loaded/unloaded)
- Multiple train arrivals
- Workshop capacity management
- Track selection strategies
- Locomotive scheduling