"""Visualization utilities for railway data."""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from .models import BoundingBox
from .models import Polygon
from .projection import elliptical_mercator

logger = logging.getLogger(__name__)

NODE_MARKERS = {
	'switch': {'marker': 'X', 'color': 'red', 'size': 100, 'label': 'Switch'},
	'buffer_stop': {
		'marker': 's',
		'color': 'orange',
		'size': 80,
		'label': 'Buffer Stop',
	},
	'default': {'marker': 'o', 'color': 'gray', 'size': 20, 'label': 'Node'},
}


def plot_railway_data(
	data: Dict[str, Any],
	boundary: Optional[Union[BoundingBox, Polygon]] = None,
	title: str = 'Railway Network',
	show_nodes: bool = True,
	figsize: tuple = (12, 10),
	use_projection: bool = False,
) -> plt.Figure:
	"""Plot railway data with tracks and nodes.

	Parameters
	----------
	data : Dict[str, Any]
		OSM data with elements (ways and nodes)
	boundary : Optional[Union[BoundingBox, Polygon]], optional
		Boundary to overlay on plot
	title : str, optional
		Plot title, by default 'Railway Network'
	show_nodes : bool, optional
		Whether to show node markers, by default True
	figsize : tuple, optional
		Figure size (width, height), by default (12, 10)
	use_projection : bool, optional
		Whether to use Mercator projection for accurate distances,
		by default False

	Returns
	-------
	plt.Figure
		Matplotlib figure object
	"""
	logger.info('Creating railway visualization: %s', title)
	fig, ax = plt.subplots(figsize=figsize)

	# Plot ways (tracks)
	way_count = 0
	for element in data.get('elements', []):
		if element['type'] == 'way' and 'geometry' in element:
			if use_projection:
				coords = [
					elliptical_mercator(node['lat'], node['lon'])
					for node in element['geometry']
				]
				xs, ys = zip(*coords)
			else:
				xs = [node['lon'] for node in element['geometry']]
				ys = [node['lat'] for node in element['geometry']]
			ax.plot(xs, ys, 'b-', linewidth=1.5, alpha=0.7)
			way_count += 1

	logger.debug('Plotted %d railway ways', way_count)

	# Plot nodes with special markers
	if show_nodes:
		node_groups = {'switch': [], 'buffer_stop': [], 'default': []}

		for element in data.get('elements', []):
			if element['type'] == 'node':
				lon, lat = element['lon'], element['lat']
				railway_type = element.get('tags', {}).get('railway')

				if railway_type in node_groups:
					node_groups[railway_type].append((lon, lat))
				else:
					node_groups['default'].append((lon, lat))

		# Plot each node group
		for node_type, coords in node_groups.items():
			if coords:
				marker_cfg = NODE_MARKERS[node_type]
				if use_projection:
					proj_coords = [
						elliptical_mercator(lat, lon) for lon, lat in coords
					]
					xs, ys = zip(*proj_coords)
				else:
					xs, ys = zip(*coords)
				ax.scatter(
					xs,
					ys,
					marker=marker_cfg['marker'],
					c=marker_cfg['color'],
					s=marker_cfg['size'],
					label=f'{marker_cfg["label"]} ({len(coords)})',
					zorder=5,
				)
				logger.debug('Plotted %d %s nodes', len(coords), node_type)

	# Plot boundary
	if boundary:
		_plot_boundary(ax, boundary)

	if use_projection:
		ax.set_xlabel('X (meters)')
		ax.set_ylabel('Y (meters)')
	else:
		ax.set_xlabel('Longitude')
		ax.set_ylabel('Latitude')
	ax.set_title(title)
	ax.grid(True, alpha=0.3)
	if show_nodes:
		ax.legend()
	ax.set_aspect('equal')

	plt.tight_layout()
	return fig


def plot_comparison(
	data_before: Dict[str, Any],
	data_after: Dict[str, Any],
	boundary: Optional[Union[BoundingBox, Polygon]] = None,
	figsize: tuple = (16, 8),
) -> plt.Figure:
	"""Plot before/after comparison of railway data.

	Parameters
	----------
	data_before : Dict[str, Any]
		OSM data before filtering
	data_after : Dict[str, Any]
		OSM data after filtering
	boundary : Optional[Union[BoundingBox, Polygon]], optional
		Boundary to overlay on plot
	figsize : tuple, optional
		Figure size (width, height), by default (16, 8)

	Returns
	-------
	plt.Figure
		Matplotlib figure with two subplots
	"""
	logger.info('Creating before/after comparison visualization')
	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

	# Before filtering
	_plot_on_axis(
		ax1, data_before, boundary, 'Before Clipping', show_nodes=False
	)

	# After filtering
	_plot_on_axis(ax2, data_after, boundary, 'After Clipping', show_nodes=True)

	plt.tight_layout()
	return fig


def _plot_on_axis(
	ax: plt.Axes,
	data: Dict[str, Any],
	boundary: Optional[Union[BoundingBox, Polygon]],
	title: str,
	show_nodes: bool = True,
) -> None:
	"""Plot railway data on given axis."""
	# Plot ways
	for element in data.get('elements', []):
		if element['type'] == 'way' and 'geometry' in element:
			lons = [node['lon'] for node in element['geometry']]
			lats = [node['lat'] for node in element['geometry']]
			ax.plot(lons, lats, 'b-', linewidth=1.5, alpha=0.7)

	# Plot nodes
	if show_nodes:
		node_groups = {'switch': [], 'buffer_stop': [], 'default': []}

		for element in data.get('elements', []):
			if element['type'] == 'node':
				lon, lat = element['lon'], element['lat']
				railway_type = element.get('tags', {}).get('railway')

				if railway_type in node_groups:
					node_groups[railway_type].append((lon, lat))
				else:
					node_groups['default'].append((lon, lat))

		for node_type, coords in node_groups.items():
			if coords:
				marker_cfg = NODE_MARKERS[node_type]
				lons, lats = zip(*coords)
				ax.scatter(
					lons,
					lats,
					marker=marker_cfg['marker'],
					c=marker_cfg['color'],
					s=marker_cfg['size'],
					label=f'{marker_cfg["label"]} ({len(coords)})',
					zorder=5,
				)

	# Plot boundary
	if boundary:
		_plot_boundary(ax, boundary)

	ax.set_xlabel('Longitude')
	ax.set_ylabel('Latitude')
	ax.set_title(title)
	ax.grid(True, alpha=0.3)
	if show_nodes:
		ax.legend()
	ax.set_aspect('equal')


def _plot_boundary(
	ax: plt.Axes, boundary: Union[BoundingBox, Polygon]
) -> None:
	"""Plot boundary on axis."""
	if isinstance(boundary, BoundingBox):
		rect = plt.Rectangle(
			(boundary.west, boundary.south),
			boundary.east - boundary.west,
			boundary.north - boundary.south,
			fill=False,
			edgecolor='red',
			linewidth=2,
			linestyle='--',
			label='Boundary',
		)
		ax.add_patch(rect)
	else:
		coords = [(lon, lat) for lat, lon in boundary.coordinates]
		poly = MplPolygon(
			coords,
			fill=False,
			edgecolor='red',
			linewidth=2,
			linestyle='--',
			label='Boundary',
		)
		ax.add_patch(poly)
