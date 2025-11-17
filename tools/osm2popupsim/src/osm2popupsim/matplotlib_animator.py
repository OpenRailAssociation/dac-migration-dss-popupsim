"""Matplotlib animator for PopUpSim train movements."""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import yaml

from .route_animator import compute_train_positions, build_graph

logger = logging.getLogger(__name__)


def create_matplotlib_animation(
	sequence_file: Path,
	topology_file: Path,
	tracks_file: Path,
	routes_file: Path,
	output_file: Path,
	timestep: float = 1.0,
	fps: int = 10
) -> None:
	"""Create matplotlib animation of train movements."""
	logger.info('Computing train positions...')
	train_positions = compute_train_positions(
		sequence_file,
		topology_file,
		tracks_file,
		routes_file,
		timestep
	)
	
	with open(topology_file, 'r', encoding='utf-8') as f:
		topology = yaml.safe_load(f)
	
	# Setup figure
	fig, ax = plt.subplots(figsize=(12, 10))
	
	# Draw railway network
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]
		ax.plot([node1['lon'], node2['lon']], [node1['lat'], node2['lat']], 
		        'gray', linewidth=1, alpha=0.5, zorder=1)
	
	# Prepare train data
	all_times = set()
	for positions in train_positions.values():
		for t, _, _ in positions:
			all_times.add(t)
	
	times = sorted(all_times)
	time_to_positions = {}
	
	for t in times:
		time_to_positions[t] = {}
		for train_id, positions in train_positions.items():
			for pos_t, lat, lon in positions:
				if pos_t == t:
					time_to_positions[t][train_id] = (lon, lat)
					break
	
	# Initialize train markers
	train_markers = {}
	for train_id in train_positions.keys():
		marker, = ax.plot([], [], 'ro', markersize=8, zorder=3, label=train_id)
		train_markers[train_id] = marker
	
	time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, 
	                    verticalalignment='top', fontsize=12,
	                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
	
	ax.set_xlabel('Longitude')
	ax.set_ylabel('Latitude')
	ax.set_title('Train Movement Animation')
	ax.legend(loc='upper right')
	ax.grid(True, alpha=0.3)
	ax.set_aspect('equal')
	
	def init():
		for marker in train_markers.values():
			marker.set_data([], [])
		time_text.set_text('')
		return list(train_markers.values()) + [time_text]
	
	def update(frame):
		t = times[frame]
		positions = time_to_positions[t]
		
		for train_id, marker in train_markers.items():
			if train_id in positions:
				lon, lat = positions[train_id]
				marker.set_data([lon], [lat])
			else:
				marker.set_data([], [])
		
		time_text.set_text(f'Time: {t:.1f}s')
		return list(train_markers.values()) + [time_text]
	
	anim = animation.FuncAnimation(fig, update, init_func=init,
	                               frames=len(times), interval=1000/fps,
	                               blit=True, repeat=True)
	
	logger.info(f'Saving animation to {output_file}...')
	anim.save(str(output_file), writer='pillow', fps=fps)
	logger.info('Animation complete!')
	plt.close()
