# Chapter 8: Routes Configuration

## File: routes.json

The routes.json file defines movement paths between tracks. Routes specify which tracks can be reached from other tracks, the path taken, and the travel duration. Proper route configuration is essential for locomotive operations.

## Example Configuration

```json
{
  "routes": [
    {
      "id": "track_19_collection1",
      "duration": 1.0,
      "path": ["track_19", "Mainline", "collection1"]
    },
    {
      "id": "collection1_retrofit",
      "duration": 1.0,
      "path": ["collection1", "Mainline", "retrofit"]
    },
    {
      "id": "retrofit_WS1",
      "duration": 1.0,
      "path": ["retrofit", "Mainline", "WS1"]
    },
    {
      "id": "WS1_retrofitted",
      "duration": 1.0,
      "path": ["WS1", "Mainline", "retrofitted"]
    },
    {
      "id": "retrofitted_parking1",
      "duration": 1.0,
      "path": ["retrofitted", "parking1"]
    }
  ]
}
```

## Route Structure

Each route definition contains:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Unique route identifier |
| `duration` | float | Yes | Travel time in minutes |
| `path` | array[string] | Yes | Ordered list of track IDs |

## Parameters Explained

### id

Unique identifier for the route:

```json
"id": "track_19_collection1"
```

**Naming Convention:**
- Format: `source_destination`
- Example: `track_19_collection1` (from track_19 to collection1)
- Clear naming helps debugging

**Requirements:**
- Must be unique across all routes
- Used in logs and reports

### duration

Travel time for the route in minutes:

```json
"duration": 1.0
```

| Value | Description | Use Case |
|-------|-------------|----------|
| 0.5 | Very short (30 seconds) | Adjacent tracks |
| 1.0 | Short (1 minute) | Standard yard movement |
| 2.0 | Medium (2 minutes) | Cross-yard movement |
| 5.0 | Long (5 minutes) | Distant tracks |

**Factors Affecting Duration:**
- Physical distance
- Speed limits
- Track complexity
- Switch operations

**Current Scenario:** All routes use 1.0 minute (simplified)

### path

Ordered sequence of tracks from source to destination:

```json
"path": ["track_19", "Mainline", "collection1"]
```

**Structure:**
- First element: Source track
- Middle elements: Intermediate tracks (e.g., mainline)
- Last element: Destination track

**Requirements:**
- All track IDs must exist in tracks.json
- Path must be physically possible
- Minimum 2 tracks (source and destination)

## Route Types

### Direct Routes

No intermediate tracks:

```json
{
  "id": "retrofitted_parking1",
  "duration": 1.0,
  "path": ["retrofitted", "parking1"]
}
```

**Use case:** Adjacent tracks with direct connection

### Via Mainline

Routes through main circulation path:

```json
{
  "id": "track_19_collection1",
  "duration": 1.0,
  "path": ["track_19", "Mainline", "collection1"]
}
```

**Use case:** Most yard movements (standard pattern)

### Multi-Hop Routes

Multiple intermediate tracks:

```json
{
  "id": "parking1_WS2",
  "duration": 2.0,
  "path": ["parking1", "collection1", "Mainline", "WS2"]
}
```

**Use case:** Complex yard layouts

## Route Patterns in ten_trains_two_days

### Locomotive Home to Operational Tracks

Locomotive starts at track_19, needs routes to all areas:

```json
{"id": "track_19_collection1", "duration": 1.0, "path": ["track_19", "Mainline", "collection1"]},
{"id": "track_19_collection2", "duration": 1.0, "path": ["track_19", "Mainline", "collection2"]},
{"id": "track_19_retrofit", "duration": 1.0, "path": ["track_19", "Mainline", "retrofit"]},
{"id": "track_19_WS1", "duration": 1.0, "path": ["track_19", "Mainline", "WS1"]},
{"id": "track_19_WS2", "duration": 1.0, "path": ["track_19", "Mainline", "WS2"]},
{"id": "track_19_retrofitted", "duration": 1.0, "path": ["track_19", "Mainline", "retrofitted"]}
```

### Return Routes to Locomotive Home

Locomotive returns from operational tracks:

```json
{"id": "collection1_track_19", "duration": 1.0, "path": ["collection1", "Mainline", "track_19"]},
{"id": "collection2_track_19", "duration": 1.0, "path": ["collection2", "Mainline", "track_19"]},
{"id": "retrofit_track_19", "duration": 1.0, "path": ["retrofit", "Mainline", "track_19"]},
{"id": "WS1_track_19", "duration": 1.0, "path": ["WS1", "Mainline", "track_19"]},
{"id": "WS2_track_19", "duration": 1.0, "path": ["WS2", "Mainline", "track_19"]},
{"id": "retrofitted_track_19", "duration": 1.0, "path": ["retrofitted", "Mainline", "track_19"]}
```

### Operational Flow Routes

Wagon movement through retrofit process:

```json
{"id": "collection1_retrofit", "duration": 1.0, "path": ["collection1", "Mainline", "retrofit"]},
{"id": "collection2_retrofit", "duration": 1.0, "path": ["collection2", "Mainline", "retrofit"]},
{"id": "retrofit_WS1", "duration": 1.0, "path": ["retrofit", "Mainline", "WS1"]},
{"id": "retrofit_WS2", "duration": 1.0, "path": ["retrofit", "Mainline", "WS2"]},
{"id": "WS1_retrofitted", "duration": 1.0, "path": ["WS1", "Mainline", "retrofitted"]},
{"id": "WS2_retrofitted", "duration": 1.0, "path": ["WS2", "Mainline", "retrofitted"]}
```

### Parking Distribution Routes

From retrofitted track to parking:

```json
{"id": "retrofitted_parking1", "duration": 1.0, "path": ["retrofitted", "parking1"]},
{"id": "retrofitted_parking2", "duration": 1.0, "path": ["retrofitted", "parking2"]},
{"id": "retrofitted_parking3", "duration": 1.0, "path": ["retrofitted", "parking3"]},
...
{"id": "retrofitted_parking16", "duration": 1.0, "path": ["retrofitted", "Mainline", "parking16"]}
```

**Note:** Some parking tracks have direct routes, others via mainline

## Route Completeness

### Required Routes

For proper operation, ensure routes exist for:

1. **Locomotive home → All operational tracks**
2. **All operational tracks → Locomotive home**
3. **Collection → Retrofit staging**
4. **Retrofit staging → Workshops**
5. **Workshops → Retrofitted staging**
6. **Retrofitted staging → Parking tracks**

### Bidirectional Routes

Most routes need bidirectional pairs:

```json
{"id": "A_to_B", "duration": 1.0, "path": ["A", "B"]},
{"id": "B_to_A", "duration": 1.0, "path": ["B", "A"]}
```

**Exception:** One-way flows (e.g., retrofitted → parking may not need reverse)

## Common Modifications

### Adding Routes for New Track

When adding a new parking track (parking17):

```json
{
  "id": "retrofitted_parking17",
  "duration": 1.0,
  "path": ["retrofitted", "Mainline", "parking17"]
}
```

### Adding Routes for New Workshop

When adding a third workshop (WS3):

```json
{"id": "track_19_WS3", "duration": 1.0, "path": ["track_19", "Mainline", "WS3"]},
{"id": "WS3_track_19", "duration": 1.0, "path": ["WS3", "Mainline", "track_19"]},
{"id": "retrofit_WS3", "duration": 1.0, "path": ["retrofit", "Mainline", "WS3"]},
{"id": "WS3_retrofitted", "duration": 1.0, "path": ["WS3", "Mainline", "retrofitted"]}
```

### Realistic Travel Times

Model actual yard distances:

```json
{"id": "track_19_collection1", "duration": 0.5, "path": ["track_19", "collection1"]},
{"id": "track_19_WS1", "duration": 2.0, "path": ["track_19", "Mainline", "WS1"]},
{"id": "WS1_parking15", "duration": 3.5, "path": ["WS1", "Mainline", "parking15"]}
```

**Effect:** More realistic simulation, affects locomotive utilization

### Complex Yard Layout

Multiple mainlines or circulation paths:

```json
{
  "id": "north_to_south",
  "duration": 5.0,
  "path": ["north_area", "mainline_north", "junction", "mainline_south", "south_area"]
}
```

## Validation Rules

- Route IDs must be unique
- All track IDs in path must exist in tracks.json
- Duration must be positive
- Path must have at least 2 tracks
- First track = source, last track = destination

## Effect on Simulation

### Travel Time Impact

Route duration affects:
- Locomotive utilization
- Wagon waiting times
- Overall throughput

**Example:**
- 1-minute routes: Low impact on utilization
- 5-minute routes: Significant impact, may need more locomotives

### Route Availability

Missing routes cause:
- Simulation errors
- Unreachable tracks
- Blocked operations

**Always verify:** All necessary routes exist for operational flow

### Route Optimization

**Shortest Path:**
- Minimize intermediate tracks
- Reduce travel time
- Improve efficiency

**Realistic Path:**
- Follow actual yard layout
- Include necessary intermediate tracks
- Model real operations

## Performance Considerations

### Route Count

**ten_trains_two_days has 33 routes:**
- Locomotive home: 12 routes (6 out, 6 back)
- Operational flow: 6 routes
- Parking distribution: 15 routes

**Scaling:**
- More tracks = more routes needed
- N tracks may need O(N²) routes for full connectivity
- Focus on necessary routes only

### Route Lookup

Simulation finds routes by source-destination pair:
- Fast lookup with proper indexing
- Route count has minimal performance impact
- Missing routes cause errors, not slowdowns

## Troubleshooting

### "No route found" Error

**Cause:** Missing route definition

**Solution:** Add route from source to destination:
```json
{"id": "source_destination", "duration": 1.0, "path": ["source", "Mainline", "destination"]}
```

### "Track not found in path" Error

**Cause:** Route references non-existent track

**Solution:** Verify all tracks in path exist in tracks.json

### Unreachable Tracks

**Symptom:** Wagons never reach certain tracks

**Solution:** Verify bidirectional routes exist

## Next Steps

Continue to [Chapter 9: Train Schedule Configuration](09-train-schedule-configuration.md) to learn about wagon arrivals and properties.
