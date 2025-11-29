# ADR-013: Hexagonal Architecture for Data Sources

**Status:** IMPLEMENTED - 2025-01-16

## Context

Need to support multiple input formats (JSON, CSV) and prepare for future API integration while maintaining clean separation between domain logic and data access.

## Decision

Implement **hexagonal architecture** specifically for the Configuration Context with data source adapters.

## Rationale

- **Multi-format support**: CSV import requirement from stakeholders
- **Future API readiness**: Planned integration with external systems
- **Testability**: Easy to mock data sources for testing
- **Maintainability**: Clear separation between data access and business logic
- **Extensibility**: New data sources without changing core logic
- **Type safety**: Consistent DTOs across all adapters

## Implementation

- **DataSourcePort**: Interface defining adapter contract
- **JsonDataSourceAdapter**: Wraps existing JSON functionality
- **CsvDataSourceAdapter**: New CSV directory support
- **DataSourceFactory**: Auto-detects source type
- **ScenarioLoader**: Orchestrates using adapters

## Alternatives Considered

- **Hexagonal Architecture** ✅ Chosen
- **Direct CSV parsing**: Tight coupling, hard to test
- **Single JSON format**: Doesn't meet CSV requirement
- **Full hexagonal everywhere**: Too complex for MVP timeline

## Implementation in MVP

### Hexagonal Architecture Components
```python
# configuration/domain/ports/data_source_port.py
class DataSourcePort(ABC):
    @abstractmethod
    def load_scenario(self, source: Path) -> ScenarioInputDTO: ...

# configuration/infrastructure/adapters/
class JsonDataSourceAdapter(DataSourcePort):
    def load_scenario(self, path: Path) -> ScenarioInputDTO:
        with open(path) as f:
            return ScenarioInputDTO.model_validate(json.load(f))

class CsvDataSourceAdapter(DataSourcePort):
    def load_scenario(self, directory: Path) -> ScenarioInputDTO:
        return self._load_from_csv_directory(directory)

# configuration/application/services/scenario_service.py
class ScenarioService:
    def __init__(self, data_source: DataSourcePort):
        self._data_source = data_source  # Dependency injection
```

### Auto-Detection Factory
```python
class DataSourceFactory:
    @staticmethod
    def create_adapter(source: Path) -> DataSourcePort:
        if source.is_file() and source.suffix == '.json':
            return JsonDataSourceAdapter()
        elif source.is_dir():
            return CsvDataSourceAdapter()
        else:
            raise UnsupportedDataSourceError(f"Unsupported source: {source}")
```

## Consequences

### Achieved
- ✅ **Multi-Format Support**: JSON and CSV scenarios supported
- ✅ **Future-Ready**: Easy to add REST API, database adapters
- ✅ **Testable**: Mock adapters for unit testing
- ✅ **Maintainable**: Clear separation between data access and business logic
- ✅ **Type Safety**: Consistent DTOs across all adapters
- ✅ **Auto-Detection**: Automatic format detection based on file/directory

### Files Implementing This Decision
- `configuration/domain/ports/data_source_port.py` - Port interface
- `configuration/infrastructure/adapters/` - JSON and CSV adapters
- `configuration/application/factories/data_source_factory.py` - Auto-detection

## CSV Directory Structure

```
csv_scenario/
├── scenario.csv      # Basic metadata (ID, dates, seed)
├── trains.csv        # Train schedule with arrival times
├── wagons.csv        # Wagon data linked to trains
├── workshops.csv     # Workshop configuration
├── tracks.csv        # Track definitions
├── routes.csv        # Route definitions
└── locomotives.csv   # Locomotive fleet data
```