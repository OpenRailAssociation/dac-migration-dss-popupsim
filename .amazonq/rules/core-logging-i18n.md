# Core Module Rules: Logging & Internationalization

## Logging Standards

### Logger Creation (MANDATORY)
All loggers MUST be created using `core.logging.get_logger()`:

```python
from core.logging import Logger, get_logger

logger: Logger = get_logger(__name__)

def process_data(data_id: str) -> None:
    logger.info("Processing data", data_id=data_id)
    logger.error("Failed to process", data_id=data_id, error="timeout")
```

### Logger Configuration
- Use `get_logger(__name__)` for module-level loggers
- Type hint: `logger: Logger` (from `core.logging`)
- Pass context as keyword arguments, NOT in `extra` dict
- Log levels: DEBUG, INFO, WARNING, ERROR
- Configure system once at startup with `configure_logging()`

### System Configuration
```python
from core.logging import configure_logging, LoggingConfig, FileConfig, FormatType
from core.i18n import init_i18n
from pathlib import Path
import logging

# Initialize i18n and get localizer
localizer = init_i18n(Path("locales"))

# Configure logging with translator
configure_logging(LoggingConfig(
    level=logging.INFO,
    format_type=FormatType.STRUCTURED,  # or FormatType.JSON
    console_output=True,
    file=FileConfig(path=Path("logs/app.log")),
    translator=localizer  # Enable log translation
))
```

### Log Message Format
```python
# Good: Structured with keyword arguments
logger.info("Workshop capacity exceeded", utilization=125.0, workshop_id="WS-001")

# Good: With translation enabled
logger.info("Workshop capacity exceeded", translate=True, utilization=125.0, workshop_id="WS-001")

# Bad: String interpolation
logger.info(f"Workshop capacity exceeded: {utilization}%")

# Bad: Using extra dict
logger.info("Message", extra={"key": "value"})
```

## Internationalization (i18n)

### Translation Functions (MANDATORY)
All user-facing strings MUST be wrapped with i18n functions:

```python
from core.i18n import _, ngettext, init_i18n, set_locale
from pathlib import Path

# Initialize once at startup
init_i18n(Path("locales"))

# Simple translation
message: str = _("Workshop capacity exceeded")

# With parameters (use named placeholders)
message: str = _("Workshop capacity exceeded: %(utilization)s%% utilization",
                 utilization=125.0)

# Plural forms
message: str = ngettext("Found %(n)d error", "Found %(n)d errors", count, n=count)
```

### Translation Rules
- Use `_()` for all user-facing strings
- Use named parameters: `%(name)s`, not positional `%s`
- Use `ngettext()` for plurals, never conditional strings
- Mark functions with `@translatable(key)` decorator for documentation
- Never concatenate translated strings

### Type Hints for i18n
```python
from typing import Optional
from pathlib import Path
from core.i18n import Localizer

def init_i18n(locale_dir: Path, domain: str = "messages",
              default_locale: str = "en") -> Localizer:
    """Initialize i18n system."""
    ...

def _(message: str, **kwargs: Any) -> str:
    """Translate message."""
    ...

def ngettext(singular: str, plural: str, n: int, **kwargs: Any) -> str:
    """Translate with plural forms."""
    ...
```

### Translatable Decorator
```python
from core.i18n import translatable

@translatable("validation.workshop")
def validate_workshop(config: dict[str, Any]) -> Optional[str]:
    """Validate workshop configuration."""
    if config["utilization"] > 100:
        return _("Workshop capacity exceeded: %(utilization)s%% utilization",
                utilization=config["utilization"])
    return None
```

## Combined Usage: Logging + i18n

### Pattern: Log Technical, Return Translated
```python
from typing import Optional
from core.logging import Logger, get_logger
from core.i18n import _

logger: Logger = get_logger(__name__)

def validate_capacity(utilization: float, workshop_id: str) -> Optional[str]:
    """Validate workshop capacity."""
    if utilization > 100:
        # Log with translation enabled
        logger.warning("Workshop capacity exceeded", translate=True,
                      utilization=utilization,
                      workshop_id=workshop_id)
        # Return user-facing message (translated)
        return _("Workshop capacity exceeded: %(utilization)s%% utilization",
                utilization=utilization)
    return None
```

### Pattern: Exception Handling
```python
from typing import Any
from core.logging import Logger, get_logger
from core.i18n import _

logger: Logger = get_logger(__name__)

def process_data(data: dict[str, Any]) -> str:
    """Process data with error handling."""
    try:
        result: str = perform_operation(data)
        logger.info("Operation successful", translate=True, data_id=data["id"])
        return result
    except ValueError as e:
        logger.error("Validation failed", translate=True, data_id=data["id"], error=str(e))
        raise ValueError(_("Invalid data format")) from e
```

## Translation Workflow Commands

```bash
# Extract translatable strings
uv run pybabel extract -F babel.cfg -k _ -k ngettext:1,2 -o popupsim/backend/src/core/i18n/locales/messages.pot popupsim/backend/src/

# Initialize new language
uv run pybabel init -i popupsim/backend/src/core/i18n/locales/messages.pot -d popupsim/backend/src/core/i18n/locales -l de

# Update existing translations
uv run pybabel update -i popupsim/backend/src/core/i18n/locales/messages.pot -d popupsim/backend/src/core/i18n/locales

# Compile for production
uv run pybabel compile -d popupsim/backend/src/core/i18n/locales
```

## Supported Languages
- English (en) - Default
- German (de) - In development

## Usage Example
```python
from core.logging import configure_logging, LoggingConfig, get_logger
from core.i18n import init_i18n, set_locale, _
from pathlib import Path
import logging

# Initialize i18n
localizer = init_i18n(Path("locales"))
set_locale("de")

# Configure logging with translator
configure_logging(LoggingConfig(
    level=logging.INFO,
    translator=localizer
))

# Get logger
logger = get_logger(__name__)

# Logs with translation
logger.info("Application started", translate=True, version="1.0")

# User-facing messages
print(_("Welcome to PopUpSim"))
```

## Log Translation

### Enable Translation Per Log
```python
# Translation is opt-in per log call using translate=True
logger.info("Application started", translate=True, app_name="popupsim")
logger.error("Validation failed", translate=True, error_count=5)

# Logs without translate=True remain in original language
logger.debug("Debug info", request_id="abc123")  # Not translated
```

### Configure Translator
```python
from core.logging import configure_logging, LoggingConfig
from core.i18n import init_i18n

# Initialize i18n and pass to logging
localizer = init_i18n(Path("locales"))
configure_logging(LoggingConfig(
    level=logging.INFO,
    translator=localizer  # Enable translation support
))
```

## Key Principles
1. **Use core.logging package** (NOT standard logging.getLogger)
2. **Logs can be translated** (use `translate=True` flag)
3. **Messages are user-facing** (always translated with `_()` function)
4. **Type hints everywhere** (Logger from core.logging, str returns)
5. **Keyword arguments** (NOT extra dict)
6. **Named parameters for i18n** (%(name)s format)
7. **Translation is opt-in** (add `translate=True` to log calls when needed)
