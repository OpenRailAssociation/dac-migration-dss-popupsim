# ADR-001 Option 1: Single Logger with Multiple Handlers

## Metadata
- **Status**: Considered
- **Date**: 2024-01-15
- **Decision Makers**: Backend Development Team
- **Related Options**: [Option 2](ADR-001-option2-multiple-loggers.md), [Option 3](ADR-001-option3-hybrid-approach.md)

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
Should we use a **single logger with multiple handlers** to distribute events to different outputs?

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Simulation Code                            │
│                                                              │
│                  logger.info(event)                          │
│                         │                                    │
│                         ▼                                    │
│              ┌──────────────────────┐                       │
│              │   SINGLE LOGGER      │                       │
│              │  logging.Logger      │                       │
│              │  (name='PopupSim')   │                       │
│              └──────────┬───────────┘                       │
│                         │                                    │
│         ┌───────────────┼───────────────┬──────────┐        │
│         │               │               │          │        │
│         ▼               ▼               ▼          ▼        │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐ ┌─────────┐ │
│  │  Console   │  │    File    │  │   CSV    │ │  JSON   │ │
│  │  Handler   │  │  Handler   │  │ Handler  │ │ Handler │ │
│  └─────┬──────┘  └─────┬──────┘  └────┬─────┘ └────┬────┘ │
│        │               │              │            │        │
│        ▼               ▼              ▼            ▼        │
│     stdout        app.log       events.csv   events.json   │
└─────────────────────────────────────────────────────────────┘

Key: ONE logger distributes to MULTIPLE handlers
```

### Key Principle
**ONE logger instance** with **MULTIPLE handlers** attached. All handlers receive the same LogRecord and process it independently. The logger acts as a central distribution point.

## Implementation

### 1. Event Model (`core/logging/events.py`)

```python
"""Simulation event models."""

from dataclasses import dataclass, field, asdict
from typing import Any
import json


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

    def to_log_message(self) -> str:
        """Convert to human-readable log message."""
        return f"[{self.timestamp:.2f}] {self.event_type}: {self.entity_id} at {self.location}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for structured export."""
        return asdict(self)
```

### 2. Custom Handlers (`core/logging/handlers.py`)

```python
"""Custom logging handlers for structured data export."""

import csv
import json
import logging
from pathlib import Path
from typing import Any


class CSVHandler(logging.Handler):
    """Handler that writes events to CSV file."""

    def __init__(self, filepath: Path) -> None:
        """Initialize CSV handler."""
        super().__init__()
        self.filepath = filepath
        self.file = open(filepath, 'w', newline='', encoding='utf-8')
        self.writer: csv.DictWriter[str, Any] | None = None
        self.headers_written = False

    def emit(self, record: logging.LogRecord) -> None:
        """Write log record to CSV."""
        try:
            if hasattr(record, 'event_data'):
                event_dict = record.event_data

                if not self.headers_written:
                    self.writer = csv.DictWriter(self.file, fieldnames=event_dict.keys())
                    self.writer.writeheader()
                    self.headers_written = True

                if self.writer:
                    self.writer.writerow(event_dict)
                    self.file.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close file handler."""
        self.file.close()
        super().close()


class JSONHandler(logging.Handler):
    """Handler that writes events to JSON file."""

    def __init__(self, filepath: Path) -> None:
        """Initialize JSON handler."""
        super().__init__()
        self.filepath = filepath
        self.events: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Collect log record for JSON export."""
        try:
            if hasattr(record, 'event_data'):
                self.events.append(record.event_data)
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Write all events to JSON file."""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2)
        super().close()
```

### 3. Logger Setup (`core/logging/setup.py`)

```python
"""Logging system setup."""

import logging
import sys
from pathlib import Path

from .handlers import CSVHandler, JSONHandler
from .events import SimulationEvent


def setup_logger(
    name: str = 'PopupSim',
    console_level: str = 'INFO',
    verbose: bool = False,
    enable_csv: bool = True,
    enable_json: bool = True,
    output_dir: Path = Path('output')
) -> logging.Logger:
    """Configure single logger with multiple handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler with verbose formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))

    if verbose:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(output_dir / 'simulation.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # CSV handler
    if enable_csv:
        csv_handler = CSVHandler(output_dir / 'events.csv')
        csv_handler.setLevel(logging.DEBUG)
        logger.addHandler(csv_handler)

    # JSON handler
    if enable_json:
        json_handler = JSONHandler(output_dir / 'events.json')
        json_handler.setLevel(logging.DEBUG)
        logger.addHandler(json_handler)

    return logger


def log_event(logger: logging.Logger, event: SimulationEvent) -> None:
    """Log simulation event to all handlers."""
    extra = {'event_data': event.to_dict()}
    logger.info(event.to_log_message(), extra=extra)
```

## Design Decisions

### Core Architecture Decision
**Use ONE logger instance** (`logging.Logger`) with **MULTIPLE handlers** attached. Each handler processes the same LogRecord independently.

### Handler Responsibilities
1. **ConsoleHandler**: User-facing output to stdout
2. **FileHandler**: Developer debug logs to file
3. **CSVHandler**: Structured data export to CSV
4. **JSONHandler**: Structured data export to JSON

### Data Flow
```python
Simulation Event → logger.info(msg, extra={'event_data': dict})
                      ↓
                  LogRecord created
                      ↓
        ┌─────────────┼─────────────┬─────────────┐
        ↓             ↓             ↓             ↓
   Console       File          CSV           JSON
   Handler       Handler       Handler       Handler
```

### Key Design Choices

#### 1. Extra Field for Structured Data
**Decision**: Use `extra={'event_data': dict}` to attach structured data to LogRecord.

**Rationale**:
- Standard Python logging pattern
- Allows handlers to access both message and structured data
- No modification to logging module needed

**Implementation**:
```python
event_dict = event.to_dict()
logger.info(event.to_log_message(), extra={'event_data': event_dict})
```

#### 2. Custom Handlers for Data Export
**Decision**: Implement custom CSVHandler and JSONHandler classes.

**Rationale**:
- Built-in handlers only support text output
- Need structured data export (CSV/JSON)
- Must implement logging.Handler interface

**Trade-off**: Custom code to maintain, but necessary for requirements.

#### 3. Single Logger Level
**Decision**: Set logger level to DEBUG, control output via handler levels.

**Rationale**:
- Logger level acts as global minimum
- Each handler can filter independently
- Console can be INFO while file is DEBUG

**Limitation**: Cannot have different logger levels per handler type.

## Detailed Argumentation

### Advantages

#### 1. Standard Python Approach ✅
- Uses `logging` module as designed by Python core team
- Well-documented in Python docs
- Familiar to all Python developers
- No external dependencies
- Battle-tested in production systems

**Example**: Django, Flask, and most Python frameworks use this pattern.

#### 2. Unified Configuration ✅
- Single logger instance to configure
- One place to set log levels
- Centralized error handling
- Simple initialization code

**Code Impact**:
```python
# Simple setup
logger = setup_logger(name='PopupSim', verbose=True)

# Use everywhere
logger.info("message")
```

#### 3. Built-in Features ✅
- **Thread-safety**: Automatic locking for concurrent access
- **Exception handling**: Built-in error recovery
- **Log level filtering**: Per-handler level control
- **Formatters**: Flexible message formatting
- **Rotation**: File rotation via RotatingFileHandler

#### 4. Simple Testing ✅
- Mock single logger instance
- Standard pytest patterns apply
- Use `caplog` fixture for assertions

**Test Example**:
```python
def test_logging(caplog):
    with caplog.at_level(logging.INFO):
        logger.info("test")
    assert "test" in caplog.text
```

### Disadvantages

#### 1. Tight Coupling ❌
**Problem**: All handlers share the same logger configuration.

**Impact**:
- Cannot have completely independent configurations
- Logger level affects all handlers
- Changing logger affects all outputs

**Example**:
```python
# If logger level is WARNING, INFO messages are lost
logger.setLevel(logging.WARNING)
logger.info("This won't reach ANY handler")
```

#### 2. Forced Paradigm ❌
**Problem**: Data export forced into logging framework.

**Impact**:
- CSV/JSON export conceptually not "logging"
- Must use LogRecord for data transport
- Awkward fit for pure data collection

**Example**:
```python
# Using logging for data export feels forced
logger.info("message", extra={'event_data': {...}})  # Awkward
```

#### 3. Limited Flexibility ❌
**Problem**: Hard to add non-logging outputs.

**Impact**:
- New output types must implement Handler interface
- Cannot easily integrate non-logging systems
- Locked into logging architecture

**Example**: Adding database export requires custom Handler, not natural fit.



#### 4. Configuration Complexity ❌
**Problem**: Handler interactions can be confusing.

**Impact**:
- Must understand handler vs logger levels
- Propagation settings can cause issues
- Formatter conflicts possible

**Common Bug**:
```python
# Logger level too high - handlers never receive events
logger.setLevel(logging.ERROR)  # Blocks INFO/DEBUG
console_handler.setLevel(logging.DEBUG)  # Never receives DEBUG
```

#### 5. Verbose Flag Limitation ❌
**Problem**: Verbose affects formatter, but all handlers see same logger.

**Impact**:
- Cannot have verbose console + compact file log independently
- Verbose mode affects entire logging system
- Must choose one format for all

**Workaround**: Set formatter per handler, but verbose flag still global.

## Verbose Flag Handling

### Integration with main.py

The `--verbose` flag from main.py controls console output detail level:

```python
# main.py
def main(verbose: bool = False, debug: str = 'INFO') -> None:
    logger = setup_logger(
        name='PopupSim',
        console_level=debug,
        verbose=verbose,
        enable_csv=True,
        enable_json=True,
        output_dir=Path('output')
    )
```

### Output Examples

#### Non-Verbose Mode (`--verbose` not set)
```
INFO - Starting simulation...
INFO - Train TRAIN-001 arrived at STATION-A
INFO - Wagon WAGON-042 conversion started
INFO - Simulation complete
```

#### Verbose Mode (`--verbose` flag set)
```
2024-01-15 14:30:45 - PopupSim - INFO - Starting simulation...
2024-01-15 14:30:46 - PopupSim - INFO - Train TRAIN-001 arrived at STATION-A
2024-01-15 14:31:12 - PopupSim - INFO - Wagon WAGON-042 conversion started
2024-01-15 14:35:12 - PopupSim - INFO - Simulation complete
```

### Implementation Detail

```python
def setup_logger(verbose: bool = False, ...) -> logging.Logger:
    # Console handler formatting based on verbose flag
    if verbose:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')

    console_handler.setFormatter(console_formatter)
```

### Limitation Analysis

**Problem**: Verbose flag affects console formatter, but all handlers share same logger.

**Impact**:
- Cannot have verbose console + compact file log independently
- File handler also affected if using same formatter
- Must set different formatters per handler

**Workaround**:
```python
# Console: verbose-aware
console_handler.setFormatter(console_formatter)  # Based on verbose flag

# File: always detailed
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
file_handler.setFormatter(file_formatter)  # Independent format
```

**Conclusion**: Workaround exists but adds complexity. Each handler needs explicit formatter configuration.

## Migration Path

1. **Setup**: Create `core/logging/` with events.py, handlers.py, setup.py
2. **Integration**: Connect to main.py (verbose/debug flags) and SimulationEngine
3. **Migration**: Replace print() with logger.info() and log_event() calls
4. **Validation**: Verify all outputs work correctly with real scenarios

## Implementation Checklist

- [ ] Create `core/logging/` directory structure
- [ ] Implement `events.py` with SimulationEvent dataclass
- [ ] Implement `handlers.py` with CSVHandler and JSONHandler
- [ ] Implement `setup.py` with setup_logger() and log_event()
- [ ] Integrate with main.py CLI (verbose, debug flags)
- [ ] Update SimulationEngine to use logger
- [ ] Replace print() with logger.info() and log_event()
- [ ] Verify with: `uv run ruff format . && uv run mypy backend/src/ && uv run pytest`

## Conclusion

### Summary
This approach uses **Python's standard logging module with multiple handlers** attached to a single logger instance. It's the most conventional Python approach.

### Strengths
- ✅ Standard Python pattern
- ✅ Well-documented and understood
- ✅ Built-in features (thread-safety, error handling)
- ✅ Simple testing with pytest

### Weaknesses
- ❌ Tight coupling between handlers
- ❌ Data export forced into logging paradigm
- ❌ Limited flexibility for non-logging outputs
- ❌ Verbose flag affects all handlers
- ❌ Performance overhead for all handlers

### Recommendation
This approach works well for **traditional logging use cases** but feels **forced for structured data export**. The tight coupling between console output and data collection makes independent configuration difficult.

**Use this option if**:
- Team is very familiar with Python logging
- Standard approach is highly valued
- Data export requirements are simple
- Tight coupling is acceptable

**Avoid this option if**:
- Need complete independence between outputs
- Data export is primary concern
- Flexibility for future extensions is important
- Performance is critical
