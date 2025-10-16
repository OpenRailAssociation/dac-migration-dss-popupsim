"""Integration tests for clipper module."""

import json
import tempfile
from pathlib import Path

import pytest

from osm_extractor.clipper import clip_data
from osm_extractor.clipper import clip_from_file
from osm_extractor.exceptions import GeometryError


@pytest.mark.integration
class TestClipperIntegration:
	"""Integration tests for clipper module."""

	def test_clip_data_bbox(self, sample_bbox, sample_osm_data):
		"""Test clipping data with bounding box."""
		result = clip_data(sample_osm_data, sample_bbox)
		assert 'elements' in result
		assert len(result['elements']) <= len(sample_osm_data['elements'])

	def test_clip_data_polygon(self, sample_polygon, sample_osm_data):
		"""Test clipping data with polygon."""
		result = clip_data(sample_osm_data, sample_polygon)
		assert 'elements' in result
		assert len(result['elements']) <= len(sample_osm_data['elements'])

	def test_clip_from_file_success(self, sample_bbox, sample_osm_data):
		"""Test clipping from file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'input.json'
			output_file = Path(tmpdir) / 'output.json'

			with open(input_file, 'w') as f:
				json.dump(sample_osm_data, f)

			clip_from_file(input_file, output_file, sample_bbox)

			assert output_file.exists()
			with open(output_file) as f:
				result = json.load(f)
			assert 'elements' in result

	def test_clip_from_file_invalid_input(self, sample_bbox):
		"""Test clipping with invalid input file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'nonexistent.json'
			output_file = Path(tmpdir) / 'output.json'

			with pytest.raises(GeometryError):
				clip_from_file(input_file, output_file, sample_bbox)
