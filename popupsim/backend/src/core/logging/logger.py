"""Logging system with protocol-based dependency injection."""

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from typing import Any

from .formatters import JsonFormatter
from .formatters import StructuredFormatter
from .handlers import FileHandler
from .handlers import RotatingFileHandler
from .handlers import StructuredHandler
from .protocols import Issue
from .protocols import IssueCollector
from .protocols import IssueTracker
from .protocols import Translator


class FormatType(Enum):
    """Log format types."""

    STRUCTURED = 'structured'
    JSON = 'json'


@dataclass
class FileConfig:
    """File logging configuration."""

    path: Path | None = None
    max_bytes: int = 50 * 1024 * 1024  # 50MB
    backup_count: int = 5


@dataclass
class LoggingConfig:
    """Complete logging system configuration."""

    level: int = logging.INFO
    format_type: FormatType = FormatType.STRUCTURED
    console_output: bool = True
    file: FileConfig | None = None
    translator: Translator | None = None


class Logger:
    """Logger with full feature support via protocols."""

    def __init__(self, name: str, issue_tracker: IssueTracker | None = None, translator: Translator | None = None):
        """Initialize logger.

        Parameters
        ----------
        name : str
            Logger name, typically module name.
        issue_tracker : IssueTracker, optional
            Issue tracker for structured error handling.
        translator : Translator, optional
            Translator for internationalization support.
        """
        self._logger = logging.getLogger(name)
        self._issue_tracker = issue_tracker
        self._translator = translator

    def info(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log info message with optional context.

        Parameters
        ----------
        message : str
            Log message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record.
        """
        extra = kwargs.copy() if kwargs else {}
        if translate:
            extra['translate'] = True
            extra['msg_args'] = kwargs
        self._logger.info(message, extra=extra if extra else None)

    def warning(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log warning message with optional context.

        Parameters
        ----------
        message : str
            Warning message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record and issue tracker.
        """
        extra = kwargs.copy() if kwargs else {}
        if translate:
            extra['translate'] = True
            extra['msg_args'] = kwargs
        self._logger.warning(message, extra=extra if extra else None)
        if self._issue_tracker:
            self._issue_tracker.track_warning(message, **kwargs)

    def error(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log error message with optional context.

        Parameters
        ----------
        message : str
            Error message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record and issue tracker.
        """
        extra = kwargs.copy() if kwargs else {}
        if translate:
            extra['translate'] = True
            extra['msg_args'] = kwargs
        self._logger.error(message, extra=extra if extra else None)
        if self._issue_tracker:
            self._issue_tracker.track_error(message, **kwargs)

    def debug(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log debug message with optional context.

        Parameters
        ----------
        message : str
            Debug message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record.
        """
        extra = kwargs.copy() if kwargs else {}
        if translate:
            extra['translate'] = True
            extra['msg_args'] = kwargs
        self._logger.debug(message, extra=extra if extra else None)

    def log_issue(self, message: str, issue: Issue) -> None:
        """Log message with issue object.

        Parameters
        ----------
        message : str
            Log message text.
        issue : Issue
            Issue object containing structured error information.
        """
        self.error(message, issue=issue)

    def validation_summary(self, collector: IssueCollector) -> None:
        """Log validation summary from issue collector.

        Parameters
        ----------
        collector : IssueCollector
            Issue collector containing validation results.
        """
        issues = collector.get_issues()
        if issues:
            self.warning(f'Validation completed with {len(issues)} issues', issues=collector)
        else:
            self.info('Validation completed successfully')

    def log_error(self, error: Any) -> None:
        """Log PopUpSimError with full context when available.

        Parameters
        ----------
        error : Any
            Error object to log, preferably with to_dict() method for structured data.
        """
        self.error(str(error))
        if self._issue_tracker and hasattr(error, 'to_dict'):
            self._issue_tracker.track_structured_error(error.to_dict())


def configure_logging(config: LoggingConfig | None = None) -> None:
    """Configure logging system.

    Parameters
    ----------
    config : LoggingConfig, optional
        Logging configuration. Uses defaults if None.
    """
    if config is None:
        config = LoggingConfig()

    root_logger = logging.getLogger()
    root_logger.setLevel(config.level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    formatter: JsonFormatter | StructuredFormatter
    if config.format_type == FormatType.JSON:
        formatter = JsonFormatter(config.translator)
    else:
        formatter = StructuredFormatter(config.translator)

    # Console handler
    if config.console_output:
        console_handler = StructuredHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if config.file and config.file.path:
        file_handler: FileHandler | RotatingFileHandler
        if config.file.max_bytes > 0:
            file_handler = RotatingFileHandler(
                config.file.path, max_bytes=config.file.max_bytes, backup_count=config.file.backup_count
            )
        else:
            file_handler = FileHandler(config.file.path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str, issue_tracker: IssueTracker | None = None, translator: Translator | None = None) -> Logger:
    """Get logger instance for module.

    Parameters
    ----------
    name : str
        Logger name, typically module name (__name__).
    issue_tracker : IssueTracker, optional
        Issue tracker for structured error handling.
    translator : Translator, optional
        Translator for internationalization support.

    Returns
    -------
    Logger
        Configured logger instance with specified dependencies.
    """
    return Logger(name, issue_tracker, translator)
