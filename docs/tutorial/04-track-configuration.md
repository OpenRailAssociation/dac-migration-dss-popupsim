# Chapter 4: Track Configuration

## File: tracks.json

The tracks.json file defines functional tracks by assigning types and properties to the physical edges defined in topology.json. Track types determine how the simulation uses each track.

## Example Configuration

```json
{
  "tracks": [
    {"id": "parking1", "name": "Parking track", "edges": ["parking1"], "type": "parking"},
    {"id": "collection1", "name": "Collection track", "edges": ["collection1"], "type": "collection"},
    {"id": "WS1", "edges": ["WS1"], "type": "workshop"},
    {"id": "loco_parking", "edges": ["loco_parking"], "type": "rescource_parking"},
    {"id": "Mainline", "name": "Mainline connecting yards", "edges": ["Mainline"], "type": "mainline"}
  ]
}
```

## Track Structure

Each track definition contains:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Unique track identifier |
| `name` | string | No | Human-readable track name |
| `edges` | array[string] | Yes | List of edge IDs from topology.json |
| `type` | string | Yes | Track type (determines function) |

## Track Types

### parking

**Purpose:** Store wagons waiting for retrofit or after completion

```json
{"id": "parking1", "name": "Parking track", "edges": ["parking1"], "type": "parking"}
```

**Characteristics:**
- Used for wagon storage
- Capacity based on edge length
- Selected by `parking_selection_strategy`
- Multiple parking tracks improve throughput

**In ten_trains_two_days:** 15 parking tracks (parking1-parking16, excluding parking4)

### collection

**Purpose:** Receive incoming trains and temporarily hold wagons

```json
{"id": "collection1", "name": "Collection track", "edges": ["collection1"], "type": "collection"}
```

**Characteristics:**
- First destination for arriving trains
- Must accommodate full train lengths
- Wagons are distributed from here to parking or retrofit
- Typically 2-4 collection tracks needed

**In ten_trains_two_days:** 2 collection tracks

### workshop

**Purpose:** Dedicated tracks for workshop operations

```json
{"id": "WS1", "edges": ["WS1"], "type": "workshop"}
```

**Characteristics:**
- Associated with workshop definitions in workshops.json
- Wagons undergo retrofit here
- Capacity affects workshop throughput
- Number of tracks = number of workshops

**In ten_trains_two_days:** 2 workshop tracks (WS1, WS2)

### retrofit

**Purpose:** Staging area for wagons ready for retrofit

```json
{"id": "retrofit", "edges": ["retrofit"], "type": "retrofit"}
```

**Characteristics:**
- Holds wagons waiting for workshop availability
- Acts as a buffer between parking and workshop
- Reduces workshop idle time

**In ten_trains_two_days:** 1 retrofit track

### retrofitted

**Purpose:** Staging area for completed wagons

```json
{"id": "retrofitted", "edges": ["retrofitted"], "type": "retrofitted"}
```

**Characteristics:**
- Holds wagons after retrofit completion
- Wagons distributed from here to final parking
- Prevents workshop blocking

**In ten_trains_two_days:** 1 retrofitted track

### rescource_parking

**Purpose:** Home location for locomotives and other resources

```json
{"id": "loco_parking", "edges": ["loco_parking"], "type": "rescource_parking"}
```

**Characteristics:**
- Locomotives return here when idle
- Referenced in locomotive.json as "home track"
- Typically one per locomotive

**In ten_trains_two_days:** 2 resource parking tracks

### mainline

**Purpose:** Main circulation path connecting yard areas

```json
{"id": "Mainline", "name": "Mainline connecting yards", "edges": ["Mainline"], "type": "mainline"}
```

**Characteristics:**
- Used in route definitions
- Represents main yard circulation
- Not used for wagon storage
- Typically very long

**In ten_trains_two_days:** 1 mainline track

## Multi-Edge Tracks

Tracks can span multiple edges:

```json
{"id": "long_track", "edges": ["edge1", "edge2", "edge3"], "type": "parking"}
```

**Total length:** Sum of all edge lengths
**Use case:** Modeling tracks that span multiple physical segments

## Track Naming

The `name` field is optional but recommended for clarity:

```json
{"id": "parking1", "name": "North side parking track 1", "edges": ["parking1"], "type": "parking"}
```

- Used in logs and reports
- Helps identify tracks during analysis
- Not used for simulation logic

## Common Modifications

### Adding More Parking Capacity

Add new parking tracks:

```json
{"id": "parking17", "name": "Additional parking", "edges": ["parking17"], "type": "parking"},
{"id": "parking18", "name": "Additional parking", "edges": ["parking18"], "type": "parking"}
```

**Effect:** Increases total parking capacity, reduces waiting times

### Adding Workshop Capacity

Add workshop tracks (must also update workshops.json):

```json
{"id": "WS3", "edges": ["WS3"], "type": "workshop"}
```

### Changing Track Type

Convert a parking track to collection:

```json
{"id": "parking16", "name": "Converted to collection", "edges": ["parking16"], "type": "collection"}
```

**Effect:** Changes how the simulation uses this track

## Validation Rules

- Track IDs must be unique
- All edge IDs must exist in topology.json
- Track types must be valid values
- Workshop tracks must have corresponding entries in workshops.json
- Resource parking tracks must be referenced in locomotive.json

## Effect on Simulation

- **Track type** determines operational role
- **Number of tracks** affects capacity and throughput
- **Track distribution** impacts resource utilization
- **Edge references** determine physical capacity

## Track Type Summary

| Type | Purpose | Typical Count | Capacity Impact |
|------|---------|---------------|-----------------|
| parking | Wagon storage | 10-20 | High - more = better throughput |
| collection | Train reception | 2-4 | Medium - must fit trains |
| workshop | Retrofit operations | 1-3 | Critical - bottleneck point |
| retrofit | Pre-workshop staging | 1-2 | Medium - buffer for workshops |
| retrofitted | Post-workshop staging | 1-2 | Medium - prevents blocking |
| rescource_parking | Locomotive home | 1 per loco | Low - resource management |
| mainline | Circulation | 1 | Low - routing only |

## Next Steps

Continue to [Chapter 5: Workshop Configuration](05-workshop-configuration.md) to learn about workshop setup.
