"""Configure pytest to find the src package."""

from pathlib import Path

import pytest

from core.i18n import init_i18n


@pytest.fixture(scope='session', autouse=True)
def initialize_i18n() -> None:
    """Initialize i18n for all tests."""
    locale_dir = Path(__file__).parent.parent / 'src' / 'core' / 'i18n' / 'locales'
    init_i18n(locale_dir)
