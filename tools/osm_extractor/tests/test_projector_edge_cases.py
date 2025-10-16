"""Edge case tests for projector."""

import json
import tempfile
from pathlib import Path

import pytest

from osm_extractor.exceptions import ProjectionError
from osm_extractor.projector import project_from_file


class TestProjectorEdgeCases:
	"""Edge case tests for projector."""

	def test_project_from_file_invalid_json(self):
		"""Test projection with invalid JSON file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'invalid.json'
			output_file = Path(tmpdir) / 'output.json'

			with open(input_file, 'w') as f:
				f.write('invalid json')

			with pytest.raises(ProjectionError):
				project_from_file(input_file, output_file)

	def test_project_from_file_missing_file(self):
		"""Test projection with missing input file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			input_file = Path(tmpdir) / 'missing.json'
			output_file = Path(tmpdir) / 'output.json'

			with pytest.raises(ProjectionError):
				project_from_file(input_file, output_file)
