# Internationalization (i18n) Package

## Overview

General-purpose internationalization package using **Babel + gettext** with compiled `.mo` files and standard translation workflows. Designed for reuse across projects.

**gettext** is the GNU internationalization library that enables marking strings for localization. Strings are wrapped with functions like `gettext(str)` and `ngettext(singular, plural, num)`. For brevity, `gettext` is aliased to `_(str)`:

```python
print(_("Hello world!"))  # Localizable
print("Hello world!")     # Not localizable
```

**Babel** is a Python library that extracts translatable strings from source code, manages translation catalogs, and compiles them into efficient binary `.mo` files for runtime use.

**References:**
- [Python gettext documentation](https://docs.python.org/3/library/gettext.html)
- [Babel documentation](https://babel.pocoo.org/)
- [GNU gettext manual](https://www.gnu.org/software/gettext/manual/gettext.html)


## Quick Start

```python
from pathlib import Path
from core.i18n import init_i18n, _, set_locale, ngettext

# Initialize with explicit locale directory
>>> init_i18n(Path('locales'))
<Localizer ...>

# Use translations
>>> _("Workshop capacity exceeded: %(utilization)s%% utilization", utilization=125.0)
'Workshop capacity exceeded: 125.0% utilization'

# Switch language
>>> set_locale("de")
>>> _("Workshop capacity exceeded: %(utilization)s%% utilization", utilization=125.0)
'Werkstattkapazität überschritten: 125.0% Auslastung'

# Plural forms
>>> ngettext("Found %(n)d error", "Found %(n)d errors", 3, n=3)
'Found 3 errors'
>>> set_locale("de")
>>> ngettext("Found %(n)d error", "Found %(n)d errors", 3, n=3)
'3 Fehler gefunden'
```

## API Reference

### Functions
- `init_i18n(locale_dir, domain="messages", default_locale="en")` - Initialize i18n system
- `_(message, **kwargs)` - Translate message with parameters
- `ngettext(singular, plural, n, **kwargs)` - Plural forms
- `set_locale(locale)` - Switch language

### Classes
- `Localizer` - Core translation engine

### Decorators
- `@translatable(message_key)` - Mark functions/classes as translatable

## Translation Workflow

### 1. Extract Messages
```bash
uv run pybabel extract -F babel.cfg -k _ -k ngettext:1,2 -o locales/messages.pot src/
```

### 2. Initialize New Language
```bash
uv run pybabel init -i locales/messages.pot -d locales -l de
```

### 3. Translate Messages
Edit the `.po` file in your preferred editor (Poedit, VS Code, etc.):

**Simple Messages:**
```po
msgid "Workshop capacity exceeded"
msgstr "Werkstattkapazität überschritten"
```

**With Parameters:**
```po
msgid "Workshop capacity exceeded: %(utilization)s%% utilization"
msgstr "Werkstattkapazität überschritten: %(utilization)s%% Auslastung"
```

**Plural Forms:**
```po
msgid "Found %(n)d validation error"
msgid_plural "Found %(n)d validation errors"
msgstr[0] "%(n)d erreur de validation trouvée"
msgstr[1] "%(n)d erreurs de validation trouvées"
```

### 4. Update Existing Translations
```bash
uv run pybabel update -i locales/messages.pot -d locales
```

### 5. Compile for Production
```bash
uv run pybabel compile -d locales
```

## File Structure

```
locales/
├── messages.pot              # Message template
├── de/LC_MESSAGES/
│   ├── messages.po           # German source
│   └── messages.mo           # German compiled
└── fr/LC_MESSAGES/
    ├── messages.po           # French source
    └── messages.mo           # French compiled
```

## Message Format

### Simple Messages
```python
>>> _("Workshop capacity exceeded")
'Workshop capacity exceeded'
```

### With Parameters
```python
>>> _("Workshop capacity exceeded: %(utilization)s%% utilization", utilization=125.0)
'Workshop capacity exceeded: 125.0% utilization'
```

### Plural Forms
```python
>>> ngettext("Found %(n)d error", "Found %(n)d errors", 1, n=1)
'Found 1 error'
>>> ngettext("Found %(n)d error", "Found %(n)d errors", 5, n=5)
'Found 5 errors'
```

## Supported Languages

- **English** (en) - Default
- **German** (de) - In development
- **Add more**: Use `pybabel init` command

## Decorators

The `@translatable` decorator marks functions or classes that contain translatable strings for documentation and tooling purposes.

```python
from core.i18n import translatable

@translatable("validation.workshop.capacity")
def validate_workshop_capacity(config):
    """Validate workshop capacity limits."""
    if config.utilization > 100:
        return _("Workshop capacity exceeded: %(utilization)s%% utilization",
                utilization=config.utilization)
    return None

@translatable("error.messages")
class ValidationError:
    """Error class with translatable messages."""
    def __init__(self, message_key: str):
        self.message = _(message_key)
```

**Purpose:**
- **Documentation**: Clearly mark code sections that handle translations
- **Static Analysis**: Enable tools to find functions with translatable content
- **IDE Integration**: Highlight translatable code for developers
- **Coverage Analysis**: Track which components support internationalization
- **Future Tooling**: Enable automated i18n management and validation

**Note**: The decorator is purely metadata - translations work without it.

## Performance

- **Compiled `.mo` files** for fast runtime lookups
- **Thread-safe** with thread-local storage
- **Lazy loading** of translations
- **Fallback chain**: target locale → default locale → original message
