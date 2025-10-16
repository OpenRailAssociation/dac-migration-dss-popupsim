"""Pytest configuration and fixtures."""

import matplotlib
import pytest

matplotlib.use('Agg')


@pytest.fixture
def sample_bbox():
	"""Sample bounding box for testing."""
	from osm_extractor.models import BoundingBox

	return BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)


@pytest.fixture
def sample_polygon():
	"""Sample polygon for testing."""
	from osm_extractor.models import Polygon

	return Polygon(
		coordinates=[
			(47.37, 8.54),
			(47.39, 8.54),
			(47.39, 8.56),
			(47.37, 8.56),
		]
	)


@pytest.fixture
def sample_osm_data():
	"""Sample OSM data for testing."""
	return {
		'elements': [
			{
				'type': 'node',
				'id': 1,
				'lat': 47.38,
				'lon': 8.55,
				'tags': {'railway': 'switch'},
			},
			{
				'type': 'way',
				'id': 2,
				'geometry': [
					{'lat': 47.38, 'lon': 8.55},
					{'lat': 47.385, 'lon': 8.555},
				],
				'tags': {'railway': 'rail'},
			},
		]
	}


@pytest.fixture
def mock_overpass_response():
	"""Mock Overpass API response."""
	from unittest.mock import MagicMock

	result = MagicMock()
	result.nodes = [
		MagicMock(id=1, lat=47.38, lon=8.55, tags={'railway': 'switch'})
	]
	result.ways = [
		MagicMock(
			id=2,
			tags={'railway': 'rail'},
			nodes=[
				MagicMock(lat=47.38, lon=8.55),
				MagicMock(lat=47.385, lon=8.555),
			],
		)
	]
	return result
