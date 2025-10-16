"""Retry logic with exponential backoff."""

import logging
import time
from typing import Any
from typing import Callable
from typing import TypeVar

from .exceptions import ExtractionError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def exponential_backoff(
	func: Callable[..., T],
	max_retries: int = 3,
	base_delay: float = 1.0,
	max_delay: float = 60.0,
) -> Callable[..., T]:
	"""Retry function with exponential backoff.

	Parameters
	----------
	func : Callable
		Function to retry
	max_retries : int
		Maximum retry attempts
	base_delay : float
		Initial delay in seconds
	max_delay : float
		Maximum delay in seconds

	Returns
	-------
	Callable
		Wrapped function with retry logic
	"""

	def wrapper(*args: Any, **kwargs: Any) -> T:
		last_exception = None
		for attempt in range(max_retries + 1):
			try:
				return func(*args, **kwargs)
			except ExtractionError as e:
				last_exception = e
				if attempt < max_retries:
					delay = min(base_delay * (2**attempt), max_delay)
					logger.warning(
						'Attempt %d/%d failed: %s. Retrying in %.1fs...',
						attempt + 1,
						max_retries + 1,
						e,
						delay,
					)
					time.sleep(delay)
				else:
					logger.error('All %d attempts failed', max_retries + 1)

		raise last_exception  # type: ignore

	return wrapper
