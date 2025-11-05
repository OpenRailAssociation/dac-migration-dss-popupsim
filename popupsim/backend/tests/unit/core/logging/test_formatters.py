"""Tests for logging formatters."""

import json
import logging
from typing import Any

import pytest

from core.logging.formatters import I18nFormatter
from core.logging.formatters import JsonFormatter
from core.logging.formatters import StructuredFormatter


class MockTranslator:
    """Mock translator for testing."""

    def translate(self, message: str, **_kwargs: Any) -> str:
        """Translate message."""
        return f'TRANSLATED_{message}'


@pytest.fixture
def mock_translator() -> MockTranslator:
    """Create mock translator."""
    return MockTranslator()


@pytest.fixture
def log_record() -> logging.LogRecord:
    """Create test log record."""
    record = logging.LogRecord(
        name='test.logger',
        level=logging.INFO,
        pathname='/test/path.py',
        lineno=42,
        msg='Test message',
        args=(),
        exc_info=None,
    )
    record.module = 'test_module'
    record.funcName = 'test_function'
    return record


class TestJsonFormatter:
    """Test JsonFormatter."""

    def test_basic_formatting(self, log_record: logging.LogRecord) -> None:
        """Test basic JSON formatting."""
        formatter = JsonFormatter()
        result = formatter.format(log_record)

        # Parse JSON to verify structure
        data = json.loads(result)
        assert data['level'] == 'INFO'
        assert data['logger'] == 'test.logger'
        assert data['message'] == 'Test message'
        assert data['module'] == 'test_module'
        assert data['function'] == 'test_function'
        assert data['line'] == 42
        assert 'timestamp' in data

    def test_extra_fields(self, log_record: logging.LogRecord) -> None:
        """Test extra fields in JSON output."""
        formatter = JsonFormatter()

        # Add extra fields
        log_record.user_id = '123'
        log_record.action = 'login'

        result = formatter.format(log_record)
        data = json.loads(result)

        assert data['user_id'] == '123'
        assert data['action'] == 'login'

    def test_translation_support(self, log_record: logging.LogRecord, mock_translator: MockTranslator) -> None:
        """Test translation support in JSON formatter."""
        formatter = JsonFormatter(mock_translator)

        # Mark record for translation
        log_record.translate = True
        log_record.msg_args = {'param': 'value'}

        result = formatter.format(log_record)
        data = json.loads(result)

        assert data['message'] == 'TRANSLATED_Test message'

    def test_exception_handling(self, log_record: logging.LogRecord) -> None:
        """Test exception formatting."""
        formatter = JsonFormatter()

        try:
            raise ValueError('Test exception')
        except ValueError:
            import sys

            log_record.exc_info = sys.exc_info()

        result = formatter.format(log_record)
        data = json.loads(result)

        assert 'exception' in data
        assert 'ValueError: Test exception' in data['exception']


class TestStructuredFormatter:
    """Test StructuredFormatter."""

    def test_basic_formatting(self, log_record: logging.LogRecord) -> None:
        """Test basic structured formatting."""
        formatter = StructuredFormatter()
        result = formatter.format(log_record)

        # Check basic structure
        assert 'INFO' in result
        assert 'test.logger' in result
        assert 'Test message' in result
        assert result.startswith('[')  # Timestamp

    def test_extra_fields(self, log_record: logging.LogRecord) -> None:
        """Test extra fields in structured output."""
        formatter = StructuredFormatter()

        # Add extra fields
        log_record.user_id = '123'
        log_record.action = 'login'

        result = formatter.format(log_record)

        # Should contain JSON-formatted extra data
        assert '"user_id": "123"' in result
        assert '"action": "login"' in result

    def test_translation_support(self, log_record: logging.LogRecord, mock_translator: MockTranslator) -> None:
        """Test translation support in structured formatter."""
        formatter = StructuredFormatter(mock_translator)

        # Mark record for translation
        log_record.translate = True
        log_record.msg_args = {'param': 'value'}

        result = formatter.format(log_record)

        assert 'TRANSLATED_Test message' in result

    def test_exception_handling(self, log_record: logging.LogRecord) -> None:
        """Test exception formatting."""
        formatter = StructuredFormatter()

        try:
            raise ValueError('Test exception')
        except ValueError:
            import sys

            log_record.exc_info = sys.exc_info()

        result = formatter.format(log_record)

        # Should contain exception traceback
        assert 'ValueError: Test exception' in result
        assert 'Traceback' in result

    def test_minimal_extra_fields(self) -> None:
        """Test formatting with minimal extra fields."""
        formatter = StructuredFormatter()

        # Create a minimal record
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should contain basic message structure
        assert 'Test message' in result
        assert 'INFO' in result
        assert 'test.logger' in result


@pytest.mark.unit
class TestFormatterIntegration:
    """Integration tests for formatters."""

    def test_formatter_consistency(self, log_record: logging.LogRecord, mock_translator: MockTranslator) -> None:
        """Test that both formatters handle translation consistently."""
        json_formatter = JsonFormatter(mock_translator)
        structured_formatter = StructuredFormatter(mock_translator)

        # Mark record for translation
        log_record.translate = True
        log_record.msg_args = {'param': 'value'}

        json_result = json_formatter.format(log_record)
        structured_result = structured_formatter.format(log_record)

        # Both should contain translated message
        assert 'TRANSLATED_Test message' in json_result
        assert 'TRANSLATED_Test message' in structured_result


class TestI18nFormatter:
    """Test I18nFormatter."""

    def test_without_translator(self) -> None:
        """Test I18nFormatter without translator."""
        formatter = I18nFormatter()

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )
        record.translate = True
        record.msg_args = {'key': 'value'}

        # Should not crash without translator
        result = formatter.format(record)
        assert 'Test message' in result

    def test_with_translator(self) -> None:
        """Test I18nFormatter with translator."""

        class MockTranslator:
            def translate(self, message: str, **_kwargs: Any) -> str:
                return f'TRANSLATED_{message}'

        formatter = I18nFormatter(MockTranslator())

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )
        record.translate = True
        record.msg_args = {'key': 'value'}

        result = formatter.format(record)
        assert 'TRANSLATED_Test message' in result


class TestFormatterEdgeCases:
    """Test formatter edge cases for coverage."""

    def test_json_formatter_without_translator_translate_flag(self) -> None:
        """Test JsonFormatter without translator but with translate flag."""
        formatter = JsonFormatter()

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )
        record.translate = True
        record.msg_args = {'key': 'value'}

        result = formatter.format(record)
        data = json.loads(result)
        assert data['message'] == 'Test message'

    def test_structured_formatter_without_translator_translate_flag(self) -> None:
        """Test StructuredFormatter without translator but with translate flag."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )
        record.translate = True
        record.msg_args = {'key': 'value'}

        result = formatter.format(record)
        assert 'Test message' in result
