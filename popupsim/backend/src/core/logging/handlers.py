"""Custom logging handlers for PopUpSim."""

import logging
import logging.handlers
from pathlib import Path

from .protocols import Issue
from .protocols import IssueCollector


def _extract_issue_data(record: logging.LogRecord) -> None:
    """Extract structured data from Issue and IssueCollector objects.

    Parameters
    ----------
    record : logging.LogRecord
        Log record to process, potentially containing Issue or IssueCollector objects.
    """
    # Handle Issue objects
    if hasattr(record, 'issue') and isinstance(record.issue, Issue):
        issue = record.issue
        record.error_code = issue.error_code
        record.severity = issue.severity.value
        record.category = issue.category.value
        record.component = issue.component
        record.field_path = issue.field_path
        record.context = issue.context

    # Handle IssueCollector objects
    if hasattr(record, 'issues') and isinstance(record.issues, IssueCollector):
        collector = record.issues
        record.issue_count = len(collector.get_issues())
        record.error_count = len([i for i in collector.get_issues() if i.severity.value in ['HIGH', 'CRITICAL']])


class StructuredHandler(logging.StreamHandler):
    """Handler that supports structured logging with extra fields."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record with structured data support.

        Parameters
        ----------
        record : logging.LogRecord
            Log record to emit, potentially containing Issue or IssueCollector objects.
        """
        _extract_issue_data(record)
        super().emit(record)


class FileHandler(logging.FileHandler):
    """File handler with automatic directory creation."""

    def __init__(self, filename: Path, mode: str = 'a', encoding: str = 'utf-8', delay: bool = False):
        """Initialize file handler with automatic directory creation.

        Parameters
        ----------
        filename : Path
            Path to the log file.
        mode : str, default 'a'
            File open mode.
        encoding : str, default 'utf-8'
            File encoding.
        delay : bool, default False
            Whether to delay file opening.
        """
        # Ensure directory exists
        filename.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(str(filename), mode, encoding, delay)


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler with automatic directory creation."""

    def __init__(self, filename: Path, max_bytes: int = 0, backup_count: int = 0):
        """Initialize rotating file handler with automatic directory creation.

        Parameters
        ----------
        filename : Path
            Path to the log file.
        max_bytes : int, default 0
            Maximum file size before rotation.
        backup_count : int, default 0
            Number of backup files to keep.
        """
        # Ensure directory exists
        filename.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(str(filename), maxBytes=max_bytes, backupCount=backup_count)
