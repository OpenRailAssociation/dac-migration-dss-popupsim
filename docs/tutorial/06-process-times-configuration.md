# Chapter 6: Process Times Configuration

## File: process_times.json

The process_times.json file defines the duration of various operations in the simulation. These timing parameters directly affect throughput, resource utilization, and overall simulation performance.

## Example Configuration

```json
{
  "wagon_retrofit_time": 60.0,
  "train_to_hump_delay": 0.0,
  "wagon_hump_interval": 0.0,
  "screw_coupling_time": 3.0,
  "screw_decoupling_time": 5.0,
  "dac_coupling_time": 0.5,
  "dac_decoupling_time": 0.5
}
```

## Parameters

All time values are in **minutes** unless otherwise specified.

### wagon_retrofit_time

Time required to retrofit one wagon with DAC:

```json
"wagon_retrofit_time": 60.0
```

| Value | Description | Throughput Impact |
|-------|-------------|-------------------|
| 30.0 | Fast retrofit (30 min) | High throughput |
| 60.0 | Standard retrofit (1 hour) | Medium throughput |
| 120.0 | Slow retrofit (2 hours) | Low throughput |

**Critical Parameter:**
- Directly affects workshop throughput
- Longer time = more bottlenecks
- Shorter time = higher capacity requirements

**Throughput Calculation:**
```
wagons_per_station_per_day = (24 × 60) / wagon_retrofit_time
```

**Examples:**
- 30 min: 48 wagons/station/day
- 60 min: 24 wagons/station/day
- 120 min: 12 wagons/station/day

**Realistic Values:**
- Quick retrofit: 30-45 minutes
- Standard retrofit: 60-90 minutes
- Complex retrofit: 120-180 minutes

### train_to_hump_delay

Delay before train wagons can be distributed:

```json
"train_to_hump_delay": 0.0
```

**Purpose:** Models administrative or safety delays after train arrival

| Value | Description |
|-------|-------------|
| 0.0 | Immediate processing (current setting) |
| 5.0 | 5-minute safety check |
| 15.0 | 15-minute inspection |

**Effect:**
- Adds delay to all arriving trains
- Increases collection track occupancy
- May create arrival bottlenecks

**Current Setting:** 0.0 (no delay) for simplified simulation

### wagon_hump_interval

Time interval between distributing individual wagons:

```json
"wagon_hump_interval": 0.0
```

**Purpose:** Models the time to separate and route individual wagons from a train

| Value | Description |
|-------|-------------|
| 0.0 | Instant distribution (current setting) |
| 1.0 | 1 minute per wagon |
| 2.0 | 2 minutes per wagon |

**Effect:**
- Longer interval = slower train processing
- Affects collection track occupancy
- Impacts locomotive utilization

**Example:**
- 30-wagon train with 2-minute interval
- Total distribution time: 30 × 2 = 60 minutes

**Current Setting:** 0.0 (instant) for simplified simulation

### screw_coupling_time

Time to couple wagons using traditional screw couplers:

```json
"screw_coupling_time": 3.0
```

**Purpose:** Models coupling wagons that haven't been retrofitted yet

| Value | Description |
|-------|-------------|
| 2.0 | Fast coupling |
| 3.0 | Standard coupling (current) |
| 5.0 | Slow/careful coupling |

**When Used:**
- Coupling non-retrofitted wagons
- Initial train assembly
- Moving wagons to retrofit

**Realistic Values:** 2-5 minutes per coupling operation

### screw_decoupling_time

Time to decouple wagons using traditional screw couplers:

```json
"screw_decoupling_time": 5.0
```

**Purpose:** Models decoupling wagons that haven't been retrofitted yet

| Value | Description |
|-------|-------------|
| 3.0 | Fast decoupling |
| 5.0 | Standard decoupling (current) |
| 7.0 | Slow/careful decoupling |

**When Used:**
- Separating non-retrofitted wagons
- Train disassembly
- Individual wagon movements

**Note:** Typically slower than coupling due to safety procedures

**Realistic Values:** 3-7 minutes per decoupling operation

### dac_coupling_time

Time to couple wagons using Digital Automatic Couplers:

```json
"dac_coupling_time": 0.5
```

**Purpose:** Models coupling retrofitted wagons with DAC

| Value | Description |
|-------|-------------|
| 0.5 | Automatic coupling (current) |
| 1.0 | Semi-automatic |

**When Used:**
- Coupling retrofitted wagons
- Final train assembly
- Moving completed wagons

**Key Advantage:** Much faster than screw coupling (0.5 vs 3.0 minutes)

**Realistic Values:** 0.5-1.0 minutes (automatic operation)

### dac_decoupling_time

Time to decouple wagons using Digital Automatic Couplers:

```json
"dac_decoupling_time": 0.5
```

**Purpose:** Models decoupling retrofitted wagons with DAC

| Value | Description |
|-------|-------------|
| 0.5 | Automatic decoupling (current) |
| 1.0 | Semi-automatic |

**When Used:**
- Separating retrofitted wagons
- Parking operations
- Final distribution

**Key Advantage:** Much faster than screw decoupling (0.5 vs 5.0 minutes)

**Realistic Values:** 0.5-1.0 minutes (automatic operation)

## Coupling/Decoupling Comparison

| Operation | Screw Coupler | DAC | Time Savings |
|-----------|---------------|-----|--------------|
| Coupling | 3.0 min | 0.5 min | 83% faster |
| Decoupling | 5.0 min | 0.5 min | 90% faster |
| Round trip | 8.0 min | 1.0 min | 87.5% faster |

**Simulation Impact:** DAC significantly reduces shunting operation time

## Common Modifications

### Faster Retrofit Operations

Simulate improved workshop efficiency:

```json
{
  "wagon_retrofit_time": 45.0,  // Was 60.0
  "screw_coupling_time": 2.5,   // Was 3.0
  "screw_decoupling_time": 4.0  // Was 5.0
}
```

**Effect:**
- Increases throughput by 25%
- Reduces workshop bottlenecks
- Improves resource utilization

### Realistic Train Processing

Add delays for safety and inspection:

```json
{
  "train_to_hump_delay": 10.0,    // Was 0.0
  "wagon_hump_interval": 1.5      // Was 0.0
}
```

**Effect:**
- More realistic simulation
- Increases collection track occupancy
- May reveal arrival bottlenecks

### Slower Coupling Operations

Model less experienced crews:

```json
{
  "screw_coupling_time": 5.0,     // Was 3.0
  "screw_decoupling_time": 7.0,   // Was 5.0
  "dac_coupling_time": 1.0,       // Was 0.5
  "dac_decoupling_time": 1.0      // Was 0.5
}
```

**Effect:**
- Increases locomotive utilization
- Longer wagon movement times
- May create shunting bottlenecks

## Validation Rules

- All values must be non-negative numbers
- Time values are in minutes
- Zero values are allowed (instant operations)
- Decoupling typically ≥ coupling time

## Effect on Simulation

### Primary Bottleneck: wagon_retrofit_time

This parameter typically dominates simulation performance:

```
Total retrofit time = wagon_count × wagon_retrofit_time / retrofit_stations
```

**Example (ten_trains_two_days):**
- 224 wagons × 60 minutes / 4 stations = 3,360 minutes = 56 hours

### Secondary Impact: Coupling/Decoupling

Affects locomotive utilization and wagon movement:

```
Movement time = travel_time + coupling_time + decoupling_time
```

**Example:**
- Travel: 1 minute
- Screw decouple: 5 minutes
- Screw couple: 3 minutes
- Total: 9 minutes per movement

### Optimization Strategy

1. **Reduce retrofit time** → Biggest throughput impact
2. **Optimize coupling operations** → Improves shunting efficiency
3. **Minimize delays** → Reduces idle time
4. **Balance all parameters** → Realistic simulation

## Performance Tuning

### High Throughput Scenario

```json
{
  "wagon_retrofit_time": 30.0,
  "train_to_hump_delay": 0.0,
  "wagon_hump_interval": 0.0,
  "screw_coupling_time": 2.0,
  "screw_decoupling_time": 3.0,
  "dac_coupling_time": 0.5,
  "dac_decoupling_time": 0.5
}
```

### Realistic Scenario

```json
{
  "wagon_retrofit_time": 75.0,
  "train_to_hump_delay": 15.0,
  "wagon_hump_interval": 2.0,
  "screw_coupling_time": 4.0,
  "screw_decoupling_time": 6.0,
  "dac_coupling_time": 1.0,
  "dac_decoupling_time": 1.0
}
```

### Conservative Scenario

```json
{
  "wagon_retrofit_time": 120.0,
  "train_to_hump_delay": 20.0,
  "wagon_hump_interval": 3.0,
  "screw_coupling_time": 5.0,
  "screw_decoupling_time": 7.0,
  "dac_coupling_time": 1.5,
  "dac_decoupling_time": 1.5
}
```

## Next Steps

Continue to [Chapter 7: Locomotive Configuration](07-locomotive-configuration.md) to learn about shunting resources.
