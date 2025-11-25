"""Decorators for internationalization support.

This module provides decorators to mark functions and classes as
containing translatable content for documentation and future tooling
integration.
"""

from collections.abc import Callable
from typing import Any
from typing import TypeVar

F = TypeVar('F', bound=Callable[..., Any])


def translatable(message_key: str) -> Callable[[F], F]:
    """Mark functions or classes as containing translatable content.

    This decorator adds metadata to functions/classes to indicate they
    contain translatable strings. Useful for documentation, testing
    and future tooling.

    Parameters
    ----------
    message_key : str
        Translation key identifier for the function/class

    Returns
    -------
    Callable[[F], F]
        Decorator function that adds message_key attribute

    Examples
    --------
    >>> @translatable('validation.workshop.capacity')
    ... def validate_capacity():
    ...     return _('Workshop capacity exceeded')
    >>> validate_capacity.message_key
    'validation.workshop.capacity'

    Notes
    -----
    This decorator is currently used for metadata only and does not
    affect the actual translation process. It is intended for future
    tooling for:

    - Documentation generation
    - Translation coverage analysis
    - IDE integration
    - Testing validation
    """

    def decorator(decorated_obj: F) -> F:
        # Use public attribute instead of protected
        decorated_obj.message_key = message_key
        return decorated_obj

    return decorator
