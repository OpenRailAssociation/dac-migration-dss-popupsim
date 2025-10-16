"""CLI error path tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from osm_extractor.cli import app


runner = CliRunner()


@pytest.mark.integration
class TestCLIErrorPaths:
	"""CLI error path tests."""

	def test_extract_invalid_bbox_coords(self):
		"""Test extract with invalid bbox coordinates."""
		result = runner.invoke(
			app, ['extract', '47.37,8.54,invalid', '-t', 'bbox']
		)
		assert result.exit_code == 1

	def test_extract_insufficient_bbox_coords(self):
		"""Test extract with insufficient bbox coordinates."""
		result = runner.invoke(app, ['extract', '47.37,8.54', '-t', 'bbox'])
		assert result.exit_code == 1

	def test_extract_insufficient_polygon_coords(self):
		"""Test extract with insufficient polygon coordinates."""
		result = runner.invoke(
			app, ['extract', '47.37,8.54 47.38,8.55', '-t', 'polygon']
		)
		assert result.exit_code == 1

	@patch('osm_extractor.cli.OSMRailwayExtractor')
	def test_extract_extraction_error(self, mock_extractor):
		"""Test extract with extraction error."""
		from osm_extractor.exceptions import ExtractionError

		mock_instance = mock_extractor.return_value
		mock_instance.extract.side_effect = ExtractionError('API error')

		result = runner.invoke(
			app, ['extract', '47.37,8.54,47.39,8.56', '-t', 'bbox']
		)
		assert result.exit_code == 1

	@patch('osm_extractor.cli.OSMRailwayExtractor')
	def test_extract_unexpected_error(self, mock_extractor):
		"""Test extract with unexpected error."""
		mock_instance = mock_extractor.return_value
		mock_instance.extract.side_effect = RuntimeError('Unexpected')

		result = runner.invoke(
			app, ['extract', '47.37,8.54,47.39,8.56', '-t', 'bbox']
		)
		assert result.exit_code == 1

	def test_clip_invalid_coords(self):
		"""Test clip with invalid coordinates."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'input.json'
			input_file.write_text('{"elements":[]}')

			result = runner.invoke(
				app,
				[
					'clip',
					str(input_file),
					'-c',
					'invalid',
					'-t',
					'bbox',
				],
			)
			assert result.exit_code == 1

	def test_clip_geometry_error(self):
		"""Test clip with geometry error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'missing.json'

			result = runner.invoke(
				app,
				[
					'clip',
					str(input_file),
					'-c',
					'47.37,8.54,47.39,8.56',
					'-t',
					'bbox',
				],
			)
			assert result.exit_code == 1

	def test_project_error(self):
		"""Test project with error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'missing.json'

			result = runner.invoke(app, ['project', str(input_file)])
			assert result.exit_code == 1

	def test_plot_missing_boundary_coords(self):
		"""Test plot with show-boundary but no coordinates."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'data.json'
			input_file.write_text('{"elements":[]}')

			result = runner.invoke(
				app, ['plot', str(input_file), '--show-boundary']
			)
			assert result.exit_code == 1

	def test_plot_error(self):
		"""Test plot with error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'missing.json'

			result = runner.invoke(app, ['plot', str(input_file)])
			assert result.exit_code == 1
