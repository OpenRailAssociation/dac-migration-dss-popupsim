"""Tests for retry logic."""

from unittest.mock import MagicMock

import pytest

from osm_extractor.exceptions import ExtractionError
from osm_extractor.retry import exponential_backoff


class TestRetry:
	"""Tests for retry logic."""

	def test_success_first_attempt(self):
		"""Test successful execution on first attempt."""
		mock_func = MagicMock(return_value='success')
		wrapped = exponential_backoff(mock_func, max_retries=3)

		result = wrapped()

		assert result == 'success'
		assert mock_func.call_count == 1

	def test_success_after_retries(self):
		"""Test successful execution after retries."""
		mock_func = MagicMock(
			side_effect=[
				ExtractionError('fail1'),
				ExtractionError('fail2'),
				'success',
			]
		)
		wrapped = exponential_backoff(
			mock_func, max_retries=3, base_delay=0.01
		)

		result = wrapped()

		assert result == 'success'
		assert mock_func.call_count == 3

	def test_all_retries_exhausted(self):
		"""Test all retries exhausted."""
		mock_func = MagicMock(side_effect=ExtractionError('persistent'))
		wrapped = exponential_backoff(
			mock_func, max_retries=2, base_delay=0.01
		)

		with pytest.raises(ExtractionError, match='persistent'):
			wrapped()

		assert mock_func.call_count == 3
