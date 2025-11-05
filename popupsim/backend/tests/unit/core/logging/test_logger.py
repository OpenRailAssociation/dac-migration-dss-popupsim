"""Tests for logging system."""

import logging
from pathlib import Path
import tempfile
from typing import Any

import pytest

from core.logging import FileConfig
from core.logging import FormatType
from core.logging import Logger
from core.logging import LoggingConfig
from core.logging import configure_logging
from core.logging import get_logger


class MockIssueTracker:
    """Mock issue tracker for testing."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, dict]] = []
        self.errors: list[tuple[str, dict]] = []
        self.structured_errors: list[dict] = []

    def track_warning(self, message: str, **context: Any) -> None:
        """Track warning."""
        self.warnings.append((message, context))

    def track_error(self, message: str, **context: Any) -> None:
        """Track error."""
        self.errors.append((message, context))

    def track_structured_error(self, error_dict: dict) -> None:
        """Track structured error."""
        self.structured_errors.append(error_dict)


class MockTranslator:
    """Mock translator for testing."""

    def translate(self, message: str, **_kwargs: Any) -> str:
        """Translate message."""
        return f'TRANSLATED_{message}'


@pytest.fixture
def temp_log_file() -> Path:
    """Create temporary log file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as f:
        return Path(f.name)


@pytest.fixture
def mock_issue_tracker() -> MockIssueTracker:
    """Create mock issue tracker."""
    return MockIssueTracker()


@pytest.fixture
def mock_translator() -> MockTranslator:
    """Create mock translator."""
    return MockTranslator()


class TestLogger:
    """Test Logger class."""

    def test_logger_creation(self) -> None:
        """Test logger creation."""
        logger = Logger('test.logger')
        assert logger._logger.name == 'test.logger'
        assert logger._issue_tracker is None
        assert logger._translator is None

    def test_logger_with_issue_tracker(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test logger with issue tracker."""
        logger = Logger('test.logger', issue_tracker=mock_issue_tracker)
        assert logger._issue_tracker is mock_issue_tracker

    def test_basic_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test basic logging methods."""
        logger = Logger('test.logger')

        with caplog.at_level(logging.DEBUG):
            logger.debug('Debug message')
            logger.info('Info message')
            logger.warning('Warning message')
            logger.error('Error message')

        assert 'Debug message' in caplog.text
        assert 'Info message' in caplog.text
        assert 'Warning message' in caplog.text
        assert 'Error message' in caplog.text

    def test_structured_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test structured logging with extra data."""
        logger = Logger('test.logger')

        with caplog.at_level(logging.INFO):
            logger.info('User login', user_id='123', action='login')

        # Check that extra data is included
        record = caplog.records[0]
        assert getattr(record, 'user_id', None) == '123'
        assert getattr(record, 'action', None) == 'login'

    def test_translation_support(self, caplog: pytest.LogCaptureFixture, mock_translator: MockTranslator) -> None:
        """Test translation support."""
        logger = Logger('test.logger', translator=mock_translator)

        with caplog.at_level(logging.INFO):
            logger.info('user.login', translate=True, user_id='123')

        # Check that translation was applied
        record = caplog.records[0]
        assert getattr(record, 'translate', None) is True
        assert getattr(record, 'msg_args', None) == {'user_id': '123'}

    def test_issue_tracker_integration(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test issue tracker integration."""
        logger = Logger('test.logger', issue_tracker=mock_issue_tracker)

        logger.warning('Test warning', context='test')
        logger.error('Test error', severity='high')

        assert len(mock_issue_tracker.warnings) == 1
        assert mock_issue_tracker.warnings[0] == ('Test warning', {'context': 'test'})

        assert len(mock_issue_tracker.errors) == 1
        assert mock_issue_tracker.errors[0] == ('Test error', {'severity': 'high'})


class TestLoggingConfig:
    """Test LoggingConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = LoggingConfig()
        assert config.level == logging.INFO
        assert config.format_type == FormatType.STRUCTURED
        assert config.console_output is True
        assert config.file is None
        assert config.translator is None

    def test_custom_config(self, temp_log_file: Path) -> None:
        """Test custom configuration."""
        file_config = FileConfig(path=temp_log_file, max_bytes=1024, backup_count=3)
        config = LoggingConfig(level=logging.DEBUG, format_type=FormatType.JSON, console_output=False, file=file_config)

        assert config.level == logging.DEBUG
        assert config.format_type == FormatType.JSON
        assert config.console_output is False
        assert config.file is file_config


class TestConfigureFunctions:
    """Test configuration functions."""

    def test_configure_logging_default(self) -> None:
        """Test configure_logging with defaults."""
        configure_logging()

        # Should not raise any exceptions
        logger = get_logger('test')
        assert isinstance(logger, Logger)

    def test_configure_logging_custom(self, temp_log_file: Path) -> None:
        """Test configure_logging with custom config."""
        config = LoggingConfig(level=logging.DEBUG, format_type=FormatType.JSON, file=FileConfig(path=temp_log_file))

        configure_logging(config)

        # Should not raise any exceptions
        logger = get_logger('test')
        assert isinstance(logger, Logger)

    def test_get_logger_with_dependencies(
        self, mock_issue_tracker: MockIssueTracker, mock_translator: MockTranslator
    ) -> None:
        """Test get_logger with dependency injection."""
        logger = get_logger('test', issue_tracker=mock_issue_tracker, translator=mock_translator)
        assert logger._issue_tracker is mock_issue_tracker
        assert logger._translator is mock_translator

    def test_get_logger_basic(self) -> None:
        """Test get_logger function without dependencies."""
        logger1 = get_logger('test.module')
        logger2 = get_logger('test.module')

        # Should return Logger instances
        assert isinstance(logger1, Logger)
        assert isinstance(logger2, Logger)

        # Should have same underlying logger name
        assert logger1._logger.name == logger2._logger.name

        # Should have no dependencies
        assert logger1._issue_tracker is None
        assert logger1._translator is None


class TestDependencyInjection:
    """Test dependency injection."""

    def test_concurrent_logger_creation(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test concurrent logger creation with different dependencies."""
        import threading

        loggers = []

        def create_logger_with_tracker() -> None:
            logger = get_logger('test', issue_tracker=mock_issue_tracker)
            loggers.append(logger)

        def create_logger_without_tracker() -> None:
            logger = get_logger('test')
            loggers.append(logger)

        # Run concurrent logger creation
        threads = [
            threading.Thread(target=create_logger_with_tracker),
            threading.Thread(target=create_logger_without_tracker),
            threading.Thread(target=create_logger_with_tracker),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should create 3 loggers with different configurations
        assert len(loggers) == 3
        assert loggers[0]._issue_tracker is mock_issue_tracker
        assert loggers[1]._issue_tracker is None
        assert loggers[2]._issue_tracker is mock_issue_tracker


@pytest.mark.unit
class TestIntegration:
    """Integration tests."""

    def test_full_logging_workflow(
        self, temp_log_file: Path, mock_issue_tracker: MockIssueTracker, mock_translator: MockTranslator
    ) -> None:
        """Test complete logging workflow."""
        # Configure everything
        config = LoggingConfig(
            level=logging.DEBUG,
            format_type=FormatType.STRUCTURED,
            file=FileConfig(path=temp_log_file),
            translator=mock_translator,
        )

        configure_logging(config)

        # Get logger with dependencies and test all features
        logger = get_logger('integration.test', issue_tracker=mock_issue_tracker, translator=mock_translator)

        logger.debug('Debug message')
        logger.info('Info message', user_id='123')
        logger.warning('Warning message', context='test')
        logger.error('Error message', severity='high')
        logger.info('Translated message', translate=True, param='value')

        # Verify issue tracker was called
        assert len(mock_issue_tracker.warnings) == 1
        assert len(mock_issue_tracker.errors) == 1

        # Verify log file was created
        assert temp_log_file.exists()
        assert temp_log_file.stat().st_size > 0


class TestLoggerEdgeCases:
    """Test Logger edge cases for coverage."""

    def test_log_issue_method(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test log_issue method."""

        class MockIssue:
            def __init__(self) -> None:
                self.error_code = 'E001'

        logger = Logger('test.logger', issue_tracker=mock_issue_tracker)
        issue = MockIssue()  # type: ignore[arg-type]

        logger.log_issue('Issue occurred', issue)  # type: ignore[arg-type]

        # Should call error method with issue
        assert len(mock_issue_tracker.errors) == 1
        assert mock_issue_tracker.errors[0][0] == 'Issue occurred'

    def test_validation_summary_with_issues(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test validation_summary with issues."""
        from core.logging.protocols import Issue

        class MockSeverity:
            def __init__(self, value: str) -> None:
                self.value = value

        class MockIssue:
            def __init__(self) -> None:
                self.severity = MockSeverity('HIGH')

        class MockIssueCollector:
            def get_issues(self) -> list[Issue]:
                return [MockIssue(), MockIssue()]  # type: ignore[list-item]

        logger = Logger('test.logger')
        collector = MockIssueCollector()  # type: ignore[arg-type]

        with caplog.at_level(logging.WARNING):
            logger.validation_summary(collector)

        # Should log warning about issues
        assert '2 issues' in caplog.text

    def test_validation_summary_no_issues(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test validation_summary without issues."""
        from core.logging.protocols import Issue

        class MockIssueCollector:
            def get_issues(self) -> list[Issue]:
                return []

        logger = Logger('test.logger')
        collector = MockIssueCollector()  # type: ignore[arg-type]

        with caplog.at_level(logging.INFO):
            logger.validation_summary(collector)

        # Should log success message
        assert 'successfully' in caplog.text

    def test_log_error_with_to_dict(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test log_error with error that has to_dict method."""

        class MockError:
            def __str__(self) -> str:
                return 'Mock error'

            def to_dict(self) -> dict[str, Any]:
                return {'error_type': 'mock', 'details': 'test'}

        logger = Logger('test.logger', issue_tracker=mock_issue_tracker)
        error = MockError()

        logger.log_error(error)

        # Should track structured error
        assert len(mock_issue_tracker.structured_errors) == 1
        assert mock_issue_tracker.structured_errors[0] == {'error_type': 'mock', 'details': 'test'}

    def test_log_error_without_to_dict(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test log_error with error that doesn't have to_dict method."""
        logger = Logger('test.logger', issue_tracker=mock_issue_tracker)
        error = Exception('Simple error')

        logger.log_error(error)

        # Should not track structured error
        assert len(mock_issue_tracker.structured_errors) == 0
        assert len(mock_issue_tracker.errors) == 1


class TestConfigureLoggingEdgeCases:
    """Test configure_logging edge cases."""

    def test_configure_logging_file_without_rotation(self, temp_log_file: Path) -> None:
        """Test configure_logging with file but no rotation."""
        config = LoggingConfig(
            file=FileConfig(path=temp_log_file, max_bytes=0)  # 0 means no rotation
        )

        configure_logging(config)

        # Should create FileHandler instead of RotatingFileHandler
        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if hasattr(h, 'baseFilename')]
        assert len(file_handlers) == 1
        assert file_handlers[0].__class__.__name__ == 'FileHandler'

    def test_logging_methods_without_kwargs(self) -> None:
        """Test logging methods without kwargs to cover empty extra handling."""
        logger = Logger('test.logger')

        # These should hit the empty kwargs path
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.debug('Debug message')

    def test_logging_methods_with_translate_no_kwargs(self) -> None:
        """Test logging methods with translate but no other kwargs."""
        logger = Logger('test.logger')

        # These should hit the translate=True path with empty kwargs
        logger.info('Info message', translate=True)
        logger.warning('Warning message', translate=True)
        logger.error('Error message', translate=True)
        logger.debug('Debug message', translate=True)
