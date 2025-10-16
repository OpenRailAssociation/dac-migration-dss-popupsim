"""Integration tests for CLI module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from osm_extractor.cli import app


runner = CliRunner()


@pytest.mark.integration
class TestCLIIntegration:
	"""Integration tests for CLI."""

	@patch('osm_extractor.cli.OSMRailwayExtractor')
	def test_extract_bbox_command(self, mock_extractor, sample_osm_data):
		"""Test extract command with bbox."""
		mock_instance = mock_extractor.return_value
		mock_instance.extract.return_value = sample_osm_data

		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'output.json'
			result = runner.invoke(
				app,
				[
					'extract',
					'47.37,8.54,47.39,8.56',
					'-t',
					'bbox',
					'-o',
					str(output),
				],
			)
			assert result.exit_code == 0
			assert output.exists()

	@patch('osm_extractor.cli.OSMRailwayExtractor')
	def test_extract_polygon_command(self, mock_extractor, sample_osm_data):
		"""Test extract command with polygon."""
		mock_instance = mock_extractor.return_value
		mock_instance.extract.return_value = sample_osm_data

		with tempfile.TemporaryDirectory() as tmpdir:
			output = Path(tmpdir) / 'output.json'
			result = runner.invoke(
				app,
				[
					'extract',
					'47.37,8.54 47.39,8.54 47.39,8.56',
					'-t',
					'polygon',
					'-o',
					str(output),
				],
			)
			assert result.exit_code == 0
			assert output.exists()

	def test_clip_command(self, sample_osm_data):
		"""Test clip command."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'input.json'
			output_file = Path(tmpdir) / 'output.json'

			with open(input_file, 'w') as f:
				json.dump(sample_osm_data, f)

			result = runner.invoke(
				app,
				[
					'clip',
					str(input_file),
					'-c',
					'47.37,8.54,47.39,8.56',
					'-t',
					'bbox',
					'-o',
					str(output_file),
				],
			)
			assert result.exit_code == 0
			assert output_file.exists()

	def test_project_command(self, sample_osm_data):
		"""Test project command."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'input.json'
			output_file = Path(tmpdir) / 'output.json'

			with open(input_file, 'w') as f:
				json.dump(sample_osm_data, f)

			result = runner.invoke(
				app, ['project', str(input_file), '-o', str(output_file)]
			)
			assert result.exit_code == 0
			assert output_file.exists()

	def test_plot_command(self, sample_osm_data):
		"""Test plot command."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'input.json'
			output_file = Path(tmpdir) / 'plot.png'

			with open(input_file, 'w') as f:
				json.dump(sample_osm_data, f)

			result = runner.invoke(
				app, ['plot', str(input_file), '-o', str(output_file)]
			)
			assert result.exit_code == 0
			assert output_file.exists()

	def test_info_command(self):
		"""Test info command."""
		result = runner.invoke(app, ['info'])
		assert result.exit_code == 0
		assert 'Available Railway Types:' in result.stdout
		assert 'Available Node Types:' in result.stdout
