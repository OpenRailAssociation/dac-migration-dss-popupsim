"""Tests for projector module."""

import pytest

from osm_extractor.projector import project_data


class TestProjector:
	"""Tests for coordinate projection."""

	def test_project_nodes(self):
		"""Test projecting node coordinates."""
		data = {
			'elements': [
				{'type': 'node', 'id': 1, 'lat': 47.38, 'lon': 8.55, 'tags': {}}
			]
		}
		projected = project_data(data)
		assert len(projected['elements']) == 1
		node = projected['elements'][0]
		assert 'x' in node
		assert 'y' in node
		assert 'lat' in node
		assert 'lon' in node
		assert isinstance(node['x'], float)
		assert isinstance(node['y'], float)

	def test_project_ways(self):
		"""Test projecting way geometry."""
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
		projected = project_data(data)
		assert len(projected['elements']) == 1
		way = projected['elements'][0]
		assert len(way['geometry']) == 2
		for node in way['geometry']:
			assert 'x' in node
			assert 'y' in node
			assert 'lat' in node
			assert 'lon' in node

	def test_preserves_original_data(self):
		"""Test that original lat/lon are preserved."""
		data = {
			'elements': [
				{'type': 'node', 'id': 1, 'lat': 47.38, 'lon': 8.55, 'tags': {}}
			]
		}
		projected = project_data(data)
		node = projected['elements'][0]
		assert node['lat'] == 47.38
		assert node['lon'] == 8.55
