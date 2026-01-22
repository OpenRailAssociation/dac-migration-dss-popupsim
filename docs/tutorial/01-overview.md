# Chapter 1: Overview

## Scenario Structure

A PopUpSim scenario consists of multiple configuration files that work together to define the simulation. The `ten_trains_two_days` scenario contains 8 files:

```
ten_trains_two_days/
├── scenario.json           # Main configuration and file references
├── topology.json           # Network structure (e.g. track length)
├── tracks.json            # Track definitions and types
├── workshops.json         # Workshop configurations
├── process_times.json     # Operation durations
├── locomotive.json        # Shunting locomotive resources
├── routes.json           # Movement paths between tracks including durations
└── train_schedule.csv    # Wagon arrivals and properties
```

## File Relationships

The files are interconnected, wehere the sceario.json links all of them togeher.

1. **scenario.json** - Entry point that references all other files
2. **topology.json** - Defines edges (track segments) used by tracks.json
3. **tracks.json** - Defines tracks using edges from topology.json
4. **workshops.json** - References workshop tracks from tracks.json
5. **routes.json** - Defines paths between tracks from tracks.json
6. **locomotive.json** - References home tracks from tracks.json
7. **train_schedule.csv** - References track types from tracks.json
8. **process_times.json** - Standalone timing parameters

## Configuration Flow

```
scenario.json (entry point)
    ├─> topology.json (network structure)
    ├─> tracks.json (uses topology edges)
    ├─> workshops.json (uses tracks)
    ├─> routes.json (uses tracks)
    ├─> locomotive.json (uses tracks)
    ├─> train_schedule.csv (uses track types)
    └─> process_times.json (timing parameters)
```

## File Formats

- **JSON files** - Structured configuration with validation
- **CSV file** - Tabular data for train schedules (easier to edit in spreadsheets)

## Validation

PopUpSim validates all configuration files on startup:
- Required fields must be present
- References between files must be valid
- Values must be within acceptable ranges
- Data types must match specifications

If validation fails, PopUpSim provides detailed error messages indicating which file and field caused the issue.

## Next Steps

Continue to [Chapter 2: Scenario Configuration](02-scenario-configuration.md) to learn about the main scenario settings.
