"""Edge case tests for geometry operations."""

from osm_extractor.geometry import filter_way_geometry
from osm_extractor.models import BoundingBox


class TestGeometryEdgeCases:
	"""Edge case tests for geometry filtering."""

	def test_way_without_geometry(self):
		"""Test way without geometry field."""
		way = {'type': 'way', 'id': 1, 'tags': {'railway': 'rail'}}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		result = filter_way_geometry(way, bbox)
		assert result == way

	def test_way_single_point(self):
		"""Test way with single point."""
		way = {
			'type': 'way',
			'id': 1,
			'geometry': [{'lat': 47.38, 'lon': 8.55}],
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		result = filter_way_geometry(way, bbox)
		assert result == way

	def test_way_multilinestring_intersection(self):
		"""Test way crossing boundary multiple times."""
		way = {
			'type': 'way',
			'id': 1,
			'geometry': [
				{'lat': 47.36, 'lon': 8.55},
				{'lat': 47.38, 'lon': 8.55},
				{'lat': 47.40, 'lon': 8.55},
			],
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		result = filter_way_geometry(way, bbox)
		assert result is not None
		assert 'geometry' in result
