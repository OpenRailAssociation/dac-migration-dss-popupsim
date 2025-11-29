# ADR-007: File-Based Data Storage

**Status:** IMPLEMENTED - 2025-01-15

## Context

Need data storage for configuration and results. Full version will use database, but MVP needs simplest approach.

## Decision

Use **file-based storage** with JSON/CSV formats.

## Rationale

- **Local deployment**: No server infrastructure needed
- **Small data volume**: Typical scenarios have <1000 wagons
- **Simple installation**: No database setup required
- **Transparency**: Human-readable formats
- **Version control**: Git-friendly text files
- **Portability**: Easy to share and backup

## Alternatives Considered

- **Files (JSON/CSV)** ✅ Chosen
- **SQLite**: Overkill for MVP data volume
- **PostgreSQL**: Requires installation and setup
- **In-memory only**: No persistence

## Implementation in MVP

### File Formats Supported
```python
# JSON scenario files
{
  "id": "small-scenario",
  "trains": [...],
  "wagons": [...],
  "workshops": [...]
}

# CSV directory structure
csv_scenario/
├── scenario.csv
├── trains.csv
├── wagons.csv
└── workshops.csv
```

### Data Access Layer
```python
# configuration/infrastructure/adapters/
class JsonDataSourceAdapter:
    def load_scenario(self, path: Path) -> ScenarioInputDTO:
        with open(path) as f:
            return ScenarioInputDTO.model_validate(json.load(f))

class CsvDataSourceAdapter:
    def load_scenario(self, directory: Path) -> ScenarioInputDTO:
        # Load from multiple CSV files
        return self._build_scenario_from_csvs(directory)
```

### Results Export
- **CSV Files**: Simulation metrics and KPIs
- **PNG Charts**: Matplotlib visualizations
- **JSON Data**: Raw metrics for future web interface

## Consequences

### Achieved
- ✅ **Zero Installation**: No database setup required
- ✅ **Transparent Data**: Human-readable JSON/CSV formats
- ✅ **Version Control**: Git-friendly text files
- ✅ **Multi-Format Support**: JSON and CSV input via hexagonal adapters
- ✅ **Export Flexibility**: Multiple output formats for different use cases

### Files Implementing This Decision
- `configuration/infrastructure/adapters/` - File format adapters
- `analytics/infrastructure/exporters/` - Results export
- `Data/examples/` - Example scenarios in JSON and CSV