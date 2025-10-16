"""Tests for data models."""

import pytest

from osm_extractor.models import BoundingBox
from osm_extractor.models import Polygon


class TestBoundingBox:
	"""Tests for BoundingBox model."""

	def test_creation(self):
		"""Test bounding box creation."""
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		assert bbox.south == 47.37
		assert bbox.west == 8.54
		assert bbox.north == 47.39
		assert bbox.east == 8.56

	def test_expand(self):
		"""Test bounding box expansion."""
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		expanded = bbox.expand(0.01)
		assert expanded.south == 47.36
		assert expanded.west == 8.53
		assert expanded.north == 47.40
		assert expanded.east == 8.57

	def test_immutable(self):
		"""Test that bounding box is immutable."""
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		with pytest.raises(AttributeError):
			bbox.south = 47.38


class TestPolygon:
	"""Tests for Polygon model."""

	def test_creation(self):
		"""Test polygon creation."""
		coords = [(47.37, 8.54), (47.39, 8.54), (47.39, 8.56)]
		poly = Polygon(coordinates=coords)
		assert len(poly.coordinates) == 3
		assert poly.coordinates[0] == (47.37, 8.54)

	def test_to_bbox(self):
		"""Test polygon to bounding box conversion."""
		coords = [(47.37, 8.54), (47.39, 8.54), (47.39, 8.56), (47.37, 8.56)]
		poly = Polygon(coordinates=coords)
		bbox = poly.to_bbox()
		assert bbox.south == 47.37
		assert bbox.west == 8.54
		assert bbox.north == 47.39
		assert bbox.east == 8.56

	def test_immutable(self):
		"""Test that polygon is immutable."""
		coords = [(47.37, 8.54), (47.39, 8.54)]
		poly = Polygon(coordinates=coords)
		with pytest.raises(AttributeError):
			poly.coordinates = []
