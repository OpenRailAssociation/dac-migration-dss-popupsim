"""Tests for custom exceptions."""

import pytest

from osm_extractor.exceptions import ExtractionError
from osm_extractor.exceptions import GeometryError
from osm_extractor.exceptions import InvalidQueryError
from osm_extractor.exceptions import OSMExtractorError
from osm_extractor.exceptions import PlottingError
from osm_extractor.exceptions import ProjectionError
from osm_extractor.exceptions import QueryTimeoutError
from osm_extractor.exceptions import RateLimitError


class TestExceptions:
	"""Tests for exception hierarchy."""

	def test_base_exception(self):
		"""Test base exception."""
		with pytest.raises(OSMExtractorError):
			raise OSMExtractorError('Test error')

	def test_extraction_error(self):
		"""Test extraction error is subclass of base."""
		assert issubclass(ExtractionError, OSMExtractorError)
		with pytest.raises(OSMExtractorError):
			raise ExtractionError('Test error')

	def test_rate_limit_error(self):
		"""Test rate limit error is subclass of extraction error."""
		assert issubclass(RateLimitError, ExtractionError)
		with pytest.raises(ExtractionError):
			raise RateLimitError('Test error')

	def test_query_timeout_error(self):
		"""Test query timeout error is subclass of extraction error."""
		assert issubclass(QueryTimeoutError, ExtractionError)
		with pytest.raises(ExtractionError):
			raise QueryTimeoutError('Test error')

	def test_invalid_query_error(self):
		"""Test invalid query error is subclass of extraction error."""
		assert issubclass(InvalidQueryError, ExtractionError)
		with pytest.raises(ExtractionError):
			raise InvalidQueryError('Test error')

	def test_geometry_error(self):
		"""Test geometry error is subclass of base."""
		assert issubclass(GeometryError, OSMExtractorError)
		with pytest.raises(OSMExtractorError):
			raise GeometryError('Test error')

	def test_projection_error(self):
		"""Test projection error is subclass of base."""
		assert issubclass(ProjectionError, OSMExtractorError)
		with pytest.raises(OSMExtractorError):
			raise ProjectionError('Test error')

	def test_plotting_error(self):
		"""Test plotting error is subclass of base."""
		assert issubclass(PlottingError, OSMExtractorError)
		with pytest.raises(OSMExtractorError):
			raise PlottingError('Test error')
