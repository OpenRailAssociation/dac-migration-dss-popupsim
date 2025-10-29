"""Test fixtures for i18n tests."""

from pathlib import Path
import tempfile

from babel.messages import Catalog
from babel.messages.mofile import write_mo
import pytest


@pytest.fixture
def test_locales_dir():
    """Create temporary directory with test locale files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        locales_dir = Path(temp_dir)

        # Create German translations
        de_dir = locales_dir / 'de' / 'LC_MESSAGES'
        de_dir.mkdir(parents=True)

        de_catalog = Catalog(locale='de')
        de_catalog.add('Hello World', 'Hallo Welt')
        de_catalog.add('Hello %(name)s', 'Hallo %(name)s')
        de_catalog.add(('%(n)d error found', '%(n)d errors found'), ('%(n)d Fehler gefunden', '%(n)d Fehler gefunden'))

        with open(de_dir / 'messages.mo', 'wb') as f:
            write_mo(f, de_catalog)

        # Create French translations
        fr_dir = locales_dir / 'fr' / 'LC_MESSAGES'
        fr_dir.mkdir(parents=True)

        fr_catalog = Catalog(locale='fr')
        fr_catalog.add('Hello World', 'Bonjour le monde')
        fr_catalog.add('Hello %(name)s', 'Bonjour %(name)s')
        fr_catalog.add(('%(n)d error found', '%(n)d errors found'), ('%(n)d erreur trouvée', '%(n)d erreurs trouvées'))

        with open(fr_dir / 'messages.mo', 'wb') as f:
            write_mo(f, fr_catalog)

        yield locales_dir


@pytest.fixture
def empty_locales_dir():
    """Create empty temporary directory for testing missing locales."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def cleanup_i18n():
    """Clean up i18n state after each test."""
    yield

    # Clear thread-local and global config
    import core.i18n.localizer as localizer_module

    if hasattr(localizer_module._thread_local, 'localizer'):
        delattr(localizer_module._thread_local, 'localizer')
    localizer_module._global_config.clear()
