"""Edge case tests for plotter."""

import tempfile
from pathlib import Path

from osm_extractor.models import BoundingBox
from osm_extractor.models import Polygon
from osm_extractor.plotter import plot_data


class TestPlotterEdgeCases:
	"""Edge case tests for plotter."""

	def test_plot_with_polygon_boundary_geographic(self):
		"""Test plotting with polygon boundary on geographic data."""
		data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'lat': 47.38, 'lon': 8.55},
						{'lat': 47.385, 'lon': 8.555},
					],
					'tags': {'railway': 'rail'},
				}
			]
		}
		poly = Polygon(
			coordinates=[
				(47.37, 8.54),
				(47.39, 8.54),
				(47.39, 8.56),
				(47.37, 8.56),
			]
		)
		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'plot.png'
			plot_data(data, output, boundary=poly)
			assert output.exists()

	def test_plot_with_bbox_boundary_projected(self):
		"""Test plotting with bbox boundary on projected data."""
		data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'x': 1000.0, 'y': 2000.0},
						{'x': 1100.0, 'y': 2100.0},
					],
					'tags': {'railway': 'rail'},
				}
			]
		}
		bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)
		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'plot.png'
			plot_data(data, output, boundary=bbox)
			assert output.exists()

	def test_plot_with_polygon_boundary_projected(self):
		"""Test plotting with polygon boundary on projected data."""
		data = {
			'elements': [
				{
					'type': 'way',
					'id': 1,
					'geometry': [
						{'x': 1000.0, 'y': 2000.0},
						{'x': 1100.0, 'y': 2100.0},
					],
					'tags': {'railway': 'rail'},
				}
			]
		}
		poly = Polygon(
			coordinates=[
				(47.37, 8.54),
				(47.39, 8.54),
				(47.39, 8.56),
				(47.37, 8.56),
			]
		)
		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'plot.png'
			plot_data(data, output, boundary=poly)
			assert output.exists()

	def test_plot_with_buffer_stop_nodes(self):
		"""Test plotting with buffer_stop nodes."""
		data = {
			'elements': [
				{
					'type': 'node',
					'id': 1,
					'lat': 47.38,
					'lon': 8.55,
					'tags': {'railway': 'buffer_stop'},
				}
			]
		}
		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'plot.png'
			plot_data(data, output)
			assert output.exists()
