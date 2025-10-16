"""Tests for validators."""

import pytest

from osm_extractor.validators import ValidationError
from osm_extractor.validators import validate_bbox
from osm_extractor.validators import validate_coordinates
from osm_extractor.validators import validate_polygon


class TestValidators:
	"""Tests for validation functions."""

	def test_valid_coordinates(self):
		"""Test valid coordinates."""
		validate_coordinates(47.38, 8.55)
		validate_coordinates(0, 0)
		validate_coordinates(-90, -180)
		validate_coordinates(90, 180)

	def test_invalid_latitude(self):
		"""Test invalid latitude."""
		with pytest.raises(ValidationError, match='Latitude.*out of range'):
			validate_coordinates(91, 0)
		with pytest.raises(ValidationError, match='Latitude.*out of range'):
			validate_coordinates(-91, 0)

	def test_invalid_longitude(self):
		"""Test invalid longitude."""
		with pytest.raises(ValidationError, match='Longitude.*out of range'):
			validate_coordinates(0, 181)
		with pytest.raises(ValidationError, match='Longitude.*out of range'):
			validate_coordinates(0, -181)

	def test_valid_bbox(self):
		"""Test valid bounding box."""
		validate_bbox(47.37, 8.54, 47.39, 8.56)

	def test_bbox_south_north_inverted(self):
		"""Test bbox with south >= north."""
		with pytest.raises(ValidationError, match='South.*North'):
			validate_bbox(47.39, 8.54, 47.37, 8.56)

	def test_bbox_west_east_inverted(self):
		"""Test bbox with west >= east."""
		with pytest.raises(ValidationError, match='West.*East'):
			validate_bbox(47.37, 8.56, 47.39, 8.54)

	def test_valid_polygon(self):
		"""Test valid polygon."""
		coords = [(47.37, 8.54), (47.39, 8.54), (47.39, 8.56)]
		validate_polygon(coords)

	def test_polygon_too_few_points(self):
		"""Test polygon with too few points."""
		with pytest.raises(ValidationError, match='at least 3 points'):
			validate_polygon([(47.37, 8.54), (47.39, 8.54)])

	def test_polygon_invalid_coordinate(self):
		"""Test polygon with invalid coordinate."""
		coords = [(47.37, 8.54), (91, 8.54), (47.39, 8.56)]
		with pytest.raises(ValidationError, match='Point 1'):
			validate_polygon(coords)
