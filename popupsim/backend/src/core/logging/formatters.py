"""Logging formatters with i18n and structured output support."""

from datetime import UTC
from datetime import datetime
import json
import logging

from .protocols import Translator


class I18nFormatter(logging.Formatter):
    """Formatter with internationalization support."""

    def __init__(self, translator: Translator | None = None, fmt: str | None = None, datefmt: str | None = None):
        """Initialize internationalization formatter.

        Parameters
        ----------
        translator : Translator, optional
            Translator instance for message translation.
        fmt : str, optional
            Log format string.
        datefmt : str, optional
            Date format string.
        """
        super().__init__(fmt, datefmt)
        self._translator = translator

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with internationalization support.

        Parameters
        ----------
        record : logging.LogRecord
            Log record to format.

        Returns
        -------
        str
            Formatted log message with translation applied if needed.
        """
        # Translate message if translator available and translation requested
        if self._translator and hasattr(record, 'translate') and record.translate:
            record.msg = self._translator.translate(record.msg, **getattr(record, 'msg_args', {}))

        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, translator: Translator | None = None):
        """Initialize JSON formatter.

        Parameters
        ----------
        translator : Translator, optional
            Translator instance for message translation.
        """
        super().__init__()
        self._translator = translator

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Parameters
        ----------
        record : logging.LogRecord
            Log record to format.

        Returns
        -------
        str
            JSON-formatted log entry with timestamp, level, message, and extra fields.
        """
        # Translate message if translator available and translation requested
        if self._translator and hasattr(record, 'translate') and record.translate:
            record.msg = self._translator.translate(record.msg, **getattr(record, 'msg_args', {}))

        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                'name',
                'msg',
                'args',
                'levelname',
                'levelno',
                'pathname',
                'filename',
                'module',
                'lineno',
                'funcName',
                'created',
                'msecs',
                'relativeCreated',
                'thread',
                'threadName',
                'processName',
                'process',
                'getMessage',
                'exc_info',
                'exc_text',
                'stack_info',
                'taskName',
                'translate',
                'msg_args',
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class StructuredFormatter(logging.Formatter):
    """Human-readable structured formatter."""

    def __init__(self, translator: Translator | None = None) -> None:
        """Initialize structured formatter.

        Parameters
        ----------
        translator : Translator, optional
            Translator instance for message translation.
        """
        super().__init__()
        self._translator = translator

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in human-readable structured format.

        Parameters
        ----------
        record : logging.LogRecord
            Log record to format.

        Returns
        -------
        str
            Human-readable log message with timestamp, level, and structured extra data.
        """
        # Translate message if translator available and translation requested
        if self._translator and hasattr(record, 'translate') and record.translate:
            record.msg = self._translator.translate(record.msg, **getattr(record, 'msg_args', {}))

        # Base message
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime('%Y-%m-%d %H:%M:%S')
        base_msg = f'[{timestamp}] {record.levelname:8} {record.name}: {record.getMessage()}'

        # Add structured data if present
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in (
                'name',
                'msg',
                'args',
                'levelname',
                'levelno',
                'pathname',
                'filename',
                'module',
                'lineno',
                'funcName',
                'created',
                'msecs',
                'relativeCreated',
                'thread',
                'threadName',
                'processName',
                'process',
                'getMessage',
                'exc_info',
                'exc_text',
                'stack_info',
                'taskName',
                'translate',
                'msg_args',
            ):
                extra_data[key] = value

        if extra_data:
            base_msg += f' | {json.dumps(extra_data, default=str)}'

        # Add exception if present
        if record.exc_info:
            base_msg += f'\n{self.formatException(record.exc_info)}'

        return base_msg
