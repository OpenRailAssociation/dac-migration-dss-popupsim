"""Protocols for logging system dependency injection."""

from typing import Any
from typing import Protocol
from typing import runtime_checkable


@runtime_checkable
class Issue(Protocol):
    """Protocol for issue objects."""

    @property
    def error_code(self) -> str:
        """Get issue error code.

        Returns
        -------
        str
            Unique error code identifier.
        """

    @property
    def severity(self) -> Any:
        """Get issue severity level.

        Returns
        -------
        Any
            Severity level (enum or string).
        """

    @property
    def category(self) -> Any:
        """Get issue category.

        Returns
        -------
        Any
            Issue category (enum or string).
        """

    @property
    def component(self) -> str:
        """Get component where issue occurred.

        Returns
        -------
        str
            Component name.
        """

    @property
    def field_path(self) -> str:
        """Get field path where issue occurred.

        Returns
        -------
        str
            Dot-separated field path.
        """

    @property
    def context(self) -> dict:
        """Get additional issue context.

        Returns
        -------
        dict
            Context data dictionary.
        """


@runtime_checkable
class IssueCollector(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for issue collector objects."""

    def get_issues(self) -> list[Issue]:
        """Get collected issues.

        Returns
        -------
        list[Issue]
            List of collected issues.
        """


class Translator(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for i18n translation."""

    def translate(self, message: str, **kwargs: Any) -> str:
        """Translate message with parameters.

        Parameters
        ----------
        message : str
            Message key or text to translate.
        **kwargs : Any
            Translation parameters.

        Returns
        -------
        str
            Translated message.
        """


class IssueTracker(Protocol):
    """Protocol for issue tracking integration."""

    def track_warning(self, message: str, **context: Any) -> None:
        """Track warning with context.

        Parameters
        ----------
        message : str
            Warning message text.
        **context : Any
            Additional context data.
        """

    def track_error(self, message: str, **context: Any) -> None:
        """Track error with context.

        Parameters
        ----------
        message : str
            Error message text.
        **context : Any
            Additional context data.
        """

    def track_structured_error(self, error_dict: dict) -> None:
        """Track structured error data.

        Parameters
        ----------
        error_dict : dict
            Structured error data dictionary.
        """
