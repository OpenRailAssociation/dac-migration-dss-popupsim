"""Clipper for filtering OSM data to boundaries."""

import json
import logging
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Union

from .exceptions import GeometryError
from .geometry import filter_osm_data
from .models import BoundingBox
from .models import Polygon

logger = logging.getLogger(__name__)


def clip_data(
	data: Dict[str, Any], boundary: Union[BoundingBox, Polygon]
) -> Dict[str, Any]:
	"""Clip OSM data to boundary.

	Parameters
	----------
	data : Dict[str, Any]
		OSM data with elements
	boundary : Union[BoundingBox, Polygon]
		Boundary for clipping

	Returns
	-------
	Dict[str, Any]
		Clipped OSM data
	"""
	logger.info('Clipping data to boundary')
	original_count = len(data.get('elements', []))
	clipped = filter_osm_data(data, boundary)
	filtered_count = len(clipped.get('elements', []))
	logger.info('Clipped %d -> %d elements', original_count, filtered_count)
	return clipped


def clip_from_file(
	input_file: Path, output_file: Path, boundary: Union[BoundingBox, Polygon]
) -> None:
	"""Clip OSM data from file.

	Parameters
	----------
	input_file : Path
		Input JSON file with OSM data
	output_file : Path
		Output JSON file for clipped data
	boundary : Union[BoundingBox, Polygon]
		Boundary for clipping
		
	Raises
	------
	GeometryError
		If clipping operation fails
	"""
	try:
		logger.info('Loading data from %s', input_file)
		with open(input_file, encoding='utf-8') as f:
			data = json.load(f)

		clipped = clip_data(data, boundary)

		logger.info('Saving clipped data to %s', output_file)
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(clipped, f, indent=2)
	except Exception as e:
		logger.error('Clipping failed: %s', e)
		raise GeometryError(f'Failed to clip data: {e}') from e
