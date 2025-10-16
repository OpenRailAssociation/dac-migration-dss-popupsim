"""Tests for coordinate projection."""

import pytest

from osm_extractor.projection import elliptical_mercator


class TestEllipticalMercator:
	"""Tests for elliptical Mercator projection."""

	def test_projection(self):
		"""Test basic coordinate projection."""
		x, y = elliptical_mercator(47.37, 8.54)
		assert isinstance(x, float)
		assert isinstance(y, float)
		assert x > 0
		assert y > 0

	def test_equator(self):
		"""Test projection at equator."""
		x, y = elliptical_mercator(0.0, 0.0)
		assert x == 0.0
		assert abs(y) < 1.0

	def test_latitude_clamping(self):
		"""Test that extreme latitudes are clamped."""
		x1, y1 = elliptical_mercator(90.0, 0.0)
		x2, y2 = elliptical_mercator(89.5, 0.0)
		assert y1 == y2

		x3, y3 = elliptical_mercator(-90.0, 0.0)
		x4, y4 = elliptical_mercator(-89.5, 0.0)
		assert y3 == y4

	def test_longitude_scaling(self):
		"""Test longitude scaling."""
		x1, _ = elliptical_mercator(0.0, 0.0)
		x2, _ = elliptical_mercator(0.0, 1.0)
		assert x2 > x1
