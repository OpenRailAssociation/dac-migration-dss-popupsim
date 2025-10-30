"""Tests for logging handlers."""

from collections.abc import Generator
import logging
from pathlib import Path
import tempfile
import pytest

from core.logging.handlers import FileHandler
from core.logging.handlers import RotatingFileHandler
from core.logging.handlers import StructuredHandler


class MockSeverity:
    """Mock severity for testing."""
    def __init__(self, value: str) -> None:
        self.value = value


class MockCategory:
    """Mock category for testing."""
    def __init__(self, value: str) -> None:
        self.value = value


class MockIssue:
    """Mock issue for testing."""

    def __init__(self) -> None:
        self.error_code = 'TEST_001'
        self.severity = MockSeverity('HIGH')
        self.category = MockCategory('VALIDATION')
        self.component = 'test_component'
        self.field_path = 'test.field'
        self.context = {'key': 'value'}


class MockIssueCollector:
    """Mock issue collector for testing."""

    def __init__(self, issues: list[MockIssue]) -> None:
        self._issues = issues

    def get_issues(self) -> list[MockIssue]:
        """Get issues."""
        return self._issues


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_issue() -> MockIssue:
    """Create mock issue."""
    return MockIssue()


@pytest.fixture
def mock_issue_collector() -> MockIssueCollector:
    """Create mock issue collector."""
    return MockIssueCollector([MockIssue(), MockIssue()])


class TestFileHandler:
    """Test FileHandler."""

    def test_file_creation(self, temp_dir: Path) -> None:
        """Test file handler creates file and directories."""
        log_file = temp_dir / 'subdir' / 'test.log'
        handler = FileHandler(log_file)

        # Directory should be created
        assert log_file.parent.exists()

        # Test logging
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        handler.emit(record)
        handler.close()

        # File should exist and contain content
        assert log_file.exists()
        assert log_file.stat().st_size > 0

    def test_custom_encoding(self, temp_dir: Path) -> None:
        """Test file handler with custom encoding."""
        log_file = temp_dir / 'test.log'
        handler = FileHandler(log_file, encoding='utf-8')

        assert handler.encoding == 'utf-8'
        handler.close()


class TestRotatingFileHandler:
    """Test RotatingFileHandler."""

    def test_file_creation(self, temp_dir: Path) -> None:
        """Test rotating file handler creates file and directories."""
        log_file = temp_dir / 'subdir' / 'test.log'
        handler = RotatingFileHandler(log_file, max_bytes=1024, backup_count=3)

        # Directory should be created
        assert log_file.parent.exists()

        # Test logging
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        handler.emit(record)
        handler.close()

        # File should exist
        assert log_file.exists()

    def test_rotation_parameters(self, temp_dir: Path) -> None:
        """Test rotation parameters are set correctly."""
        log_file = temp_dir / 'test.log'
        handler = RotatingFileHandler(log_file, max_bytes=2048, backup_count=5)

        assert handler.maxBytes == 2048
        assert handler.backupCount == 5
        handler.close()


class TestStructuredHandler:
    """Test StructuredHandler."""

    def test_basic_emit(self) -> None:
        """Test basic emit functionality."""
        handler = StructuredHandler()

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        # Should not raise any exceptions
        handler.emit(record)

    def test_issue_handling(self, mock_issue: MockIssue) -> None:
        """Test handling of Issue objects."""
        handler = StructuredHandler()

        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        # Add issue to record
        record.issue = mock_issue

        handler.emit(record)

        # Check that issue fields were extracted
        assert getattr(record, 'error_code', None) == 'TEST_001'
        assert getattr(record, 'severity', None) == 'HIGH'
        assert getattr(record, 'category', None) == 'VALIDATION'
        assert getattr(record, 'component', None) == 'test_component'
        assert getattr(record, 'field_path', None) == 'test.field'
        assert getattr(record, 'context', None) == {'key': 'value'}

    def test_issue_collector_handling(self, mock_issue_collector: MockIssueCollector) -> None:
        """Test handling of IssueCollector objects."""
        handler = StructuredHandler()

        record = logging.LogRecord(
            name='test', level=logging.WARNING, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        # Add issue collector to record
        record.issues = mock_issue_collector

        handler.emit(record)

        # Check that collector fields were extracted
        assert getattr(record, 'issue_count', None) == 2
        assert getattr(record, 'error_count', None) == 2  # Both mock issues have HIGH severity

    def test_no_issue_handling(self) -> None:
        """Test normal operation without issues."""
        handler = StructuredHandler()

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        # Should not raise any exceptions
        handler.emit(record)

        # Should not have issue-related attributes
        assert not hasattr(record, 'error_code')
        assert not hasattr(record, 'issue_count')


@pytest.mark.unit
class TestHandlerIntegration:
    """Integration tests for handlers."""

    def test_file_handler_with_formatter(self, temp_dir: Path) -> None:
        """Test file handler with formatter."""
        from core.logging.formatters import StructuredFormatter

        log_file = temp_dir / 'test.log'
        handler = FileHandler(log_file)
        handler.setFormatter(StructuredFormatter())

        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None
        )

        handler.emit(record)
        handler.close()

        # Check file content
        content = log_file.read_text(encoding='utf-8')
        assert 'Test message' in content
        assert 'INFO' in content

    def test_structured_handler_with_issues(self, mock_issue: MockIssue) -> None:
        """Test structured handler with issue processing."""
        from core.logging.formatters import JsonFormatter

        handler = StructuredHandler()
        handler.setFormatter(JsonFormatter())

        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0, msg='Error occurred', args=(), exc_info=None
        )

        record.issue = mock_issue

        # Should process issue and format without errors
        handler.emit(record)

        # Verify issue data was extracted
        assert getattr(record, 'error_code', None) == 'TEST_001'
        assert getattr(record, 'severity', None) == 'HIGH'
