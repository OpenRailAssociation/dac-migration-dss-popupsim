# CSV Data Source Example

This directory demonstrates the CSV data source adapter for PopUpSim's hexagonal architecture.

## File Structure

- `scenario.csv` - Basic scenario metadata (ID, dates, random seed)
- `trains.csv` - Train schedule with arrival times
- `wagons.csv` - Wagon data linked to trains
- `workshops.csv` - Workshop configuration and capacity
- `tracks.csv` - Track definitions with types and capacity
- `routes.csv` - Route definitions between tracks
- `locomotives.csv` - Locomotive fleet data

## Usage

```python
from configuration.application.scenario_loader import ScenarioLoader

# Auto-detect CSV source and load
loader = ScenarioLoader()
scenario_dto = loader.load_scenario('path/to/csv_scenario')

# Or use specific CSV adapter
from configuration.infrastructure.adapters.csv_data_source_adapter import CsvDataSourceAdapter
adapter = CsvDataSourceAdapter()
scenario_dto = adapter.load_scenario('path/to/csv_scenario')
```

## CSV Format Requirements

### scenario.csv
- Required columns: `scenario_id`, `start_date`, `end_date`
- Optional columns: `random_seed`

### trains.csv
- Required columns: `train_id`, `arrival_time`
- Format: ISO datetime strings

### wagons.csv
- Required columns: `wagon_id`, `train_id`, `length`
- Optional columns: `is_loaded`, `needs_retrofit`
- Boolean values: `true`/`false`

### workshops.csv
- Required columns: `workshop_id`, `track_id`, `start_date`, `end_date`
- Optional columns: `retrofit_stations`, `worker`

### tracks.csv
- Required columns: `id`, `name`, `type`
- Optional columns: `capacity`, `edges`
- Track types: `collection`, `workshop`, `retrofitted`, `parking`

### routes.csv
- Required columns: `route_id`, `from_track`, `to_track`, `duration`
- Optional columns: `path` (comma-separated track IDs)

### locomotives.csv
- Required columns: `locomotive_id`, `name`, `track_id`, `start_date`, `end_date`

## Benefits of Hexagonal Architecture

1. **Source Independence**: Same domain logic works with JSON, CSV, API, or database sources
2. **Testability**: Easy to mock data sources for testing
3. **Extensibility**: New data sources can be added without changing core logic
4. **Maintainability**: Clear separation between data access and business logic