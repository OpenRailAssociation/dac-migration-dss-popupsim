"""Async logging support."""

import asyncio
from functools import partial
from typing import Any

from .logger import Logger
from .protocols import Issue
from .protocols import IssueCollector
from .protocols import IssueTracker
from .protocols import Translator


class AsyncLogger:
    """Async wrapper for Logger with non-blocking operations."""

    def __init__(self, name: str, issue_tracker: IssueTracker | None = None, translator: Translator | None = None):
        """Initialize async logger.

        Parameters
        ----------
        name : str
            Logger name, typically module name.
        issue_tracker : IssueTracker, optional
            Issue tracker for structured error handling.
        translator : Translator, optional
            Translator for internationalization support.
        """
        self._logger = Logger(name, issue_tracker, translator)

    async def info(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log info message asynchronously.

        Parameters
        ----------
        message : str
            Log message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record.
        """
        func = partial(self._logger.info, message, translate=translate, **kwargs)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def warning(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log warning message asynchronously.

        Parameters
        ----------
        message : str
            Warning message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record and issue tracker.
        """
        func = partial(self._logger.warning, message, translate=translate, **kwargs)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def error(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log error message asynchronously.

        Parameters
        ----------
        message : str
            Error message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record and issue tracker.
        """
        func = partial(self._logger.error, message, translate=translate, **kwargs)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def debug(self, message: str, translate: bool = False, **kwargs: Any) -> None:
        """Log debug message asynchronously.

        Parameters
        ----------
        message : str
            Debug message text.
        translate : bool, default False
            Whether to translate the message using i18n.
        **kwargs : Any
            Additional context data to include in log record.
        """
        func = partial(self._logger.debug, message, translate=translate, **kwargs)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def log_issue(self, message: str, issue: Issue) -> None:
        """Log message with issue object asynchronously.

        Parameters
        ----------
        message : str
            Log message text.
        issue : Issue
            Issue object containing structured error information.
        """
        func = partial(self._logger.log_issue, message, issue)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def validation_summary(self, collector: IssueCollector) -> None:
        """Log validation summary asynchronously.

        Parameters
        ----------
        collector : IssueCollector
            Issue collector containing validation results.
        """
        func = partial(self._logger.validation_summary, collector)
        await asyncio.get_event_loop().run_in_executor(None, func)

    async def log_error(self, error: Any) -> None:
        """Log error asynchronously.

        Parameters
        ----------
        error : Any
            Error object to log, preferably with to_dict() method for structured data.
        """
        func = partial(self._logger.log_error, error)
        await asyncio.get_event_loop().run_in_executor(None, func)


def get_async_logger(
    name: str, issue_tracker: IssueTracker | None = None, translator: Translator | None = None
) -> AsyncLogger:
    """Get async logger instance.

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
    AsyncLogger
        Configured async logger instance with specified dependencies.
    """
    return AsyncLogger(name, issue_tracker, translator)
