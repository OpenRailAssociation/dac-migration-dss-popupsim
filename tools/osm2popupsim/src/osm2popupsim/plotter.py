"""Plotter for PopUpSim topology and tracks."""

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import yaml

logger = logging.getLogger(__name__)

TRACK_COLORS = {
	'retrofit': 'magenta',
	'ressourceparking': '#8B4513',  # brownish
	'parking': 'blue',
	'retrofitted': 'red',
	'circulating': 'yellow',
	'mainline': 'orange',
	'workshop': 'purple',
	'unused': 'lightgray',
}


def plot_popupsim_network(
	topology_file: Path,
	tracks_file: Path,
	output_file: Optional[Path] = None,
	title: str = 'Railway Network',
	figsize: tuple = (14, 10),
	label_switches: bool = True,
) -> None:
	"""Plot PopUpSim railway network with track types.

	Parameters
	----------
	topology_file : Path
		Path to topology YAML file
	tracks_file : Path
		Path to tracks YAML file
	output_file : Optional[Path]
		Output image file path
	title : str
		Plot title
	figsize : tuple
		Figure size (width, height)
	label_switches : bool
		Whether to show switch labels
	"""
	logger.info('Loading topology from %s', topology_file)
	with open(topology_file, 'r') as f:
		topology = yaml.safe_load(f)

	logger.info('Loading tracks from %s', tracks_file)
	with open(tracks_file, 'r') as f:
		tracks_data = yaml.safe_load(f)

	# Build edge to track type mapping
	edge_to_type = {}
	for track in tracks_data['tracks']:
		track_type = track.get('type', 'unused')
		for edge_id in track.get('edges', []):
			edge_to_type[edge_id] = track_type

	fig, ax = plt.subplots(figsize=figsize)

	# Plot edges by track type
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]

		x_coords = [node1['coords'][0], node2['coords'][0]]
		y_coords = [node1['coords'][1], node2['coords'][1]]

		track_type = edge_to_type.get(edge_id, 'unused')
		color = TRACK_COLORS.get(track_type, 'gray')

		ax.plot(x_coords, y_coords, color=color, linewidth=2, alpha=0.8)

	# Plot nodes
	for node_id, node_data in topology['nodes'].items():
		x, y = node_data['coords']
		node_type = node_data.get('type', 'junction')

		if node_type == 'switch':
			ax.plot(x, y, 'ro', markersize=5, zorder=10)
			if label_switches:
				label = node_data.get('name', node_id.replace('node_', ''))
				ax.text(x, y, label, fontsize=6, ha='right', va='bottom',
					bbox={'boxstyle': 'round,pad=0.2', 'facecolor': 'yellow', 'alpha': 0.7})
		elif node_type == 'buffer_stop':
			ax.plot(x, y, 'ks', markersize=5, zorder=10)

	# Create legend
	legend_elements = [
		plt.Line2D([0], [0], color=color, linewidth=2, label=track_type.capitalize())
		for track_type, color in TRACK_COLORS.items()
		if any(t == track_type for t in edge_to_type.values())
	]
	ax.legend(handles=legend_elements, loc='best')

	ax.set_aspect('equal')
	ax.grid(True, alpha=0.3)
	ax.set_title(title)
	ax.set_xlabel('X (meters)')
	ax.set_ylabel('Y (meters)')

	plt.tight_layout()
	if output_file:
		logger.info('Saving plot to %s', output_file)
		fig.savefig(output_file, dpi=300, bbox_inches='tight')
		plt.close(fig)
	else:
		plt.show()
