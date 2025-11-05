# TICKET-001: Implement Dual Logging System for PopUp-Sim

## Description
Implement logging system with real-time console output and structured data export (CSV/JSON) for dashboard visualization. Both outputs must be independently configurable.

## Priority: High | Story Points: 8

## Acceptance Criteria
- [ ] Real-time console output with configurable log levels
- [ ] CSV/JSON export for analysis data
- [ ] Console and export are completely independent
- [ ] Log rotation for file logs
- [ ] All code has type hints, passes mypy/ruff/pylint
- [ ] Unit test coverage >90%

## Architecture
See [ADR-001](../adr/ADR-001-dual-logging-system.md) for detailed design decisions.

**Approach**: Hybrid system
- Python `logging` module for console/file output
- Custom `EventCollector` for structured data export
- Performance overhead: <0.02% (see [Performance Analysis](../adr/ADR-001-performance-analysis.md))

## Implementation Tasks

### Phase 1: Core Infrastructure (2 days)
- [ ] Create `core/logging/` module structure
- [ ] Implement `SimulationEvent` dataclass (timestamp, event_type, entity_id, location, status, duration, metadata)
- [ ] Implement `setup_console_logger()` and `setup_file_logger()` functions
- [ ] Write unit tests

### Phase 2: Data Export (2 days)
- [ ] Implement `EventCollector` class (collect, export_all, clear, event_count)
- [ ] Define `DataExporter` Protocol
- [ ] Implement `CSVExporter` (exports to CSV with metadata formatting)
- [ ] Implement `JSONExporter` (exports with metadata + events structure)
- [ ] Write unit tests, validate output formats

### Phase 3: Integration (2 days)
- [ ] Update `PopupSim.__init__()` with optional `console_logger` and `event_collector` parameters
- [ ] Implement `PopupSim._emit_event()` to send events to both systems
- [ ] Update `PopupSim.run()` to emit start/end events and export data
- [ ] Update `main.py` CLI with flags: `--verbose`, `--debug`, `--export-format`, `--no-console`, `--enable-file-log`
- [ ] Implement `ReportGenerator` for final summary
- [ ] Write unit tests

### Phase 4: Testing & Docs (2 days)
- [ ] Unit tests for all components (>90% coverage)
- [ ] Integration test with example scenario
- [ ] Performance benchmark (verify <0.1% overhead)
- [ ] Update README with logging examples
- [ ] Create `docs/logging-guide.md` with usage instructions
- [ ] Create `docs/dashboard-integration.md` with data schemas
- [ ] Run all quality checks: `uv run ruff format . && uv run ruff check . && uv run mypy backend/src/ && uv run pylint backend/src/ && uv run pytest`

## Module Structure
```
core/logging/
├── __init__.py
├── events.py           # SimulationEvent dataclass
├── console.py          # setup_console_logger, setup_file_logger
├── collector.py        # EventCollector class
├── report.py           # ReportGenerator class
└── exporters/
    ├── __init__.py
    ├── base.py         # DataExporter Protocol
    ├── csv_exporter.py # CSVExporter class
    └── json_exporter.py # JSONExporter class
```

## CLI Usage Examples
```bash
# Console only
popupsim --scenarioPath ./scenario.json --outputPath ./output --verbose

# Export only
popupsim --scenarioPath ./scenario.json --outputPath ./output --export-format csv,json --no-console

# Both
popupsim --scenarioPath ./scenario.json --outputPath ./output --verbose --export-format csv,json
```

## Output Formats

**Console**: `INFO - Train T001 arrived at entry_track (50 wagons)`

**CSV**: `timestamp,event_type,entity_id,location,status,duration,metadata`

**JSON**: `{"metadata": {...}, "events": [{"timestamp": 0.0, "event_type": "simulation_start", ...}]}`

## Definition of Done
- [ ] All phases completed
- [ ] Tests pass (>90% coverage)
- [ ] MyPy, Ruff, Pylint pass
- [ ] Documentation complete
- [ ] Code review approved
- [ ] PR merged

## Timeline
8 days (2 days per phase)

## Related Docs
- [ADR-001: Architecture](../adr/ADR-001-dual-logging-system.md)
- [Performance Analysis](../adr/ADR-001-performance-analysis.md)
