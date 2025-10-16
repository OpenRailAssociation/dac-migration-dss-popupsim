"""Tests for geometry operations."""

import pytest

from osm_extractor.geometry import filter_osm_data
from osm_extractor.models import BoundingBox
from osm_extractor.models import Polygon


class TestFilterOSMData:
	"""Tests for OSM data filtering."""

	def test_filter_bbox_nodes(self):
		"""Test filtering nodes with bounding box."""
		data = {
			'elements': [
				{'type': 'node', 'id': 1, 'lat': 47.38, 'lon': 8.55, 'tags': {}},
				{'type': 'node', 'id': 2, 'lat': 47.40, 'lon': 8.57, 'tags': {}},
			]
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		filtered = filter_osm_data(data, bbox)
		assert len(filtered['elements']) == 1
		assert filtered['elements'][0]['id'] == 1

	def test_filter_polygon_nodes(self):
		"""Test filtering nodes with polygon."""
		data = {
			'elements': [
				{'type': 'node', 'id': 1, 'lat': 47.38, 'lon': 8.55, 'tags': {}},
				{'type': 'node', 'id': 2, 'lat': 47.40, 'lon': 8.57, 'tags': {}},
			]
		}
		poly = Polygon(
			coordinates=[(47.37, 8.54), (47.39, 8.54), (47.39, 8.56), (47.37, 8.56)]
		)
		filtered = filter_osm_data(data, poly)
		assert len(filtered['elements']) == 1
		assert filtered['elements'][0]['id'] == 1

	def test_filter_ways(self):
		"""Test filtering ways."""
		data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'lat': 47.38, 'lon': 8.55},
						{'lat': 47.385, 'lon': 8.555},
					],
					'tags': {},
				}
			]
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		filtered = filter_osm_data(data, bbox)
		assert len(filtered['elements']) == 1
		assert filtered['elements'][0]['type'] == 'way'

	def test_filter_removes_outside_ways(self):
		"""Test that ways completely outside boundary are removed."""
		data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'lat': 47.40, 'lon': 8.57},
						{'lat': 47.41, 'lon': 8.58},
					],
					'tags': {},
				}
			]
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		filtered = filter_osm_data(data, bbox)
		assert len(filtered['elements']) == 0
