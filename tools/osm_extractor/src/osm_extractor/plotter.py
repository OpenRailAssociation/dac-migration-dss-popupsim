"""Plotter for visualizing railway data.

This module provides functions to plot railway network data extracted from
OpenStreetMap, with support for both geographic and projected coordinates.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from .exceptions import PlottingError
from .models import BoundingBox
from .projection import elliptical_mercator

logger = logging.getLogger(__name__)

NODE_MARKERS = {
	'switch': {'marker': 'X', 'color': 'red', 'size': 100, 'label': 'Switch'},
	'buffer_stop': {'marker': 's', 'color': 'orange', 'size': 80, 'label': 'Buffer Stop'},
	'default': {'marker': 'o', 'color': 'gray', 'size': 20, 'label': 'Node'},
}


def plot_data(
	data: Dict[str, Any],
	output_file: Optional[Path] = None,
	title: str = 'Railway Network',
	show_nodes: bool = True,
	show_switches: bool = True,
	show_labels: bool = False,
	label_switches: bool = False,
	show_disused: bool = True,
	figsize: tuple = (12, 10),
	boundary: Optional[Any] = None,
	show_plot: bool = False,
) -> None:
	"""Plot railway data.

	Automatically detects if data is projected (has x/y) or geographic
	(has lat/lon). Renders ways as blue lines, nodes as colored markers,
	and optionally displays track labels from railway:track_ref tags.

	Parameters
	----------
	data : Dict[str, Any]
		OSM data with elements list containing nodes and ways
	output_file : Optional[Path], optional
		Output image file path (PNG format), default None (no save)
	title : str, optional
		Plot title, default 'Railway Network'
	show_nodes : bool, optional
		Whether to show node markers, default True
	show_switches : bool, optional
		Whether to show switches, default True
	show_labels : bool, optional
		Whether to show track labels from railway:track_ref tags, default False
	label_switches : bool, optional
		Whether to show switch labels, default False
	show_disused : bool, optional
		Whether to show disused/abandoned tracks, default True
	figsize : tuple, optional
		Figure size in inches (width, height), default (12, 10)
	boundary : Optional[Union[BoundingBox, Polygon]], optional
		Boundary to overlay on plot, default None
	show_plot : bool, optional
		Whether to display interactive plot window, default False

	Returns
	-------
	None

	Notes
	-----
	Coordinate system is auto-detected:
	- Geographic: Uses lat/lon from elements
	- Projected: Uses x/y from elements

	Track labels are positioned at the average midpoint of all segments
	sharing the same railway:track_ref value.
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
	track_positions: dict[str, list[tuple[float, float]]] = {}
	for element in data.get('elements', []):
		if element['type'] == 'way' and 'geometry' in element:
			tags = element.get('tags', {})
			is_disused = (
				'disused:railway' in tags or 'abandoned:railway' in tags or
				tags.get('usage') in ['disused', 'abandoned'] or
				tags.get('railway') in ['disused', 'abandoned']
			)

			if is_disused and not show_disused:
				continue

			if is_projected:
				xs = [node['x'] for node in element['geometry']]
				ys = [node['y'] for node in element['geometry']]
			else:
				xs = [node['lon'] for node in element['geometry']]
				ys = [node['lat'] for node in element['geometry']]

			color = 'red' if is_disused else 'blue'
			ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.7)
			way_count += 1

			if show_labels:
				label = element.get('tags', {}).get('railway:track_ref')
				if label:
					mid_idx = len(xs) // 2
					if label not in track_positions:
						track_positions[label] = []
					track_positions[label].append((xs[mid_idx], ys[mid_idx]))

	logger.debug('Plotted %d ways', way_count)

	if show_labels:
		for label, positions in track_positions.items():
			avg_x = sum(p[0] for p in positions) / len(positions)
			avg_y = sum(p[1] for p in positions) / len(positions)
			ax.text(
				avg_x, avg_y, str(label), fontsize=8, ha='center',
				bbox={'boxstyle': 'round,pad=0.3', 'facecolor': 'white', 'alpha': 0.7}
			)

	# Plot nodes
	if show_nodes or show_switches:
		node_groups: dict[str, list[tuple[float, float]]] = {
			'switch': [],
			'buffer_stop': [],
			'default': [],
		}
		switch_labels: list[tuple[float, float, int]] = []

		for element in data.get('elements', []):
			if element['type'] == 'node':
				coord = (element['x'], element['y']) if is_projected else (element['lon'], element['lat'])

				railway_type = element.get('tags', {}).get('railway')
				if railway_type == 'switch':
					if show_switches:
						node_groups['switch'].append(coord)
						if label_switches:
							switch_id = element.get('id', 0)
							switch_labels.append((coord[0], coord[1], switch_id))
				elif railway_type in node_groups and show_nodes:
					node_groups[railway_type].append(coord)
				elif show_nodes:
					node_groups['default'].append(coord)

		for node_type, coords in node_groups.items():
			if coords:
				marker_cfg = NODE_MARKERS[node_type]
				xs, ys = zip(*coords, strict=False)  # type: ignore
				ax.scatter(
					xs,
					ys,
					marker=marker_cfg['marker'],  # type: ignore
					c=marker_cfg['color'],  # type: ignore
					s=marker_cfg['size'],  # type: ignore
					label=f'{marker_cfg["label"]} ({len(coords)})',
					zorder=5,
				)

		if label_switches:
			for x, y, switch_id in switch_labels:
				ax.text(
					x, y, str(switch_id), fontsize=6, ha='center',
					bbox={'boxstyle': 'round,pad=0.2', 'facecolor': 'yellow', 'alpha': 0.7}
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
	if output_file:
		logger.info('Saving plot to %s', output_file)
		fig.savefig(output_file, dpi=150, bbox_inches='tight')
	if show_plot:
		plt.show()
	else:
		plt.close(fig)


def plot_from_file(
	input_file: Path,
	output_file: Optional[Path] = None,
	title: Optional[str] = None,
	show_nodes: bool = True,
	show_switches: bool = True,
	show_labels: bool = False,
	label_switches: bool = False,
	show_disused: bool = True,
	boundary: Optional[Any] = None,
	show_plot: bool = False,
) -> None:
	"""Plot railway data from file.

	Loads OSM data from JSON file and generates a visualization plot.

	Parameters
	----------
	input_file : Path
		Input JSON file with OSM data
	output_file : Optional[Path], optional
		Output image file path (PNG format), default None (no save)
	title : Optional[str], optional
		Plot title, defaults to input filename stem
	show_nodes : bool, optional
		Whether to show node markers, default True
	show_switches : bool, optional
		Whether to show switches, default True
	show_labels : bool, optional
		Whether to show track labels, default False
	label_switches : bool, optional
		Whether to show switch labels, default False
	show_disused : bool, optional
		Whether to show disused tracks, default True
	boundary : Optional[Union[BoundingBox, Polygon]], optional
		Boundary to overlay on plot, default None
	show_plot : bool, optional
		Whether to display interactive plot window, default False

	Returns
	-------
	None

	Raises
	------
	PlottingError
		If plotting operation fails

	See Also
	--------
	plot_data : Core plotting function
	"""
	try:
		logger.info('Loading data from %s', input_file)
		with open(input_file, encoding='utf-8') as f:
			data = json.load(f)

		if title is None:
			title = input_file.stem

		plot_data(
			data, output_file, title=title, show_nodes=show_nodes,
			show_switches=show_switches, show_labels=show_labels,
			label_switches=label_switches, show_disused=show_disused,
			boundary=boundary, show_plot=show_plot
		)
	except Exception as e:
		logger.error('Plotting failed: %s', e)
		raise PlottingError(f'Failed to plot data: {e}') from e
