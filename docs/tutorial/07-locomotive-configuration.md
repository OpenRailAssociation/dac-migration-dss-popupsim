# Chapter 7: Locomotive Configuration

## File: locomotive.json

The locomotive.json file defines shunting locomotives used to move wagons between tracks. Locomotives are critical resources that can become bottlenecks if insufficient capacity is provided.

**⚠️ IMPORTANT LIMITATION:** The current implementation is only tested and validated for **single locomotive operation**. While the configuration supports multiple locomotives, using more than one locomotive may cause issues because:
- The simulation has no real track network model
- Track sharing between locomotives on the same route is not prevented
- Only job-level conflicts are prevented (same job not executed twice, no simultaneous movements on same route)
- Physical track occupancy conflicts are not modeled

**Recommendation:** Use only one locomotive in your scenarios until multi-locomotive support is fully implemented.

## Example Configuration

```json
{
  "metadata": {
    "description": "locomotive configurations for DAC retrofit operations",
    "version": "1.0.0",
    "created": "2024-01-15"
  },
  "locomotives": [
    {
      "id": "LOCO_01",
      "name": "Shunting loco",
      "home track": "track_19"
    }
  ]
}
```

## Structure

### Metadata

Optional metadata for documentation:

| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | string | Locomotive configuration description |
| `version` | string | Configuration version |
| `created` | string | Creation date |

### Locomotive Definitions

Each locomotive in the `locomotives` array:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Unique locomotive identifier |
| `name` | string | No | Human-readable locomotive name |
| `home track` | string | Yes | Track ID where locomotive parks when idle |

## Parameters Explained

### id

Unique identifier for the locomotive:

```json
"id": "LOCO_01"
```

- Must be unique across all locomotives
- Used in logs and reports
- Referenced internally by simulation

**Naming Convention:**
- `LOCO_01`, `LOCO_02`, etc. for sequential numbering
- `SHUNT_A`, `SHUNT_B` for functional naming
- `LOCO_NORTH`, `LOCO_SOUTH` for location-based naming

### name

Human-readable locomotive name:

```json
"name": "Shunting loco"
```

- Optional but recommended
- Used in reports and visualizations
- Helps identify locomotives during analysis

**Examples:**
- "Main shunting locomotive"
- "Backup shunting unit"
- "Heavy-duty shunter"

### home track

Track where the locomotive returns when idle:

```json
"home track": "track_19"
```

**Requirements:**
- Must reference a track ID from tracks.json
- Track should have type "rescource_parking"
- Track must be accessible via routes

**Purpose:**
- Defines locomotive starting position
- Idle locomotives return here
- Affects travel time to first task

## Locomotive Operations

### Task Assignment

Locomotives perform wagon movements:
1. Travel from current location to source track
2. Couple to wagon(s)
3. Travel to destination track
4. Decouple wagon(s)
5. Return to home track or next task

### Resource Contention

With only one locomotive:
- Tasks are queued
- Wagons wait for locomotive availability
- Locomotive utilization may reach 100%

With multiple locomotives:
- Tasks can be parallelized
- Reduced waiting times
- Better throughput

## Common Modifications

### Adding More Locomotives

**⚠️ WARNING:** Multi-locomotive operation is not fully tested. Use at your own risk.

Increase shunting capacity:

```json
{
  "locomotives": [
    {
      "id": "LOCO_01",
      "name": "Primary shunting loco",
      "home track": "track_19"
    },
    {
      "id": "LOCO_02",
      "name": "Secondary shunting loco",
      "home track": "loco_parking"
    }
  ]
}
```

**Requirements:**
1. Add home track in topology.json (if new)
2. Add home track in tracks.json with type "rescource_parking"
3. Add routes connecting home track to other tracks

**Known Limitations:**
- No physical track conflict detection between locomotives
- Locomotives may attempt to use the same track segment simultaneously
- Only route-level and job-level conflicts are prevented
- May cause unrealistic behavior or simulation errors

**Effect (if working correctly):**
- Doubles shunting capacity
- Reduces wagon waiting times
- Improves overall throughput

### Distributed Locomotive Placement

**⚠️ WARNING:** Multi-locomotive operation is not fully tested. Use at your own risk.

Place locomotives in different yard areas:

```json
{
  "locomotives": [
    {
      "id": "LOCO_NORTH",
      "name": "North yard shunter",
      "home track": "loco_parking_north"
    },
    {
      "id": "LOCO_SOUTH",
      "name": "South yard shunter",
      "home track": "loco_parking_south"
    }
  ]
}
```

**Intended Benefit:** Reduces average travel distance to tasks

**Known Limitations:** Physical track conflicts not prevented

### Specialized Locomotives

Different locomotives for different tasks (future enhancement):

```json
{
  "locomotives": [
    {
      "id": "LOCO_HEAVY",
      "name": "Heavy shunter",
      "home track": "track_19",
      "capacity": "high"
    },
    {
      "id": "LOCO_LIGHT",
      "name": "Light shunter",
      "home track": "loco_parking",
      "capacity": "low"
    }
  ]
}
```

**Note:** Current MVP doesn't support specialized attributes, but structure allows future extension

## Locomotive Capacity Planning

### Utilization Analysis

Locomotive utilization depends on:
- Number of wagon movements
- Movement duration (travel + coupling/decoupling)
- Number of locomotives

**Formula:**
```
utilization = (total_movement_time) / (simulation_duration × locomotive_count)
```

### Capacity Requirements

**Rule of thumb:**
```
required_locomotives = ceil(total_movements × avg_movement_time / simulation_duration)
```

**Example (ten_trains_two_days):**
- 224 wagons
- ~4 movements per wagon (collection → parking → retrofit → workshop → retrofitted → parking)
- 896 total movements
- ~10 minutes per movement (travel + coupling/decoupling)
- 48-hour simulation (2880 minutes)
- Required: ceil(896 × 10 / 2880) = ceil(3.11) = 4 locomotives

**Current scenario has 1 locomotive** → Expect high utilization and queuing

### Bottleneck Detection

Signs that locomotives are a bottleneck:
- Locomotive utilization > 80%
- Long wagon waiting times
- Idle workshops waiting for wagons
- Parking tracks not filling efficiently

**Solution:** Add more locomotives

## Validation Rules

- Locomotive IDs must be unique
- Home track must exist in tracks.json
- Home track should have type "rescource_parking"
- At least one locomotive must be defined
- Home track must be reachable via routes

## Effect on Simulation

### Single Locomotive (Current - Recommended)

**Advantages:**
- Simple configuration
- Easy to analyze
- Lower operational cost
- **Fully tested and validated**

**Disadvantages:**
- Potential bottleneck
- High utilization
- Sequential operations only

**Best for:**
- All current scenarios (only tested configuration)
- Small scenarios (< 100 wagons)
- Testing configurations
- Cost-sensitive operations

### Multiple Locomotives (Experimental - Not Recommended)

**⚠️ WARNING:** Not fully tested. May cause simulation errors or unrealistic behavior.

**Intended Advantages:**
- Parallel operations
- Lower utilization per locomotive
- Better throughput
- Redundancy

**Known Issues:**
- No physical track conflict detection
- Locomotives may occupy same track simultaneously
- Unrealistic behavior possible
- Not validated in testing

**Disadvantages:**
- Higher operational cost
- More complex coordination
- Requires more parking space

**Use only if:**
- You understand the limitations
- You can validate results manually
- You're willing to accept potential errors

## Performance Considerations

### Optimal Locomotive Count

**Under-capacity (too few):**
- Locomotives become bottleneck
- Wagons wait excessively
- Workshops may idle
- Poor throughput

**Optimal capacity:**
- 60-80% locomotive utilization
- Minimal wagon waiting
- Workshops stay busy
- Good throughput

**Over-capacity (too many):**
- Low locomotive utilization
- Diminishing returns
- Higher operational cost
- No throughput improvement

### Monitoring Metrics

Track these metrics to assess locomotive capacity:
- Locomotive utilization percentage
- Average wagon waiting time for movement
- Number of queued movement tasks
- Idle time per locomotive

## Integration with Other Components

### Routes (routes.json)

Locomotives use routes to travel between tracks:
- Home track must have routes to all operational tracks
- Missing routes prevent locomotive access
- Route duration affects movement time

### Process Times (process_times.json)

Coupling/decoupling times affect locomotive utilization:
- Longer times = higher utilization
- Shorter times = more movements possible

### Tracks (tracks.json)

Home track configuration:
- Must be type "rescource_parking"
- Should be centrally located
- Must have sufficient capacity

## Next Steps

Continue to [Chapter 8: Routes Configuration](08-routes-configuration.md) to learn about movement paths between tracks.
