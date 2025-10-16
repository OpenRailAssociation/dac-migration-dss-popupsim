"""Integration tests for plotter module."""

import json
import tempfile
from pathlib import Path

import pytest

from osm_extractor.exceptions import PlottingError
from osm_extractor.plotter import plot_data
from osm_extractor.plotter import plot_from_file


@pytest.mark.integration
class TestPlotterIntegration:
	"""Integration tests for plotter module."""

	def test_plot_data_geographic(self, sample_osm_data):
		"""Test plotting geographic data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			output_file = Path(tmpdir) / 'plot.png'
			plot_data(sample_osm_data, output_file)
			assert output_file.exists()

	def test_plot_data_projected(self):
		"""Test plotting projected data."""
		projected_data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'x': 1000.0, 'y': 2000.0},
						{'x': 1100.0, 'y': 2100.0},
					],
					'tags': {'railway': 'rail'},
				},
				{
					'type': 'node',
					'id': 2,
					'x': 1050.0,
					'y': 2050.0,
					'tags': {'railway': 'switch'},
				},
			]
		}
		with tempfile.TemporaryDirectory() as tmpdir:
			output_file = Path(tmpdir) / 'plot.png'
			plot_data(projected_data, output_file)
			assert output_file.exists()

	def test_plot_data_with_boundary(self, sample_osm_data, sample_bbox):
		"""Test plotting with boundary overlay."""
		with tempfile.TemporaryDirectory() as tmpdir:
			output_file = Path(tmpdir) / 'plot.png'
			plot_data(sample_osm_data, output_file, boundary=sample_bbox)
			assert output_file.exists()

	def test_plot_data_without_nodes(self, sample_osm_data):
		"""Test plotting without node markers."""
		with tempfile.TemporaryDirectory() as tmpdir:
			output_file = Path(tmpdir) / 'plot.png'
			plot_data(sample_osm_data, output_file, show_nodes=False)
			assert output_file.exists()

	def test_plot_from_file_success(self, sample_osm_data):
		"""Test plotting from file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'data.json'
			output_file = Path(tmpdir) / 'plot.png'

			with open(input_file, 'w') as f:
				json.dump(sample_osm_data, f)

			plot_from_file(input_file, output_file)
			assert output_file.exists()

	def test_plot_from_file_invalid_input(self):
		"""Test plotting with invalid input file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'nonexistent.json'
			output_file = Path(tmpdir) / 'plot.png'

			with pytest.raises(PlottingError):
				plot_from_file(input_file, output_file)
