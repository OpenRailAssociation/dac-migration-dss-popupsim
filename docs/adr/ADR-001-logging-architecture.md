# ADR-001: Logging Architecture for PopUp-Sim

## Quick Reference

**Decision:** Option 3 (Hybrid) | **Fallback:** Option 1 (if Option 3 rejected) | **Status:** Proposed

## Contents

1. [Context](#1-context)
2. [Architecture Options](#2-architecture-options)
3. [Comparison](#3-comparison)
4. [Decision](#4-decision)
5. [Consequences](#5-consequences)
6. [Alternatives Considered](#6-alternatives-considered)
7. [Implementation](#7-implementation)
8. [Migration Path](#8-migration-path)
9. [When to Revisit](#9-when-to-revisit)

## 1. Context

PopUp-Sim requires dual-output logging:
1. **Console feedback**: User-facing progress tracking (controlled by `--verbose` flag)
2. **Structured data export**: CSV/JSON for dashboard visualization (independent of console)

**Key Constraint**: Both outputs must be independently configurable.

## 2. Architecture Options

### Option 1: Single Logger + Multiple Handlers

```
┌─────────────────────────────────────┐
│      Simulation Code                │
│      logger.info(event)             │
│            ▼                        │
│   ┌────────────────┐                │
│   │ SINGLE LOGGER  │                │
│   └────────┬───────┘                │
│            │                        │
│   ┌────────┼────────┬──────┐       │
│   ▼        ▼        ▼      ▼       │
│ Console  File    CSV    JSON       │
│ Handler  Handler Handler Handler   │
└─────────────────────────────────────┘
```

**Principle**: ONE logger distributes to MULTIPLE handlers.

### Option 2: Multiple Independent Loggers

```
┌─────────────────────────────────────┐
│      Simulation Code                │
│      emit_event(event)              │
│            │                        │
│   ┌────────┼────────┬──────┐       │
│   ▼        ▼        ▼      ▼       │
│ Logger   Logger  Logger Logger     │
│ console  file    csv    json       │
│ (propagate=False for all)          │
└─────────────────────────────────────┘
```

**Principle**: FOUR independent loggers, each with own config.

### Option 3: Hybrid (Logging + Event Collection)

```
┌─────────────────────────────────────┐
│      Simulation Code                │
│      _emit_event(event)             │
│            │                        │
│      ┌─────┴─────┐                 │
│      ▼           ▼                 │
│  Console      Event                │
│  Logger       Collector            │
│  (logging)    (custom)             │
│      │           │                 │
│      ▼           ▼                 │
│   stdout    CSV/JSON               │
└─────────────────────────────────────┘
```

**Principle**: Separate systems for different concerns.

## 3. Comparison

### Feature Matrix

| Feature | Option 1 | Option 2 | Option 3 |
|---------|----------|----------|----------|
| **Independence** | ❌ Shared logger | ✅ Full | ✅ Complete |
| **Complexity** | ✅ Simple | ❌ 4 loggers | ⚠️ 2 systems |
| **Standard Python** | ✅ Yes | ✅ Yes | ⚠️ Hybrid |
| **Conceptual Fit** | ❌ Forced | ❌ Forced | ✅ Natural |
| **Extensibility** | ❌ Limited | ⚠️ Medium | ✅ Easy |
| **Verbose Handling** | ⚠️ Global | ⚠️ Per-logger | ✅ Clean |
| **Testing** | ✅ Simple | ❌ Complex | ✅ Simple |
| **Performance** | ⚠️ All handlers | ⚠️ All loggers | ✅ Optimal |

### Pros & Cons

| Aspect | Option 1 | Option 2 | Option 3 |
|--------|----------|----------|----------|
| **Pros** | • Standard pattern<br>• Simple setup<br>• Built-in features<br>• Familiar | • Full independence<br>• Clear separation<br>• Flexible config | • Right tool for job<br>• Complete independence<br>• Easy to extend<br>• Clear intent |
| **Cons** | • Tight coupling<br>• Forced paradigm<br>• Limited flexibility<br>• Verbose affects all | • Config complexity<br>• Must set propagate=False<br>• Still forced paradigm<br>• 4 loggers to manage | • Two systems<br>• Events processed twice<br>• Slightly more code |

### Verbose Flag Impact

| Option | Console | Data Export | Complexity |
|--------|---------|-------------|------------|
| **Option 1** | ✅ Controlled | ⚠️ Affected by logger level | Medium |
| **Option 2** | ✅ Per-logger | ⚠️ Must configure each | High |
| **Option 3** | ✅ Controlled | ✅ Unaffected | Low |

## 4. Decision

**Status:** Proposed
**Recommended:** Option 3 (Hybrid Approach)
**Fallback:** Option 1 (Single Logger + Multiple Handlers)

### Rationale

1. **Separation of Concerns**: Logging ≠ Data Export
   - Console output is for humans → use logging
   - CSV/JSON export is for machines → use custom collector

2. **Independence**: Systems don't interfere
   - Verbose flag affects only console
   - Data export always consistent
   - Each system evolves independently

3. **Extensibility**: Easy to add new exporters
   - New exporter = new class
   - No changes to logging system

4. **Clarity**: Code expresses intent
   ```python
   logger.info("message")      # Clear: logging
   collector.collect(event)    # Clear: data collection
   ```

### Fallback Recommendation

**If Option 3 is rejected: Choose Option 1** (simpler than Option 2)

<details>
<summary><b>Why Option 1 over Option 2?</b></summary>

**Advantages:**
- ✅ Simpler setup (1 logger vs 4 loggers)
- ✅ Standard Python pattern (familiar to all developers)
- ✅ Easier testing (mock 1 logger vs 4)
- ✅ Less code to maintain
- ✅ No propagation trap (`propagate=False` easy to forget)
- ✅ Coupling issue has workaround: set logger to DEBUG, control via handler levels

**Option 1 Workaround:**
```python
logger.setLevel(logging.DEBUG)  # Allow all events through
console_handler.setLevel(logging.INFO)  # User-facing
csv_handler.setLevel(logging.DEBUG)     # Complete data export
# Result: Independent handler control without tight coupling
```

**Conclusion:** Option 2's complexity burden (4 loggers, propagation settings, 4x configuration) outweighs Option 1's coupling issue (which has a simple workaround).

</details>

## 5. Consequences

**Note:** These consequences apply to **Option 3 (Hybrid Approach)** - the recommended solution.

### Positive
- ✅ Clean architecture with clear responsibilities
- ✅ Verbose flag cleanly handled (console only)
- ✅ Data export deterministic and consistent
- ✅ Easy to test each system independently
- ✅ Simple to extend with new exporters
- ✅ Type-safe with mypy compliance

### Negative
- ⚠️ Two systems to maintain (but each simpler)
- ⚠️ Events processed twice (but operations fast)
- ⚠️ Slightly more code (but better organized)

### Neutral
- Each system can evolve independently
- Team needs to understand both systems
- More files but clearer organization

## 6. Alternatives Considered

### Option 1: Single Logger + Multiple Handlers (Fallback Choice)

<details>
<summary><b>Why Not Primary Choice?</b></summary>

**Reasons:**
- **Tight Coupling**: All handlers share same logger level. If logger is set to WARNING, INFO messages never reach ANY handler, even if handler level is DEBUG.
- **Forced Paradigm**: CSV/JSON export conceptually not "logging" but forced into logging framework via custom handlers.
- **Limited Flexibility**: Hard to add non-logging outputs (e.g., database, message queue) without implementing Handler interface.
- **Verbose Flag Issue**: Affects entire logging system; cannot have verbose console + compact file independently without complex formatter management.

**Example Problem:**
```python
logger.setLevel(logging.WARNING)  # Blocks all INFO messages
console_handler.setLevel(logging.INFO)  # Never receives INFO
csv_handler.setLevel(logging.DEBUG)  # Never receives DEBUG
# Result: Data export incomplete
```

</details>

### Option 2: Multiple Independent Loggers (Rejected)

<details>
<summary><b>Why Rejected?</b></summary>

**Reasons:**
- **Configuration Complexity**: Must configure 4 separate loggers (console, file, csv, json), each with own setup method.
- **Propagation Trap**: Must remember `propagate=False` on every logger, otherwise duplicate messages appear. Easy to forget, hard to debug.
- **Still Forced Paradigm**: CSV/JSON "loggers" don't actually log—they write files directly. Using logging.Logger for non-logging is misleading.
- **Testing Overhead**: Must mock 4 loggers instead of 1, increasing test complexity.
- **Maintenance Burden**: 4x configuration code, 4x potential bugs, 4x documentation needed.

**Example Problem:**
```python
# Forgot propagate=False
console_logger = logging.getLogger('PopupSim.console')
# Result: Messages appear in both console_logger AND root logger (duplicate output)

# CSV "logger" that doesn't log
csv_logger = logging.getLogger('PopupSim.csv')  # Misleading name
self.csv_writer.writerow(data)  # Direct file write, not logging
```

</details>

## 7. Implementation

**Note:** This implementation is for **Option 3 (Hybrid Approach)** - the recommended solution.

### Core Components

```python
# 1. Event Model
@dataclass
class SimulationEvent:
    timestamp: float
    event_type: str
    entity_id: str
    location: str
    status: str

# 2. Console Logger
def setup_console_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger('PopupSim')
    # Configure based on verbose flag
    return logger

# 3. Event Collector
class EventCollector:
    def collect(self, event: SimulationEvent) -> None:
        self.events.append(event)

    def export(self, exporter: DataExporter, path: Path) -> None:
        exporter.export(self.events, path)

# 4. Usage
def _emit_event(self, event: SimulationEvent) -> None:
    if self.console_logger:
        self.console_logger.info(f"{event.event_type}: {event.entity_id}")
    self.event_collector.collect(event)
```

### Simulation Prototype

```python
# main.py
def main(verbose: bool = False, scenario: str = "default") -> None:
    engine = SimulationEngine(verbose=verbose)
    engine.run()

# simulation/engine.py
class SimulationEngine:
    def __init__(self, verbose: bool = False) -> None:
        self.console_logger = setup_console_logger(verbose=verbose)
        self.event_collector = EventCollector()

    def run(self) -> None:
        # Start simulation
        self.console_logger.info("Starting simulation...")

        # Train arrives
        event = SimulationEvent(
            timestamp=10.5,
            event_type="train_arrival",
            entity_id="TRAIN-001",
            location="WORKSHOP-A",
            status="arrived"
        )
        self._emit_event(event)

        # Wagon conversion
        event = SimulationEvent(
            timestamp=25.0,
            event_type="wagon_conversion",
            entity_id="WAGON-042",
            location="TRACK-3",
            status="started"
        )
        self._emit_event(event)

        # End simulation
        self.console_logger.info("Simulation complete")

        # Export data
        self.event_collector.export(CSVExporter(), Path("output/events.csv"))
        self.event_collector.export(JSONExporter(), Path("output/events.json"))
```

**CLI Usage:**
```bash
# Non-verbose mode
$ python main.py --scenario default
INFO - Starting simulation...
INFO - train_arrival: TRAIN-001
INFO - wagon_conversion: WAGON-042
INFO - Simulation complete

# Verbose mode
$ python main.py --scenario default --verbose
2024-01-15 14:30:45 - INFO - Starting simulation...
2024-01-15 14:30:46 - INFO - train_arrival: TRAIN-001
2024-01-15 14:31:12 - INFO - wagon_conversion: WAGON-042
2024-01-15 14:35:12 - INFO - Simulation complete
```

**Data Export (same for both modes):**
```csv
# events.csv
timestamp,event_type,entity_id,location,status
10.5,train_arrival,TRAIN-001,WORKSHOP-A,arrived
25.0,wagon_conversion,WAGON-042,TRACK-3,started
```

```json
# events.json
[{"timestamp": 10.5, "event_type": "train_arrival", ...}, ...]
```

### File Structure

```
core/logging/
├── events.py       # SimulationEvent dataclass
├── console.py      # setup_console_logger()
├── collector.py    # EventCollector class
└── exporters.py    # CSVExporter, JSONExporter
```

## 8. Migration Path

**Note:** This migration path is for **Option 3 (Hybrid Approach)** - the recommended solution.

1. Create `core/logging/` structure
2. Implement event model and systems
3. Integrate with main.py (verbose/debug flags)
4. Replace print() with logger.info() and _emit_event()
5. Validate with test scenarios


## 9. When to Revisit

This decision should be revisited if:

- **Performance Issues**: Dual event processing (logger + collector) causes measurable performance degradation
- **New Requirements**: Need for additional output formats (database, message queue, real-time streaming)
- **Team Feedback**: After 3 months of usage, team reports significant maintenance burden
- **Scale Changes**: Simulation size exceeds 100K events, causing memory issues with in-memory collection
- **Technology Changes**: New Python logging features or libraries that better address the requirements

**Review Schedule:** 3 months after implementation
