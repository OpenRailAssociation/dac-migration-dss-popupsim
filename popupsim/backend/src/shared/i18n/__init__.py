"""Internationalization support for PopUpSim.

This package provides internationalization using Babel and gettext with
compiled .mo files, translation workflows, and plural form support.

The package exposes an API that defaults to Babel-based translation while
maintaining compatibility with standard gettext conventions.

Examples
--------
>>> from shared.i18n import init_i18n, _, set_locale
>>> init_i18n(Path('locales'))
>>> message = _('Hello %(name)s', name='World')
>>> set_locale('de')
>>> german_message = _('Hello %(name)s', name='World')
"""

from .decorators import translatable
from .localizer import Localizer, _, get_localizer, init_i18n, ngettext, set_locale

# Default API alias for clean interface
translate = _

__all__ = [
    "Localizer",
    "_",
    "get_localizer",
    "init_i18n",
    "ngettext",
    "set_locale",
    "translatable",
    "translate",
]
