# OSM Railway Tags Reference

## Edge Type Field
The `type` field in edges comes from the OSM `railway` tag on ways.

### Common Values:
- **rail**: Main railway track (active)
- **disused**: Railway tag value when track is disused
- **siding**: Side track for loading/unloading
- **yard**: Track in a railway yard
- **spur**: Short branch line
- **crossover**: Track connecting parallel lines
- **service**: Service track

## Edge Status Field
The `status` field indicates operational state:
- **active**: Track is in use
- **disused**: Track exists but not operational

### Detection Logic:
Status is set to "disused" if the way has:
- `disused:railway=*` tag, OR
- `abandoned:railway=*` tag

Otherwise status is "active".

## Node Type Field
The `type` field in nodes comes from the OSM `railway` tag on nodes.

### Common Values:
- **switch**: Railway switch/turnout
- **buffer_stop**: End of track bumper
- **junction**: Track junction point
- **level_crossing**: Road/rail crossing
- **signal**: Railway signal
- **stop**: Station stop point
- **crossing**: Railway crossing
- **derail**: Derail device

## OSM Lifecycle Prefixes

OpenStreetMap uses lifecycle prefixes to indicate infrastructure state:

- **`disused:railway=*`**: Infrastructure still exists but is not in use
  - Physical structure intact
  - Could potentially be reactivated
  
- **`abandoned:railway=*`**: Infrastructure exists but deteriorated
  - Physical structure present but degraded
  - Unlikely to be reactivated without major work
  
- **`razed:railway=*`**: Infrastructure completely removed
  - Physically demolished
  - Only historical record remains
  - NOT currently detected by converter

## Current Converter Behavior

The converter:
1. Takes `railway` tag value as the `type` field
2. Checks for `disused:railway` or `abandoned:railway` tags
3. Sets `status` to "disused" if either prefix exists, otherwise "active"
4. Does NOT currently handle `razed:railway` (would need special handling)

## Example OSM Tags

### Active track:
```json
{
  "railway": "rail",
  "gauge": "1435",
  "electrified": "contact_line"
}
```
→ type: "rail", status: "active"

### Disused track:
```json
{
  "railway": "rail",
  "disused:railway": "rail",
  "gauge": "1435"
}
```
→ type: "rail", status: "disused"

### Abandoned track:
```json
{
  "railway": "disused",
  "abandoned:railway": "rail",
  "gauge": "1435"
}
```
→ type: "disused", status: "disused"
