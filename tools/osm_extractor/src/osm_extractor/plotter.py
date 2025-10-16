"""Plotter for visualizing railway data."""

import json
import logging
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from .exceptions import PlottingError
from .models import BoundingBox
from .projection import elliptical_mercator
from .visualize import NODE_MARKERS

logger = logging.getLogger(__name__)


def plot_data(
	data: Dict[str, Any],
	output_file: Path,
	title: str = 'Railway Network',
	show_nodes: bool = True,
	figsize: tuple = (12, 10),
	boundary: Optional[Any] = None,
) -> None:
	"""Plot railway data.

	Automatically detects if data is projected (has x/y) or geographic
	(has lat/lon).

	Parameters
	----------
	data : Dict[str, Any]
		OSM data with elements
	output_file : Path
		Output image file
	title : str, optional
		Plot title
	show_nodes : bool, optional
		Whether to show node markers
	figsize : tuple, optional
		Figure size
	boundary : Optional[Any], optional
		Boundary to overlay on plot
	"""
	logger.info('Creating plot: %s', title)
	fig, ax = plt.subplots(figsize=figsize)

	# Detect coordinate system
	sample = data.get('elements', [{}])[0]
	is_projected = 'x' in sample or (
		'geometry' in sample
		and sample['geometry']
		and 'x' in sample['geometry'][0]
	)

	# Plot ways
	way_count = 0
	for element in data.get('elements', []):
		if element['type'] == 'way' and 'geometry' in element:
			if is_projected:
				xs = [node['x'] for node in element['geometry']]
				ys = [node['y'] for node in element['geometry']]
			else:
				xs = [node['lon'] for node in element['geometry']]
				ys = [node['lat'] for node in element['geometry']]
			ax.plot(xs, ys, 'b-', linewidth=1.5, alpha=0.7)
			way_count += 1

	logger.debug('Plotted %d ways', way_count)

	# Plot nodes
	if show_nodes:
		node_groups: dict[str, list[tuple[float, float]]] = {
			'switch': [],
			'buffer_stop': [],
			'default': [],
		}

		for element in data.get('elements', []):
			if element['type'] == 'node':
				if is_projected:
					coord = (element['x'], element['y'])
				else:
					coord = (element['lon'], element['lat'])

				railway_type = element.get('tags', {}).get('railway')
				if railway_type in node_groups:
					node_groups[railway_type].append(coord)
				else:
					node_groups['default'].append(coord)

		for node_type, coords in node_groups.items():
			if coords:
				marker_cfg = NODE_MARKERS[node_type]
				xs, ys = zip(*coords)  # type: ignore
				ax.scatter(
					xs,
					ys,
					marker=marker_cfg['marker'],  # type: ignore
					c=marker_cfg['color'],  # type: ignore
					s=marker_cfg['size'],  # type: ignore
					label=f'{marker_cfg["label"]} ({len(coords)})',
					zorder=5,
				)

	# Plot boundary if provided
	if boundary:
		if isinstance(boundary, BoundingBox):
			if is_projected:
				x1, y1 = elliptical_mercator(boundary.south, boundary.west)
				x2, y2 = elliptical_mercator(boundary.north, boundary.east)
				rect = plt.Rectangle(
					(x1, y1), x2 - x1, y2 - y1, fill=False,
					edgecolor='red', linewidth=2, linestyle='--', label='Boundary'
				)
			else:
				rect = plt.Rectangle(
					(boundary.west, boundary.south),
					boundary.east - boundary.west,
					boundary.north - boundary.south,
					fill=False, edgecolor='red', linewidth=2,
					linestyle='--', label='Boundary'
				)
			ax.add_patch(rect)
		else:
			if is_projected:
				coords = [
					elliptical_mercator(lat, lon)
					for lat, lon in boundary.coordinates
				]
			else:
				coords = [(lon, lat) for lat, lon in boundary.coordinates]
			poly = MplPolygon(
				coords, fill=False, edgecolor='red', linewidth=2,
				linestyle='--', label='Boundary'
			)
			ax.add_patch(poly)

	if is_projected:
		ax.set_xlabel('X (meters)')
		ax.set_ylabel('Y (meters)')
	else:
		ax.set_xlabel('Longitude')
		ax.set_ylabel('Latitude')

	ax.set_title(title)
	ax.grid(True, alpha=0.3)
	if show_nodes or boundary:
		ax.legend()
	ax.set_aspect('equal')

	plt.tight_layout()
	logger.info('Saving plot to %s', output_file)
	fig.savefig(output_file, dpi=150, bbox_inches='tight')
	plt.close(fig)


def plot_from_file(
	input_file: Path,
	output_file: Path,
	title: Optional[str] = None,
	show_nodes: bool = True,
	boundary: Optional[Any] = None,
) -> None:
	"""Plot railway data from file.

	Parameters
	----------
	input_file : Path
		Input JSON file with OSM data
	output_file : Path
		Output image file
	title : Optional[str], optional
		Plot title, defaults to input filename
	show_nodes : bool, optional
		Whether to show node markers
	boundary : Optional[Any], optional
		Boundary to overlay on plot
	"""
	try:
		logger.info('Loading data from %s', input_file)
		with open(input_file, encoding='utf-8') as f:
			data = json.load(f)

		if title is None:
			title = input_file.stem

		plot_data(data, output_file, title=title, show_nodes=show_nodes, boundary=boundary)
	except Exception as e:
		logger.error('Plotting failed: %s', e)
		raise PlottingError(f'Failed to plot data: {e}') from e
