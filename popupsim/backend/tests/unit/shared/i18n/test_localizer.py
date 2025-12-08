"""Tests for i18n localizer functionality."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from shared.i18n.localizer import (
    Localizer,
    _,
    get_localizer,
    init_i18n,
    ngettext,
    set_locale,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def empty_locales_dir() -> Generator[Path]:
    """Create an empty temporary locales directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_locales_dir() -> Generator[Path]:
    """Create a test locales directory without .mo files for basic testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        locales_dir = Path(temp_dir)

        # Create German locale directory structure but no .mo files
        # This allows testing the localizer without actual translation files
        de_dir = locales_dir / "de" / "LC_MESSAGES"
        de_dir.mkdir(parents=True)

        yield locales_dir


class TestLocalizer:
    """Test cases for Localizer class."""

    def test_localizer_initialization(self, empty_locales_dir: Path) -> None:
        """Test Localizer initialization with required parameters."""
        localizer = Localizer(empty_locales_dir, "messages", "en")
        assert localizer.current_locale == "en"
        assert localizer.domain == "messages"
        assert localizer.default_locale == "en"

    def test_localizer_set_locale(self, empty_locales_dir: Path) -> None:
        """Test setting locale."""
        localizer = Localizer(empty_locales_dir, "messages", "en")
        localizer.set_locale("de")
        assert localizer.current_locale == "de"

    def test_translate_function_with_init(self, test_locales_dir: Path) -> None:
        """Test global translate function after initialization."""
        init_i18n(test_locales_dir, "messages", "en")
        result = _("Hello World")
        assert result == "Hello World"  # Fallback behavior

    def test_translate_with_actual_translation(self, test_locales_dir: Path) -> None:
        """Test translation with actual German translation."""
        init_i18n(test_locales_dir, "messages", "en")
        set_locale("de")
        result = _("Hello World")
        assert result == "Hello World"  # No .mo file, so fallback

    def test_ngettext_function_with_init(self, test_locales_dir: Path) -> None:
        """Test global ngettext function after initialization."""
        init_i18n(test_locales_dir, "messages", "en")
        result = ngettext("%(n)d item", "%(n)d items", 1)
        assert result == "%(n)d item"

        result = ngettext("%(n)d item", "%(n)d items", 2)
        assert result == "%(n)d items"

    def test_translate_with_parameters(self, test_locales_dir: Path) -> None:
        """Test translation with parameter substitution."""
        init_i18n(test_locales_dir, "messages", "en")
        result = _("Hello %(name)s", name="World")
        assert result == "Hello World"

    def test_translate_with_parameters_german(self, test_locales_dir: Path) -> None:
        """Test translation with parameters in German."""
        init_i18n(test_locales_dir, "messages", "en")
        set_locale("de")
        result = _("Hello %(name)s", name="Welt")
        assert result == "Hello Welt"  # No .mo file, so fallback with params

    def test_translate_with_invalid_parameters(self, test_locales_dir: Path) -> None:
        """Test translation with invalid parameters falls back gracefully."""
        init_i18n(test_locales_dir, "messages", "en")
        result = _("Hello %(name)s", invalid_param="World")
        assert result == "Hello %(name)s"  # Original message when formatting fails

    def test_ngettext_with_parameters(self, test_locales_dir: Path) -> None:
        """Test ngettext with parameter substitution."""
        init_i18n(test_locales_dir, "messages", "en")
        result = ngettext("%(n)d error found", "%(n)d errors found", 3, n=3)
        assert result == "3 errors found"

    def test_ngettext_with_german_translation(self, test_locales_dir: Path) -> None:
        """Test ngettext with German translation."""
        init_i18n(test_locales_dir, "messages", "en")
        set_locale("de")
        result = ngettext("%(n)d error found", "%(n)d errors found", 3, n=3)
        assert result == "3 errors found"  # No .mo file, so fallback

    def test_set_locale_global(self, test_locales_dir: Path) -> None:
        """Test global set_locale function."""
        init_i18n(test_locales_dir, "messages", "en")
        set_locale("de")
        localizer = get_localizer()
        assert localizer.current_locale == "de"

    def test_get_localizer_without_init_raises_error(self) -> None:
        """Test get_localizer raises error when not initialized."""
        # Clear any existing localizer and global config
        import shared.i18n.localizer as localizer_module

        if hasattr(localizer_module._thread_local, "localizer"):
            delattr(localizer_module._thread_local, "localizer")
        localizer_module._global_config.clear()

        with pytest.raises(RuntimeError, match="Localizer not initialized"):
            get_localizer()


class TestInitI18n:
    """Test cases for init_i18n function."""

    def test_init_i18n_basic(self, test_locales_dir: Path) -> None:
        """Test basic init_i18n functionality."""
        init_i18n(test_locales_dir)
        result = _("Test message")
        assert result == "Test message"

    def test_init_i18n_with_custom_domain(self, test_locales_dir: Path) -> None:
        """Test init_i18n with custom domain."""
        init_i18n(test_locales_dir, domain="custom", default_locale="de")
        localizer = get_localizer()
        assert localizer.domain == "custom"
        assert localizer.default_locale == "de"


class TestLocalizerEdgeCases:
    """Test edge cases and error conditions."""

    def test_load_locale_without_mo_file(self, empty_locales_dir: Path) -> None:
        """Test loading locale when .mo file doesn't exist."""
        localizer = Localizer(empty_locales_dir, "messages", "en")
        localizer._load_locale("de")  # Should create empty Translations
        assert "de" in localizer._translations

    def test_ngettext_with_invalid_format_kwargs(self, test_locales_dir: Path) -> None:
        """Test ngettext with invalid format parameters."""
        init_i18n(test_locales_dir, "messages", "en")
        result = ngettext("%(invalid)d error", "%(invalid)d errors", 3, wrong_param=3)
        assert (
            result == "%(invalid)d errors"
        )  # Falls back to original when formatting fails

    def test_set_locale_loads_new_locale(self, test_locales_dir: Path) -> None:
        """Test that set_locale loads new locale if not already loaded."""
        localizer = Localizer(test_locales_dir, "messages", "en")
        initial_count = len(localizer._translations)
        localizer.set_locale("fr")  # New locale
        assert len(localizer._translations) >= initial_count
        assert localizer.current_locale == "fr"

    def test_auto_initialize_from_global_config(self, test_locales_dir: Path) -> None:
        """Test auto-initialization from global config in new thread context."""
        # First initialize to set global config
        init_i18n(test_locales_dir, "messages", "en")

        # Clear thread-local to simulate new thread
        import shared.i18n.localizer as localizer_module

        if hasattr(localizer_module._thread_local, "localizer"):
            delattr(localizer_module._thread_local, "localizer")

        # Should auto-initialize from global config
        localizer = get_localizer()
        assert localizer.domain == "messages"
        assert localizer.default_locale == "en"
