"""Integration tests for OSM extractor."""

import pytest
from unittest.mock import patch

from osm_extractor.exceptions import InvalidQueryError
from osm_extractor.exceptions import QueryTimeoutError
from osm_extractor.exceptions import RateLimitError
from osm_extractor.extractor import OSMRailwayExtractor


@pytest.mark.integration
class TestExtractorIntegration:
	"""Integration tests for OSMRailwayExtractor."""

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_bbox_success(
		self, mock_overpass, sample_bbox, mock_overpass_response
	):
		"""Test successful extraction with bounding box."""
		mock_api = mock_overpass.return_value
		mock_api.query.return_value = mock_overpass_response

		extractor = OSMRailwayExtractor()
		data = extractor.extract(sample_bbox, filter_geometry=False)

		assert 'elements' in data
		assert len(data['elements']) == 2
		assert data['elements'][0]['type'] == 'node'
		assert data['elements'][1]['type'] == 'way'

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_polygon_success(
		self, mock_overpass, sample_polygon, mock_overpass_response
	):
		"""Test successful extraction with polygon."""
		mock_api = mock_overpass.return_value
		mock_api.query.return_value = mock_overpass_response

		extractor = OSMRailwayExtractor()
		data = extractor.extract(sample_polygon, filter_geometry=False)

		assert 'elements' in data
		assert len(data['elements']) == 2

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_with_filtering(
		self, mock_overpass, sample_bbox, mock_overpass_response
	):
		"""Test extraction with geometry filtering."""
		mock_api = mock_overpass.return_value
		mock_api.query.return_value = mock_overpass_response

		extractor = OSMRailwayExtractor()
		data = extractor.extract(sample_bbox, filter_geometry=True)

		assert 'elements' in data

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_rate_limit_error(self, mock_overpass, sample_bbox):
		"""Test rate limit error handling."""
		import overpy

		mock_api = mock_overpass.return_value
		mock_api.query.side_effect = overpy.exception.OverpassTooManyRequests

		extractor = OSMRailwayExtractor()
		with pytest.raises(RateLimitError):
			extractor.extract(sample_bbox)

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_timeout_error(self, mock_overpass, sample_bbox):
		"""Test timeout error handling."""
		import overpy

		mock_api = mock_overpass.return_value
		mock_api.query.side_effect = overpy.exception.OverpassGatewayTimeout

		extractor = OSMRailwayExtractor()
		with pytest.raises(QueryTimeoutError):
			extractor.extract(sample_bbox)

	@patch('osm_extractor.extractor.overpy.Overpass')
	def test_extract_invalid_query_error(self, mock_overpass, sample_bbox):
		"""Test invalid query error handling."""
		import overpy

		mock_api = mock_overpass.return_value
		mock_api.query.side_effect = overpy.exception.OverpassBadRequest(
			'Invalid query'
		)

		extractor = OSMRailwayExtractor()
		with pytest.raises(InvalidQueryError):
			extractor.extract(sample_bbox)

	def test_build_query_bbox(self, sample_bbox):
		"""Test query building for bounding box."""
		extractor = OSMRailwayExtractor()
		query = extractor._build_overpass_query(sample_bbox)

		assert 'out:json' in query
		assert '47.37,8.54,47.39,8.56' in query
		assert 'railway' in query

	def test_build_query_polygon(self, sample_polygon):
		"""Test query building for polygon."""
		extractor = OSMRailwayExtractor()
		query = extractor._build_overpass_query(sample_polygon)

		assert 'out:json' in query
		assert 'poly:' in query
		assert 'railway' in query

	def test_custom_railway_types(self):
		"""Test extractor with custom railway types."""
		extractor = OSMRailwayExtractor(
			railway_types=['light_rail', 'tram']
		)
		assert extractor.railway_types == ['light_rail', 'tram']

	def test_custom_node_types(self):
		"""Test extractor with custom node types."""
		extractor = OSMRailwayExtractor(node_types=['signal'])
		assert extractor.node_types == ['signal']
