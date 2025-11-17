"""Projector for converting OSM data to Cartesian coordinates."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from .exceptions import ProjectionError
from .projection import elliptical_mercator

logger = logging.getLogger(__name__)


def project_data(data: Dict[str, Any]) -> Dict[str, Any]:
	"""Project OSM data to Cartesian coordinates.

	Adds 'x' and 'y' fields to all nodes and geometry points using
	elliptical Mercator projection.

	Parameters
	----------
	data : Dict[str, Any]
		OSM data with lat/lon coordinates

	Returns
	-------
	Dict[str, Any]
		OSM data with added x/y projected coordinates
	"""
	logger.info('Projecting data to Cartesian coordinates')
	projected: Dict[str, Any] = {'elements': []}

	for element in data.get('elements', []):
		if element['type'] == 'node':
			x, y = elliptical_mercator(element['lat'], element['lon'])
			projected['elements'].append({**element, 'x': x, 'y': y})

		elif element['type'] == 'way':
			geometry = []
			for node in element.get('geometry', []):
				x, y = elliptical_mercator(node['lat'], node['lon'])
				geometry.append({**node, 'x': x, 'y': y})
			projected['elements'].append({**element, 'geometry': geometry})

	logger.info('Projected %d elements', len(projected['elements']))
	return projected


def project_from_file(input_file: Path, output_file: Path) -> None:
	"""Project OSM data from file.

	Parameters
	----------
	input_file : Path
		Input JSON file with OSM data
	output_file : Path
		Output JSON file with projected data
		
	Raises
	------
	ProjectionError
		If projection operation fails
	"""
	try:
		logger.info('Loading data from %s', input_file)
		with open(input_file, encoding='utf-8') as f:
			data = json.load(f)

		projected = project_data(data)

		logger.info('Saving projected data to %s', output_file)
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(projected, f, indent=2)
	except Exception as e:
		logger.error('Projection failed: %s', e)
		raise ProjectionError(f'Failed to project data: {e}') from e
