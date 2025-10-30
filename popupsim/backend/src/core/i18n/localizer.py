"""Babel-based internationalization.

This module provides internationalization using gettext and babel with
thread-safe localizer instances.

Attributes
----------
_thread_local : threading.local
    Thread-local storage object storing per-thread localizer instances
_global_config : Dict[str, Any]
    Global configuration storing initialization parameters for auto-creating
    localizer instances in new threads

Thread Safety
-------------
The module uses thread-local storage to ensure each thread gets its own
localizer instance. When `init_i18n()` is called, it stores configuration in
`_global_config` and creates a localizer for the current thread. When
`get_localizer()` is called from a new thread without a localizer, it
auto-initializes using the stored configuration.
"""

from pathlib import Path
import threading
from typing import Any

from babel.support import Translations

_thread_local = threading.local()
_global_config: dict[str, Any] = {}


class Localizer:
    """Babel-based localizer for gettext translations.

    Provides translation services using compiled .mo files with fallback
    support and parameter interpolation.

    Parameters
    ----------
    locale_dir : Path
        Directory containing locale subdirectories with LC_MESSAGES
    domain : str, default "messages"
        Translation domain name (matches .mo filename)
    default_locale : str, default "en"
        Fallback locale when translation is not found

    Attributes
    ----------
    locale_dir : Path
        Path to locales directory
    domain : str
        Translation domain name
    default_locale : str
        Default fallback locale
    current_locale : str
        Currently active locale

    Examples
    --------
    >>> localizer = Localizer(Path('locales'))
    >>> localizer.translate('Hello world')
    'Hello world'
    >>> localizer.set_locale('de')
    >>> localizer.translate('Hello world')
    'Hallo Welt'
    """

    def __init__(self, locale_dir: Path, domain: str = 'messages', default_locale: str = 'en'):
        self.locale_dir = locale_dir
        self.domain = domain
        self.default_locale = default_locale
        self.current_locale = default_locale
        self._translations: dict[str, Translations] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all available translations from locale directory."""
        if not self.locale_dir.exists():
            return
        for locale_subdir in self.locale_dir.iterdir():
            if locale_subdir.is_dir():
                self._load_locale(locale_subdir.name)

    def _load_locale(self, locale_code: str) -> None:
        """Load translations for specific locale.

        Parameters
        ----------
        locale_code : str
            Locale code (e.g., 'en', 'de', 'fr')
        """
        mo_file_path = self.locale_dir / locale_code / 'LC_MESSAGES' / f'{self.domain}.mo'
        if mo_file_path.exists():
            with open(mo_file_path, 'rb') as mo_file:
                self._translations[locale_code] = Translations(mo_file)
        else:
            self._translations[locale_code] = Translations()

    def translate(self, message: str, locale_code: str | None = None, **format_kwargs: Any) -> str:
        """Translate message with optional parameter substitution.

        Parameters
        ----------
        message : str
            Message to translate
        locale_code : str, optional
            Target locale, uses current_locale if None
        **format_kwargs
            Parameters for string formatting

        Returns
        -------
        str
            Translated message with parameters substituted

        Examples
        --------
        >>> localizer.translate('Hello %(name)s', name='World')
        'Hello World'
        """
        target_locale = locale_code or self.current_locale
        translations = self._translations.get(target_locale)
        if not translations:
            translations = self._translations.get(self.default_locale, Translations())

        translated_msg: str = translations.gettext(message)
        if format_kwargs:
            try:
                return translated_msg % format_kwargs
            except (KeyError, TypeError):
                return translated_msg
        return translated_msg

    def ngettext(
        self, singular_msg: str, plural_msg: str, count: int, locale_code: str | None = None, **format_kwargs: Any
    ) -> str:
        """Translate message with plural forms.

        Parameters
        ----------
        singular_msg : str
            Singular form message
        plural_msg : str
            Plural form message
        count : int
            Number determining singular/plural
        locale_code : str, optional
            Target locale, uses current_locale if None
        **format_kwargs
            Parameters for string formatting

        Returns
        -------
        str
            Translated message in appropriate plural form

        Examples
        --------
        >>> localizer.ngettext('%(n)d error', '%(n)d errors', 1, n=1)
        '1 error'
        >>> localizer.ngettext('%(n)d error', '%(n)d errors', 5, n=5)
        '5 errors'
        """
        target_locale = locale_code or self.current_locale
        translations = self._translations.get(
            target_locale, self._translations.get(self.default_locale, Translations())
        )
        translated_msg: str = translations.ngettext(singular_msg, plural_msg, count)
        if format_kwargs:
            format_kwargs['n'] = count
            try:
                return translated_msg % format_kwargs
            except (KeyError, TypeError):
                return translated_msg
        return translated_msg

    def set_locale(self, locale_code: str) -> None:
        """Set current locale for translations.

        Parameters
        ----------
        locale_code : str
            Locale code to activate (e.g., 'en', 'de', 'fr')

        Examples
        --------
        >>> localizer.set_locale('de')
        >>> localizer.current_locale
        'de'
        """
        self.current_locale = locale_code
        if locale_code not in self._translations:
            self._load_locale(locale_code)


def init_i18n(locale_dir: Path, domain: str = 'messages', default_locale: str = 'en') -> Localizer:
    """Initialize internationalization system.

    Sets up thread-safe translation system with compiled .mo files.
    This function must be called before using any translation functions.

    Parameters
    ----------
    locale_dir : Path
        Directory containing locale subdirectories with .mo files
    domain : str, default "messages"
        Translation domain name (matches .mo filename)
    default_locale : str, default "en"
        Default fallback locale

    Returns
    -------
    Localizer
        Initialized localizer instance

    Examples
    --------
    >>> init_i18n(Path('locales'))
    <Localizer ...>
    >>> init_i18n(Path('translations'), domain='myapp', default_locale='de')
    <Localizer ...>

    Notes
    -----
    This is the main entry point for i18n setup. After calling this function,
    you can use translation functions like _() and ngettext().
    """
    _global_config.update(
        {
            'locale_dir': locale_dir,
            'domain': domain,
            'default_locale': default_locale,
        }
    )
    localizer = Localizer(locale_dir, domain, default_locale)
    _thread_local.localizer = localizer
    return localizer


def get_localizer() -> Localizer:
    """Get localizer instance for current thread.

    Returns
    -------
    Localizer
        Thread-local localizer instance

    Examples
    --------
    >>> localizer = get_localizer()

    Notes
    -----
    Uses thread-local storage for thread safety. See module docstring
    for details on `_thread_local` and `_global_config` variables.
    """
    if not hasattr(_thread_local, 'localizer'):
        if _global_config:
            new_localizer = Localizer(
                _global_config['locale_dir'], _global_config['domain'], _global_config['default_locale']
            )
            _thread_local.localizer = new_localizer
        else:
            raise RuntimeError('Localizer not initialized. Call init_i18n() first.')

    current_localizer: Localizer = _thread_local.localizer
    return current_localizer


def _(message: str, **format_kwargs: Any) -> str:
    """Translate message.

    Parameters
    ----------
    message : str
        Message to translate
    **format_kwargs
        Parameters for string formatting

    Returns
    -------
    str
        Translated message

    Examples
    --------
    >>> _('Hello %(name)s', name='World')
    'Hello World'
    """
    return get_localizer().translate(message, **format_kwargs)


def ngettext(singular_msg: str, plural_msg: str, count: int, **format_kwargs: Any) -> str:
    """Translate message with plural forms.

    Parameters
    ----------
    singular_msg : str
        Singular form message
    plural_msg : str
        Plural form message
    count : int
        Number determining singular/plural
    **format_kwargs
        Parameters for string formatting

    Returns
    -------
    str
        Translated message in appropriate plural form

    Examples
    --------
    >>> ngettext('%(n)d error', '%(n)d errors', 1, n=1)
    '1 error'
    """
    return get_localizer().ngettext(singular_msg, plural_msg, count, **format_kwargs)


def set_locale(locale_code: str) -> None:
    """Set current locale.

    Parameters
    ----------
    locale_code : str
        Locale code to activate

    Examples
    --------
    >>> set_locale('de')
    """
    get_localizer().set_locale(locale_code)
