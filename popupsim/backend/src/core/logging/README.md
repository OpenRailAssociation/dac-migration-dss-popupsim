# PopUpSim Enterprise Logging System

## Overview

Logging system with protocol-based dependency injection, structured logging,
multiple output formats, async support, and seamless integration with issue
tracking and i18n systems.

## Configuration Classes

### FileConfig
Groups file logging settings:
```python
@dataclass
class FileConfig:
    path: Path | None = None              # Log file path
    max_bytes: int = 50 * 1024 * 1024     # 50MB rotation size
    backup_count: int = 5                 # Number of backup files
```

### LoggingConfig
Complete logging system configuration:
```python
@dataclass
class LoggingConfig:
    level: int = logging.INFO                    # Logging level
    format_type: str = 'structured'              # "structured" or "json"
    console_output: bool = True                  # Enable console output
    file: FileConfig | None = None               # File logging config
    translator: Translator | None = None         # i18n translator (works with all formats)
```

## Quick Start

```python
from core.logging import (
    get_logger, get_async_logger, configure_logging,
    LoggingConfig, FileConfig, FormatType
)
from pathlib import Path
import logging

# Configure logging system
configure_logging(LoggingConfig(
    level=logging.INFO,
    format_type=FormatType.STRUCTURED,
    file=FileConfig(path=Path("logs/app.log")),
    console_output=True
))

# Sync logging with dependency injection
issue_tracker = MyIssueTracker()
translator = MyTranslator()
logger = get_logger(__name__, issue_tracker=issue_tracker, translator=translator)

# Async logging with identical API
async_logger = get_async_logger(__name__, issue_tracker=issue_tracker, translator=translator)

# Basic logging
# Sync logging
logger.info("Application started")
logger.debug("Processing config", config_file="scenario.json")
logger.error("Validation failed", error_count=5)
logger.info("user.login.success", translate=True, user_id="123")

# Async logging (identical API)
await async_logger.info("Async operation completed")
await async_logger.error("Async validation failed", error_count=5)
await async_logger.info("user.logout", translate=True, user_id="123")
```

## Dependency Injection

The logging system uses pure dependency injection without global state:

```python
# Create dependencies
issue_tracker = MyIssueTracker()
translator = MyTranslator()

# Inject dependencies explicitly
logger = get_logger(__name__, issue_tracker=issue_tracker, translator=translator)

# Or use without dependencies
logger = get_logger(__name__)  # Basic logging only

# All logging operations are thread-safe
logger.info("Message from thread", thread_id=threading.current_thread().ident)
```

## Protocol-Based Architecture

The logging system uses protocols to avoid direct dependencies on issue tracking and i18n systems:

```python
# When systems become available, inject them directly
issue_tracker = MyIssueTracker()
translator = MyTranslator()

# Logger gains capabilities through dependency injection
logger = get_logger(__name__, issue_tracker=issue_tracker, translator=translator)
logger.log_issue("Validation failed", issue_obj)  # Now works
```

## Output Formats

Two main formats, both supporting i18n when translator is configured:

### 1. Structured Format (Default)
Human-readable with structured data (UTC timestamps):
```
# Without translation
[2025-10-30 19:30:45] INFO     core.config: Configuration loaded | {"file": "scenario.json", "sections": 4}

# With translation (translate=True)
[2025-10-30 19:30:45] INFO     core.config: Konfiguration geladen | {"file": "scenario.json", "sections": 4}
```

### 2. JSON Format
Machine-readable structured logs with UTC timestamps:
```json
// Without translation
{
  "timestamp": "2025-10-30T19:50:45.123456+00:00",
  "level": "INFO",
  "logger": "core.config",
  "message": "Configuration loaded",
  "module": "config",
  "function": "load_config",
  "line": 45,
  "file": "scenario.json",
  "sections": 4
}

// With translation (translate=True)
{
  "timestamp": "2025-10-30T19:50:45.123456+00:00",
  "level": "INFO",
  "logger": "core.config",
  "message": "Konfiguration geladen",
  "file": "scenario.json",
  "sections": 4
}
```

### I18n Configuration
Translation is enabled per log call, not per format:
```python
# Configure translator in logging config (for formatters)
configure_logging(LoggingConfig(
    format_type=FormatType.JSON,
    translator=MyTranslator()
))

# Or inject translator into logger directly
logger = get_logger(__name__, translator=MyTranslator())

# Use translation on demand
logger.info("user.login.success", translate=True, user_id="123")
logger.info("Regular message")  # No translation
```

## Usage Patterns

### 1. Basic Logging
```python
logger = get_logger(__name__)

# Simple messages
logger.info("Processing started")
logger.warning("Configuration file not found, using defaults")
logger.error("Failed to connect to database")

# With structured data
logger.info("User login", user_id="user123", ip_address="192.168.1.1")
logger.debug("Query executed", query="SELECT * FROM users", duration_ms=45)

# With translation (requires translator dependency)
translator = MyTranslator()
logger = get_logger(__name__, translator=translator)
logger.info("user.login.success", translate=True, user_id="user123")
logger.error("validation.failed", translate=True, error_count=5)
```

### 2. Issue Integration (when available)
```python
# Inject issue tracker dependency
issue_tracker = MyIssueTracker()
logger = get_logger(__name__, issue_tracker=issue_tracker)

# Log single issue
logger.log_issue("Workshop validation failed", issue_obj)

# Log issue collector
logger.validation_summary(collector)
```

### 3. Structured Error Logging
```python
try:
    process_configuration(config)
except ConfigurationError as e:
    logger.log_error(e)  # Uses e.to_dict() if available
```

## Configuration Examples

### Development Setup
```python
configure_logging(LoggingConfig(
    level=logging.DEBUG,
    format_type=FormatType.STRUCTURED,
    console_output=True
    # No file logging
))
```

### Production Setup
```python
configure_logging(LoggingConfig(
    level=logging.INFO,
    format_type=FormatType.JSON,
    console_output=False,
    file=FileConfig(
        path=Path("/var/log/popupsim/app.log"),
        max_bytes=50 * 1024 * 1024,  # 50MB
        backup_count=10
    )
))
```

### Complete Configuration
```python
from core.logging import LoggingConfig, FileConfig, configure_logging

config = LoggingConfig(
    level=logging.INFO,
    format_type=FormatType.STRUCTURED,
    console_output=True,
    file=FileConfig(
        path=Path("logs/app.log"),
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5
    ),
    translator=my_translator  # When available
)

configure_logging(config)
```

### Handler Features

**FileHandler**:
- Automatic directory creation
- UTF-8 encoding by default
- Configurable file mode

**RotatingFileHandler**:
- Automatic directory creation
- Size-based rotation (50MB default)
- Configurable backup count (5 default)
- Thread-safe rotation

**StructuredHandler**:
- Console output with structured data
- Issue and IssueCollector object support
- Automatic field extraction via dedicated extraction function

## Protocol Implementations

It is assumed that PopUpSim might get an issue system to track e.g. validation
erros and stack them instead of stopping at the very first error. Since the
issue system does not exist, a protocol introducedd when implementing the
issue system, create classes that satisfy the protocols:

```python
class MyIssueTracker:
    def track_warning(self, message: str, **context: Any) -> None:
        # Implementation
        pass

    def track_error(self, message: str, **context: Any) -> None:
        # Implementation
        pass

    def track_structured_error(self, error_dict: dict) -> None:
        # Implementation
        pass

class MyTranslator:
    def translate(self, message: str, **kwargs: Any) -> str:
        # Implementation
        return translated_message
```

## Best Practices

### 1. Structured Logging
```python
# ✅ Structured context
logger.info("User action", user_id="user123", action="login", success=True)

# ❌ String formatting
logger.info(f"User user123 logged in")  # Avoid
```

### 2. Dependency Injection
```python
# ✅ Explicit dependencies
logger = get_logger(__name__, issue_tracker=tracker)

# ✅ Easy testing
def test_logging():
    mock_tracker = MockIssueTracker()
    logger = get_logger("test", issue_tracker=mock_tracker)
    # Test with mock
```

### 3. Async Logging
```python
from core.logging import get_async_logger
import asyncio

# Get async logger with dependencies
async_logger = get_async_logger(__name__, issue_tracker=tracker, translator=translator)

# All sync methods available as async
await async_logger.info("Async operation started")
await async_logger.error("Async error occurred", error_code="E001")
await async_logger.log_issue("Validation failed", issue_obj)

# Concurrent logging
async def process_items(items):
    tasks = [async_logger.info("Processing item", item_id=item.id) for item in items]
    await asyncio.gather(*tasks)
```

### 3. Progressive Enhancement

```python
# Start simple
logger = get_logger(__name__)
logger.info("Basic logging")

# Add issue tracking
logger = get_logger(__name__, issue_tracker=MyIssueTracker())
logger.log_issue("Validation failed", issue_obj)

# Add full features
logger = get_logger(__name__, issue_tracker=tracker, translator=translator)
logger.info("user.login", translate=True, user_id="123")

# Go async when needed
async_logger = get_async_logger(__name__, issue_tracker=tracker, translator=translator)
await async_logger.info("Non-blocking logging")
```
