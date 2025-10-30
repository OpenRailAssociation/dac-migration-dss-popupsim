"""Tests for async logging."""

import asyncio
import logging
from typing import Any

import pytest

from core.logging import AsyncLogger
from core.logging import get_async_logger


class MockIssueTracker:
    """Mock issue tracker for testing."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, dict]] = []
        self.errors: list[tuple[str, dict]] = []

    def track_warning(self, message: str, **context: Any) -> None:
        """Track warning."""
        self.warnings.append((message, context))

    def track_error(self, message: str, **context: Any) -> None:
        """Track error."""
        self.errors.append((message, context))
    
    def track_structured_error(self, error_dict: dict[str, Any]) -> None:
        """Track structured error."""
        pass  # Not used in async tests


@pytest.fixture
def mock_issue_tracker() -> MockIssueTracker:
    """Create mock issue tracker."""
    return MockIssueTracker()


class TestAsyncLogger:
    """Test AsyncLogger class."""

    @pytest.mark.asyncio
    async def test_async_logger_creation(self) -> None:
        """Test async logger creation."""
        logger = AsyncLogger('test.async')
        assert logger._logger._logger.name == 'test.async'

    @pytest.mark.asyncio
    async def test_async_basic_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test async logging methods."""
        logger = AsyncLogger('test.async')

        with caplog.at_level(logging.DEBUG):
            await logger.debug('Debug message')
            await logger.info('Info message')
            await logger.warning('Warning message')
            await logger.error('Error message')

        assert 'Debug message' in caplog.text
        assert 'Info message' in caplog.text
        assert 'Warning message' in caplog.text
        assert 'Error message' in caplog.text

    @pytest.mark.asyncio
    async def test_async_structured_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test async structured logging."""
        logger = AsyncLogger('test.async')

        with caplog.at_level(logging.INFO):
            await logger.info('User action', user_id='123', action='login')

        record = caplog.records[0]
        assert getattr(record, 'user_id', None) == '123'
        assert getattr(record, 'action', None) == 'login'

    @pytest.mark.asyncio
    async def test_async_issue_tracker_integration(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test async issue tracker integration."""
        logger = AsyncLogger('test.async', issue_tracker=mock_issue_tracker)

        await logger.warning('Test warning', context='test')
        await logger.error('Test error', severity='high')

        assert len(mock_issue_tracker.warnings) == 1
        assert mock_issue_tracker.warnings[0] == ('Test warning', {'context': 'test'})

        assert len(mock_issue_tracker.errors) == 1
        assert mock_issue_tracker.errors[0] == ('Test error', {'severity': 'high'})


class TestGetAsyncLogger:
    """Test get_async_logger function."""

    def test_get_async_logger_basic(self) -> None:
        """Test get_async_logger without dependencies."""
        logger = get_async_logger('test.module')

        assert isinstance(logger, AsyncLogger)
        assert logger._logger._logger.name == 'test.module'
        assert logger._logger._issue_tracker is None
        assert logger._logger._translator is None

    def test_get_async_logger_with_dependencies(self, mock_issue_tracker: MockIssueTracker) -> None:
        """Test get_async_logger with dependencies."""
        logger = get_async_logger('test.module', issue_tracker=mock_issue_tracker)

        assert isinstance(logger, AsyncLogger)
        assert logger._logger._issue_tracker is mock_issue_tracker


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Integration tests for async logging."""

    async def test_concurrent_async_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test concurrent async logging operations."""
        logger = AsyncLogger('test.concurrent')

        async def log_messages(prefix: str) -> None:
            await logger.info(f'{prefix} message 1')
            await logger.info(f'{prefix} message 2')

        with caplog.at_level(logging.INFO):
            # Run concurrent logging tasks
            await asyncio.gather(log_messages('Task1'), log_messages('Task2'), log_messages('Task3'))

        # Should have 6 messages total
        assert len(caplog.records) == 6
        assert 'Task1 message 1' in caplog.text
        assert 'Task2 message 1' in caplog.text
        assert 'Task3 message 1' in caplog.text
