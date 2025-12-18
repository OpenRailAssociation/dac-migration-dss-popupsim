# ADR-001 Option 3: Hybrid Approach (Logging + Event Collection)

## Metadata
- **Status**: Recommended
- **Date**: 2024-01-15
- **Decision Makers**: Backend Development Team
- **Related Options**: [Option 1](ADR-001-option1-single-logger-multiple-handlers.md), [Option 2](ADR-001-option2-multiple-loggers.md)

## Context and Problem Statement

### Current State
PopUp-Sim simulates freight rail DAC migration scenarios. Currently, the simulation runs without providing runtime visibility to users.

### Requirements
Implement a dual-output logging system that provides:

1. **Console feedback** during simulation runs
   - Track simulation progress
   - Display events as they occur
   - Controlled by `--verbose` flag from main.py

2. **Structured data export** (CSV/JSON) for post-simulation dashboard visualization
   - Complete event history
   - Machine-readable format
   - Independent of console verbosity

**Key Constraint**: Both outputs must be independently configurable to allow flexible user customization.

### Decision Question
Should we **separate logging from data export** by using Python logging for human-readable output and a custom event collection system for structured data?

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        PopupSim                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Simulation Event Emission                   │    │
│  │              _emit_event()                          │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│         ┌───────────┴───────────┐                           │
│         │                       │                           │
│         ▼                       ▼                           │
│  ┌─────────────┐         ┌─────────────┐                   │
│  │   Console   │         │    Event    │                   │
│  │   Logger    │         │  Collector  │                   │
│  │  (logging)  │         │  (custom)   │                   │
│  └──────┬──────┘         └──────┬──────┘                   │
│         │                       │                           │
│         ▼                       ▼                           │
│    ┌────────┐           ┌──────────────┐                   │
│    │ stdout │           │  Exporters   │                   │
│    └────────┘           │ CSV | JSON   │                   │
│                         └──────┬───────┘                    │
│                                ▼                            │
│                         ┌──────────────┐                    │
│                         │  Data Files  │                    │
│                         └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Principle
**Separation of Concerns**: Use each technology for what it's designed for:
- **Python logging**: Human-readable console/file output
- **Custom event collector**: Structured data export (CSV/JSON)

These are fundamentally different concerns and should be separate systems.

## Implementation

### 1. Event Model (`core/logging/events.py`)

```python
"""Simulation event models."""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SimulationEvent:
    """Simulation event."""

    timestamp: float
    event_type: str
    entity_id: str
    location: str
    status: str
    duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
```

### 2. Console Logger (`core/logging/console.py`)

```python
"""Console logging configuration."""

import logging
import sys


def setup_console_logger(
    name: str = 'PopupSim',
    level: str = 'INFO',
    verbose: bool = False
) -> logging.Logger:
    """Configure console logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if verbose:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter('%(levelname)s - %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

### 3. Event Collector (`core/logging/collector.py`)

```python
"""Event collection system for structured data export."""

from pathlib import Path
from typing import Protocol

from .events import SimulationEvent


class DataExporter(Protocol):
    """Protocol for data exporters."""

    def export(self, events: list[SimulationEvent], output_path: Path) -> None:
        """Export events to file."""
        ...


class EventCollector:
    """Collects simulation events for structured data export."""

    def __init__(self) -> None:
        """Initialize event collector."""
        self.events: list[SimulationEvent] = []

    def collect(self, event: SimulationEvent) -> None:
        """Collect an event."""
        self.events.append(event)

    def export(self, exporter: DataExporter, output_path: Path) -> None:
        """Export collected events."""
        exporter.export(self.events, output_path)

    def clear(self) -> None:
        """Clear collected events."""
        self.events.clear()
```

### 4. Exporters (`core/logging/exporters.py`)

```python
"""Data exporters for simulation events."""

import csv
import json
from pathlib import Path

from .events import SimulationEvent


class CSVExporter:
    """Export events to CSV format."""

    def export(self, events: list[SimulationEvent], output_path: Path) -> None:
        """Export events to CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not events:
                return

            writer = csv.DictWriter(f, fieldnames=events[0].to_dict().keys())
            writer.writeheader()

            for event in events:
                writer.writerow(event.to_dict())


class JSONExporter:
    """Export events to JSON format."""

    def export(self, events: list[SimulationEvent], output_path: Path) -> None:
        """Export events to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([event.to_dict() for event in events], f, indent=2)
```

### 5. Usage Example (`simulation/engine.py`)

```python
"""Simulation engine with hybrid logging."""

from pathlib import Path

from core.logging.console import setup_console_logger
from core.logging.collector import EventCollector
from core.logging.exporters import CSVExporter, JSONExporter
from core.logging.events import SimulationEvent


class SimulationEngine:
    """Simulation engine."""

    def __init__(
        self,
        output_dir: Path = Path('output'),
        console_enabled: bool = True,
        verbose: bool = False,
        csv_enabled: bool = True,
        json_enabled: bool = True
    ) -> None:
        """Initialize simulation engine."""
        self.output_dir = output_dir
        self.console_logger = setup_console_logger(verbose=verbose) if console_enabled else None
        self.event_collector = EventCollector()
        self.csv_enabled = csv_enabled
        self.json_enabled = json_enabled

    def _emit_event(self, event: SimulationEvent) -> None:
        """Emit event to both logger and collector."""
        if self.console_logger:
            self.console_logger.info(f"{event.event_type}: {event.entity_id}")

        self.event_collector.collect(event)

    def run(self) -> None:
        """Run simulation."""
        if self.console_logger:
            self.console_logger.info("Starting simulation...")

        event = SimulationEvent(
            timestamp=0.0,
            event_type='train_arrival',
            entity_id='TRAIN-001',
            location='STATION-A',
            status='arrived',
            duration=120.0
        )

        self._emit_event(event)

        if self.console_logger:
            self.console_logger.info("Simulation complete")

        # Export collected data
        if self.csv_enabled:
            self.event_collector.export(
                CSVExporter(),
                self.output_dir / 'events.csv'
            )

        if self.json_enabled:
            self.event_collector.export(
                JSONExporter(),
                self.output_dir / 'events.json'
            )
```

## Design Decisions

### Core Architecture Decision
**Use TWO independent systems**:
1. **Python logging** (`logging.Logger`) for console/file output
2. **Custom EventCollector** for structured data export

### System Responsibilities

#### Logging System (Python logging)
- Console output for users
- File logs for developers
- Human-readable messages
- Controlled by verbose/debug flags

#### Event Collection System (Custom)
- Collect SimulationEvent objects
- Export to CSV/JSON formats
- Structured data for analysis
- Independent of logging configuration

### Data Flow
```python
Simulation Event → _emit_event(event)
                      ↓
        ┌─────────────┼─────────────┐
        ↓                       ↓
   LOGGING SYSTEM        EVENT COLLECTION
        ↓                       ↓
   logger.info()         collector.collect()
        ↓                       ↓
     stdout                  list.append()
                                 ↓
                          exporters.export()
                                 ↓
                          CSV/JSON files
```

### Key Design Choices

#### 1. Separate Systems, Not Integrated
**Decision**: Logging and data collection are completely separate.

**Rationale**:
- Logging is for human consumption
- Data export is for machine consumption
- Different purposes = different systems
- No forced integration

**Benefit**: Each system can evolve independently.

#### 2. Protocol-Based Exporters
**Decision**: Use Protocol (typing.Protocol) for exporter interface.

**Rationale**:
- Type-safe without inheritance
- Easy to add new exporters
- Duck typing with type checking
- Follows Python best practices

**Implementation**:
```python
class DataExporter(Protocol):
    def export(self, events: list[SimulationEvent], output_path: Path) -> None:
        ...
```

#### 3. In-Memory Collection, Batch Export
**Decision**: Collect events in memory, export at end.

**Rationale**:
- Simple implementation
- Fast collection (list.append is O(1))
- No file I/O during simulation
- Export happens after simulation completes

**Trade-off**: Memory usage for large simulations (acceptable for 10,000 events).

#### 4. Event Dataclass
**Decision**: Use @dataclass for SimulationEvent.

**Rationale**:
- Automatic __init__, __repr__, __eq__
- Type hints enforced
- Easy to convert to dict with asdict()
- Immutable with frozen=True (optional)

**Benefit**: Less boilerplate, more maintainable.

## Detailed Argumentation

### Advantages

#### 1. Complete Independence ✅
**Benefit**: Logging and data export are fully decoupled.

**Impact**:
- Console logger can be enabled/disabled independently
- Data export can be enabled/disabled independently
- Verbose flag affects only console
- Debug flag affects only logging
- No interference between systems

**Example**:
```python
# Console off, data export on
engine = SimulationEngine(
    console_enabled=False,  # No console output
    csv_enabled=True,       # Still get CSV
    json_enabled=True       # Still get JSON
)
```

#### 2. Right Tool for Job ✅
**Benefit**: Each system does what it's designed for.

**Impact**:
- Logging module used for logging (its purpose)
- Custom collector used for data collection (its purpose)
- No conceptual mismatch
- Code expresses intent clearly

**Clarity**:
```python
# Clear: this is logging
self.console_logger.info("Starting simulation...")

# Clear: this is data collection
self.event_collector.collect(event)
```

#### 3. Easy to Extend ✅
**Benefit**: Add new exporters without touching logging.

**Impact**:
- New exporter = new class implementing Protocol
- No changes to logging system
- No changes to event collector
- Just add new exporter class

**Example**:
```python
# Add Parquet exporter
class ParquetExporter:
    def export(self, events: list[SimulationEvent], output_path: Path) -> None:
        # Implementation
        pass

# Use it
self.event_collector.export(ParquetExporter(), output_path)
```

#### 4. No Coupling ✅
**Benefit**: Systems don't interfere with each other.

**Impact**:
- Logging changes don't affect data export
- Data export changes don't affect logging
- Can test each system independently
- Can replace either system without affecting the other

**Independence**:
```python
# Change logging format - data export unaffected
logger = setup_console_logger(verbose=True)  # Changed
self.event_collector.collect(event)  # Still works exactly the same
```



#### 5. Clear Intent ✅
**Benefit**: Code clearly shows what's logging vs data collection.

**Impact**:
- Easy to understand for new developers
- No confusion about purpose
- Self-documenting code
- Follows principle of least surprise

**Readability**:
```python
def _emit_event(self, event: SimulationEvent) -> None:
    # Logging: human-readable message
    if self.console_logger:
        self.console_logger.info(f"{event.event_type}: {event.entity_id}")

    # Data collection: structured event
    self.event_collector.collect(event)
```

### Disadvantages

#### 1. Two Systems ⚠️
**Trade-off**: More code to maintain (two separate systems).

**Impact**:
- Two codebases instead of one
- Two sets of tests
- Two systems to understand
- More files in project

**Mitigation**:
- Each system is simpler than integrated solution
- Clear separation makes maintenance easier
- Total complexity is lower

**Reality**: This is a feature, not a bug. Separation of concerns is good design.

#### 2. Events Processed Twice ⚠️
**Trade-off**: Each event sent to both logger and collector.

**Impact**:
- Two function calls per event: logger.info() + collector.collect()
- Appears to be "duplicate work"
- Both operations are simple and fast

#### 3. Slightly More Code ⚠️
**Trade-off**: Two implementations instead of one.

**Impact**:
- More lines of code
- More files to navigate
- Slightly larger codebase

**Benefit**:
- Each implementation is simpler
- Easier to understand individually
- Lower cognitive load per component

### Verbose Flag Advantages

#### 1. Clean Separation ✅
**Benefit**: Verbose only affects console logger, never data export.

**Impact**:
- Data export files are always consistent
- CSV/JSON format never changes
- Dashboard can rely on stable format
- No surprises in exported data

**Guarantee**:
```python
# Verbose or not, CSV/JSON are IDENTICAL
engine1 = SimulationEngine(verbose=False)
engine2 = SimulationEngine(verbose=True)
# Both produce identical events.csv and events.json
```

#### 2. Simple Configuration ✅
**Benefit**: Single parameter passed to console logger setup.

**Impact**:
- Easy to understand
- Easy to implement
- No complex flag passing
- Clear code flow

**Simplicity**:
```python
self.console_logger = setup_console_logger(verbose=verbose)
# That's it. Event collector doesn't even know about verbose.
```

#### 3. No Side Effects ✅
**Benefit**: Event collector completely unaffected by verbose mode.

**Impact**:
- Data export is deterministic
- No hidden dependencies
- Easy to reason about
- Testable independently

**Independence**:
```python
# Verbose affects this
self.console_logger.info(message)  # Format changes

# Verbose does NOT affect this
self.event_collector.collect(event)  # Always the same
```

#### 4. Clear Intent ✅
**Benefit**: Verbose is for human output, data export remains structured.

**Impact**:
- Matches user expectations
- Verbose = more detail for humans
- Data export = always complete for machines
- No confusion about purpose

## Verbose Flag Handling

The `--verbose` flag from main.py affects **only the console logger**:

```python
# Non-verbose console output
INFO - Starting simulation...
INFO - train_arrival: TRAIN-001
INFO - Simulation complete

# Verbose console output
2024-01-15 14:30:45 - INFO - Starting simulation...
2024-01-15 14:30:46 - INFO - train_arrival: TRAIN-001
2024-01-15 14:35:12 - INFO - Simulation complete

# Data export (ALWAYS the same, unaffected by verbose)
events.csv: timestamp,event_type,entity_id,location,status,duration
events.json: [{"timestamp": 0.0, "event_type": "train_arrival", ...}]
```

**Key Benefit**: Verbose flag has **zero impact** on data export. CSV/JSON files remain consistent regardless of console verbosity.

## Migration Path

1. **Setup**: Create `core/logging/` with events.py, console.py, collector.py, exporters.py
2. **Integration**: Connect to main.py (verbose/debug flags) and SimulationEngine
3. **Migration**: Replace print() with logger.info(), add _emit_event() for data collection
4. **Validation**: Verify system independence and verbose flag doesn't affect data export

## Implementation Checklist

- [ ] Create `core/logging/` directory structure
- [ ] Implement `events.py` with SimulationEvent dataclass
- [ ] Implement `console.py` with setup_console_logger()
- [ ] Implement `collector.py` with EventCollector class
- [ ] Implement `exporters.py` with CSVExporter and JSONExporter
- [ ] Integrate with main.py CLI (verbose, debug flags)
- [ ] Update SimulationEngine with console_logger and event_collector
- [ ] Implement _emit_event() method in SimulationEngine
- [ ] Replace print() with logger.info() and _emit_event()
- [ ] Verify with: `uv run ruff format . && uv run mypy backend/src/ && uv run pytest`

## Conclusion

### Summary
This approach provides **complete separation of concerns** by using:
- **Python logging** for human-readable console/file output
- **Custom event collection** for structured data export (CSV/JSON)

These are fundamentally different concerns and deserve separate systems.

### Strengths
- ✅ Complete independence between logging and data export
- ✅ Right tool for the job (logging for logs, custom for data)
- ✅ Easy to extend with new exporters
- ✅ No coupling between systems
- ✅ Optimal performance for each use case
- ✅ Clear code intent
- ✅ Verbose flag cleanly handled (affects only console)
- ✅ Data export always consistent
- ✅ Simple testing (test each system independently)
- ✅ Flexible configuration

### Weaknesses
- ⚠️ Two systems to maintain (but each is simpler)
- ⚠️ Events processed twice (but both operations are fast)
- ⚠️ Slightly more code (but better organized)

### Recommendation
This is the **preferred option** for PopUp-Sim.

**Use this option because**:
- ✅ Clean separation of concerns
- ✅ Each system does what it's designed for
- ✅ Easy to understand and maintain
- ✅ Flexible and extensible
- ✅ Verbose flag handled correctly
- ✅ Data export is deterministic
- ✅ Performance is excellent
- ✅ Testing is straightforward
- ✅ Follows Python best practices
- ✅ Future-proof architecture

**This option provides**:
1. **For Users**: Clear console output with optional verbose mode
2. **For Dashboard Team**: Consistent CSV/JSON data, unaffected by console settings
3. **For Developers**: Clean architecture, easy to extend, simple to test
4. **For Project**: Maintainable code, follows standards, type-safe

### Next Steps
1. Review this ADR with team
2. Get approval from stakeholders
3. Begin Phase 1 implementation
4. Follow migration path outlined above
5. Monitor and iterate based on feedback
