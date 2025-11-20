# ADR-001 Option 2: Multiple Independent Loggers

## Metadata
- **Status**: Considered
- **Date**: 2024-01-15
- **Decision Makers**: Backend Development Team
- **Related Options**: [Option 1](ADR-001-option1-single-logger-multiple-handlers.md), [Option 3](ADR-001-option3-hybrid-approach.md)

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
Should we use **multiple independent logger instances**, each dedicated to a specific output purpose?

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Simulation Code                            │
│                                                              │
│                  emit_event(event)                           │
│                         │                                    │
│         ┌───────────────┼───────────────┬──────────────┐    │
│         │               │               │              │    │
│         ▼               ▼               ▼              ▼    │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐│
│  │   LOGGER    │ │   LOGGER    │ │  LOGGER  │ │  LOGGER  ││
│  │  'console'  │ │   'file'    │ │  'csv'   │ │  'json'  ││
│  │             │ │             │ │          │ │          ││
│  │ propagate=  │ │ propagate=  │ │propagate=│ │propagate=││
│  │   False     │ │   False     │ │  False   │ │  False   ││
│  └──────┬──────┘ └──────┬──────┘ └────┬─────┘ └────┬─────┘│
│         │               │              │            │      │
│         ▼               ▼              ▼            ▼      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐ ┌──────────┐ │
│  │ Console  │   │   File   │   │   CSV    │ │   JSON   │ │
│  │ Handler  │   │ Handler  │   │  Writer  │ │ Collector│ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘ └────┬─────┘ │
│       │              │              │            │        │
│       ▼              ▼              ▼            ▼        │
│   stdout        app.log       events.csv   events.json   │
└─────────────────────────────────────────────────────────────┘

Key: FOUR independent loggers, each with its own handler
```

### Key Principle
**MULTIPLE independent logger instances** (PopupSim.console, PopupSim.file, PopupSim.csv, PopupSim.json). Each logger is completely separate with its own configuration. Code must explicitly call each logger.

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

    def to_console_message(self) -> str:
        """Format for console output."""
        return f"[{self.timestamp:.2f}] {self.event_type}: {self.entity_id} at {self.location}"

    def to_csv_row(self) -> list[Any]:
        """Format as CSV row."""
        return [self.timestamp, self.event_type, self.entity_id,
                self.location, self.status, self.duration]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
```

### 2. Logger Manager (`core/logging/manager.py`)

```python
"""Multi-logger management system."""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

from .events import SimulationEvent


class LoggerManager:
    """Manages multiple independent loggers."""

    def __init__(
        self,
        output_dir: Path = Path('output'),
        console_enabled: bool = True,
        verbose: bool = False,
        csv_enabled: bool = True,
        json_enabled: bool = True
    ) -> None:
        """Initialize logger manager."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

        self.console_logger = self._setup_console_logger() if console_enabled else None
        self.file_logger = self._setup_file_logger()

        # CSV setup
        self.csv_enabled = csv_enabled
        if csv_enabled:
            self.csv_file = open(output_dir / 'events.csv', 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(['timestamp', 'event_type', 'entity_id',
                                     'location', 'status', 'duration'])

        # JSON setup
        self.json_enabled = json_enabled
        self.json_events: list[dict[str, Any]] = []

    def _setup_console_logger(self) -> logging.Logger:
        """Setup console logger."""
        logger = logging.getLogger('PopupSim.console')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.propagate = False

        handler = logging.StreamHandler(sys.stdout)

        if self.verbose:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter('%(levelname)s - %(message)s')

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _setup_file_logger(self) -> logging.Logger:
        """Setup file logger."""
        logger = logging.getLogger('PopupSim.file')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.propagate = False

        handler = logging.FileHandler(self.output_dir / 'simulation.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_event(self, event: SimulationEvent) -> None:
        """Log event to all enabled loggers."""
        if self.console_logger:
            self.console_logger.info(event.to_console_message())

        if self.file_logger:
            self.file_logger.debug(f"{event.event_type} | {event.entity_id}")

        if self.csv_enabled:
            self.csv_writer.writerow(event.to_csv_row())
            self.csv_file.flush()

        if self.json_enabled:
            self.json_events.append(event.to_dict())

    def close(self) -> None:
        """Close all loggers and flush data."""
        if self.csv_enabled:
            self.csv_file.close()

        if self.json_enabled and self.json_events:
            json_path = self.output_dir / 'events.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_events, f, indent=2)
```

## Design Decisions

### Core Architecture Decision
**Use FOUR independent logger instances**, each with its own configuration, handler, and purpose:
1. `PopupSim.console` - Console output
2. `PopupSim.file` - Debug file logs
3. `PopupSim.csv` - CSV data export (conceptual)
4. `PopupSim.json` - JSON data export (conceptual)

### Logger Responsibilities
Each logger is completely independent:
- Own namespace in logging hierarchy
- Own handler and formatter
- Own log level
- Own enable/disable flag
- `propagate = False` to prevent parent logger interference

### Data Flow
```python
Simulation Event → emit_event(event)
                      ↓
        ┌─────────────┼─────────────┬─────────────┐
        ↓             ↓             ↓             ↓
   console_logger file_logger   csv_logger    json_logger
   .info(msg)     .debug(msg)   (direct CSV)  (collect)
        ↓             ↓             ↓             ↓
     stdout       app.log      events.csv    events.json
```

### Key Design Choices

#### 1. Logger Namespace Hierarchy
**Decision**: Use hierarchical names (PopupSim.console, PopupSim.file, etc.)

**Rationale**:
- Clear organization in logging system
- Easy to identify logger purpose
- Follows Python logging conventions
- Prevents naming conflicts

**Implementation**:
```python
console_logger = logging.getLogger('PopupSim.console')
file_logger = logging.getLogger('PopupSim.file')
csv_logger = logging.getLogger('PopupSim.csv')
json_logger = logging.getLogger('PopupSim.json')
```

#### 2. Propagation Disabled
**Decision**: Set `propagate = False` on all loggers.

**Rationale**:
- Prevents events from bubbling to parent loggers
- Avoids duplicate log messages
- Ensures complete independence

**Critical**: Without this, events would propagate to root logger and appear multiple times.

```python
logger.propagate = False  # MUST set this
```

#### 3. Direct File Writing for CSV/JSON
**Decision**: CSV/JSON loggers don't actually "log" - they write directly to files.

**Rationale**:
- Logging paradigm doesn't fit data export well
- Direct file writing is more natural
- Better performance for structured data
- Clearer code intent

**Trade-off**: Using "logger" name for non-logging is conceptually awkward.

#### 4. Manager Class Coordination
**Decision**: LoggerManager class coordinates all loggers.

**Rationale**:
- Single point of configuration
- Manages logger lifecycle
- Handles file closing and flushing
- Simplifies usage in simulation code

## Detailed Argumentation

### Advantages

#### 1. Complete Independence ✅
**Benefit**: Each logger has its own configuration with zero interference.

**Impact**:
- Console logger can be INFO level
- File logger can be DEBUG level
- CSV/JSON can be always-on
- No shared state between loggers

**Example**:
```python
console_logger.setLevel(logging.INFO)  # User-facing
file_logger.setLevel(logging.DEBUG)    # Developer-facing
# No conflict!
```

#### 2. Clear Separation ✅
**Benefit**: Each logger has single, clear responsibility.

**Impact**:
- Easy to understand code
- Clear which logger does what
- No confusion about handler purpose
- Follows Single Responsibility Principle

**Code Clarity**:
```python
self.console_logger.info("User message")  # Clear: goes to console
self.file_logger.debug("Debug info")      # Clear: goes to file
```

#### 3. Flexible Configuration ✅
**Benefit**: Each logger can have completely different settings.

**Impact**:
- Different log levels per logger
- Different formatters per logger
- Different handlers per logger
- Independent enable/disable

**Example**:
```python
# Console: simple format, INFO level
console_logger: INFO, format='%(message)s'

# File: detailed format, DEBUG level
file_logger: DEBUG, format='%(asctime)s - %(funcName)s:%(lineno)d - %(message)s'
```

#### 4. Namespace Isolation ✅
**Benefit**: No naming conflicts in logging hierarchy.

**Impact**:
- Clear logger identification
- Easy to filter logs by logger name
- No accidental logger reuse
- Follows Python logging best practices

**Hierarchy**:
```
PopupSim (root)
  ├── console
  ├── file
  ├── csv
  └── json
```

### Disadvantages

#### 1. Still Coupled to Logging ❌
**Problem**: CSV/JSON export forced into logging paradigm even though it's not really logging.

**Impact**:
- Conceptual mismatch: data export ≠ logging
- Using logging.Logger for non-logging tasks
- Awkward code that doesn't express intent
- Misleading for future developers

**Example**:
```python
# This "logger" doesn't actually log - it writes CSV
self.csv_logger = logging.getLogger('PopupSim.csv')  # Misleading name
```

#### 2. Configuration Complexity ❌
**Problem**: Must configure four separate loggers.

**Impact**:
- More setup code required
- More parameters to manage
- More potential for configuration errors
- Harder to maintain consistency

**Code Volume**:
```python
# Must setup each logger individually
self._setup_console_logger()
self._setup_file_logger()
self._setup_csv_logger()
self._setup_json_logger()
# 4x the configuration code
```

#### 3. Propagation Issues ❌
**Problem**: Must remember to set `propagate = False` on every logger.

**Impact**:
- Easy to forget
- Causes duplicate messages if forgotten
- Hard to debug when it happens
- Not obvious to new developers

**Common Bug**:
```python
logger = logging.getLogger('PopupSim.console')
# Forgot: logger.propagate = False
# Result: Messages appear twice (console + root logger)
```

#### 4. Awkward Data Export ❌
**Problem**: CSV/JSON "loggers" don't actually log.

**Impact**:
- Misleading code structure
- Logger used for file writing
- Doesn't leverage logging features
- Better done with custom classes

**Reality**:
```python
# This isn't logging, it's just file writing
if self.csv_enabled:
    self.csv_writer.writerow(event.to_csv_row())  # Direct file write
    # Why use a "logger" for this?
```



#### 5. Verbose Flag Complexity ❌
**Problem**: Must pass verbose flag to each logger setup individually.

**Impact**:
- More parameters to pass around
- More configuration code
- Easy to forget for one logger
- Inconsistent behavior if forgotten

**Configuration**:
```python
def __init__(self, verbose: bool = False):
    self.verbose = verbose
    self.console_logger = self._setup_console_logger()  # Uses self.verbose
    self.file_logger = self._setup_file_logger()        # Might also use it
    # Must remember to use verbose in each setup method
```

## Verbose Flag Handling

The `--verbose` flag from main.py can be handled independently per logger:

```python
# Console logger can be verbose
self.console_logger = self._setup_console_logger(verbose=True)

# File logger can have different format
self.file_logger = self._setup_file_logger(verbose=False)
```

**Advantage**: Each logger can have independent verbose settings. Console can be verbose while file logs remain compact.

**Disadvantage**: Must pass verbose flag to each logger setup method, increasing configuration complexity.

## Migration Path

1. **Setup**: Create `core/logging/` with events.py and manager.py (LoggerManager class)
2. **Integration**: Connect to main.py (verbose/debug flags) and SimulationEngine
3. **Migration**: Replace print() with manager.log_event() calls
4. **Validation**: Verify logger independence and propagate=False settings

## Implementation Checklist

- [ ] Create `core/logging/` directory structure
- [ ] Implement `events.py` with SimulationEvent dataclass
- [ ] Implement `manager.py` with LoggerManager class
- [ ] Implement _setup_console_logger() and _setup_file_logger() with propagate=False
- [ ] Implement CSV/JSON writing logic in LoggerManager
- [ ] Integrate with main.py CLI (verbose, debug flags)
- [ ] Update SimulationEngine to use LoggerManager
- [ ] Replace print() with manager.log_event()
- [ ] Verify with: `uv run ruff format . && uv run mypy backend/src/ && uv run pytest`

## Conclusion

### Summary
This approach uses **multiple independent logger instances**, each dedicated to a specific output. It provides better independence than Option 1 but still forces data export into the logging paradigm.

### Strengths
- ✅ Complete independence between loggers
- ✅ Clear separation of concerns
- ✅ Flexible configuration per logger
- ✅ Namespace isolation
- ✅ Verbose flag can be per-logger

### Weaknesses
- ❌ Still couples data export to logging
- ❌ Configuration complexity (4 loggers)
- ❌ Must remember propagate=False
- ❌ CSV/JSON "loggers" don't actually log
- ❌ Testing complexity (mock 4 loggers)
- ❌ More code to maintain

### Recommendation
This approach provides **better independence** than Option 1 but **doesn't solve the fundamental problem**: data export is not logging. The multiple loggers add complexity without addressing the conceptual mismatch.

**Use this option if**:
- Complete logger independence is critical
- Team comfortable with multiple logger management
- Willing to accept logging paradigm for data export
- Configuration complexity is acceptable

**Avoid this option if**:
- Data export is primary concern
- Want conceptually clean separation
- Prefer simpler configuration
- Team unfamiliar with propagate settings
