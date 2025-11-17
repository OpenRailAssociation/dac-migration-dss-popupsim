"""Route animator for PopUpSim train movements."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import folium
from folium import plugins
import networkx as nx
import yaml

logger = logging.getLogger(__name__)


def build_graph(topology: Dict) -> nx.Graph:
	"""Build NetworkX graph from topology."""
	G = nx.Graph()
	
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		length = edge_data.get('length', 10.0)
		G.add_edge(nodes[0], nodes[1], edge_id=edge_id, length=length)
	
	return G


def find_path_between_nodes(
	start_node: str,
	end_node: str,
	G: nx.Graph
) -> List[str]:
	"""Find shortest path between two nodes, return edge IDs."""
	try:
		node_path = nx.shortest_path(G, start_node, end_node)
		edge_ids = []
		for i in range(len(node_path) - 1):
			edge_data = G[node_path[i]][node_path[i + 1]]
			edge_ids.append(edge_data['edge_id'])
		return edge_ids
	except nx.NetworkXNoPath:
		return []


def compute_route_edges(
	route_id: str,
	routes_data: Dict,
	tracks_data: Dict,
	topology: Dict,
	G: nx.Graph,
	start_pos: tuple = None
) -> List[Tuple[str, float, float, float, float, float]]:
	"""Compute edge sequence for a route using NetworkX graph."""
	route = next((r for r in routes_data['routes'] if r['id'] == route_id), None)
	if not route:
		logger.warning(f'Route {route_id} not found')
		return []
	
	# Build edge-to-track mapping
	edge_to_track = {}
	for track in tracks_data['tracks']:
		for edge_id in track['edges']:
			edge_to_track[edge_id] = track['id']
	
	edges_list = []
	current_node = None
	all_edges = []
	used_edges = set()
	
	logger.info(f'\n=== Route {route_id} ===')
	logger.info(f'Path: {" -> ".join(route["path"])}')
	
	for i, track_id in enumerate(route['path']):
		track = next((t for t in tracks_data['tracks'] if t['id'] == track_id), None)
		if not track:
			continue
		
		# Get track endpoints
		first_edge = topology['edges'][track['edges'][0]]
		last_edge = topology['edges'][track['edges'][-1]]
		track_start = first_edge['nodes'][0]
		track_end = last_edge['nodes'][1]
		reverse_track = False
		
		if i == 0:
			# Check if we need to reverse the first track based on start position
			if start_pos:
				# Check which end of the track is closer to start_pos
				start_node_data = topology['nodes'][track_start]
				end_node_data = topology['nodes'][track_end]
				dist_to_start = ((start_node_data['lat'] - start_pos[0])**2 + (start_node_data['lon'] - start_pos[1])**2)**0.5
				dist_to_end = ((end_node_data['lat'] - start_pos[0])**2 + (end_node_data['lon'] - start_pos[1])**2)**0.5
				
				if dist_to_end < dist_to_start:
					# Start from end, so reverse the track
					track_start, track_end = track_end, track_start
					reverse_track = True
					logger.info(f'  Reversing first track {track_id} to start from current position')
			
			current_node = track_start
		else:
			# Connect to track using NetworkX only if not already there
			if current_node != track_start:
				try:
					connecting_path = nx.shortest_path(G, current_node, track_start)
					connecting_edges = []
					for j in range(len(connecting_path) - 1):
						edge_data = G[connecting_path[j]][connecting_path[j + 1]]
						edge_id = edge_data['edge_id']
						connecting_edges.append(edge_id)
						used_edges.add(edge_id)
						edge = topology['edges'][edge_id]
						nodes = edge['nodes']
						node1 = topology['nodes'][nodes[0]]
						node2 = topology['nodes'][nodes[1]]
						edge_length = edge.get('length', 10.0)
						if connecting_path[j] == nodes[0]:
							edges_list.append((edge_id, node1['lat'], node1['lon'], node2['lat'], node2['lon'], edge_length))
						else:
							edges_list.append((edge_id, node2['lat'], node2['lon'], node1['lat'], node1['lon'], edge_length))
					if connecting_edges:
						logger.info(f'  Connecting edges: {connecting_edges}')
						all_edges.extend(connecting_edges)
					current_node = track_start
				except nx.NetworkXNoPath:
					logger.warning(f'No path from {current_node} to {track_start}')
					continue
		
		# Add track's own edges (skip if already used in connection)
		track_edges = []
		skipped_edges = []
		edge_list = list(reversed(track['edges'])) if reverse_track else track['edges']
		for edge_id in edge_list:
			if edge_id in used_edges:
				skipped_edges.append(edge_id)
				continue
			track_edges.append(edge_id)
			used_edges.add(edge_id)
			edge = topology['edges'][edge_id]
			nodes = edge['nodes']
			node1 = topology['nodes'][nodes[0]]
			node2 = topology['nodes'][nodes[1]]
			edge_length = edge.get('length', 10.0)
			if current_node == nodes[0]:
				edges_list.append((edge_id, node1['lat'], node1['lon'], node2['lat'], node2['lon'], edge_length))
				current_node = nodes[1]
			else:
				edges_list.append((edge_id, node2['lat'], node2['lon'], node1['lat'], node1['lon'], edge_length))
				current_node = nodes[0]
		
		# If all edges were skipped, update current_node to track end
		if skipped_edges and not track_edges:
			current_node = track_end
			logger.info(f'  Track {track_id}: {track_edges} (skipped: {skipped_edges}, moved to end)')
		elif skipped_edges:
			logger.info(f'  Track {track_id}: {track_edges} (skipped: {skipped_edges})')
		else:
			logger.info(f'  Track {track_id}: {track_edges}')
		all_edges.extend(track_edges)
	
	logger.info(f'All edges: {all_edges}')
	logger.info(f'Tracks visited: {[edge_to_track.get(e, "connector") for e in all_edges]}')
	logger.info(f'Total: {len(all_edges)} edges\n')
	
	return edges_list


def compute_train_positions(
	sequence_file: Path,
	topology_file: Path,
	tracks_file: Path,
	routes_file: Path,
	timestep: float = 1.0
) -> Dict[str, List[Tuple[float, float, float]]]:
	"""Compute train positions at each timestep."""
	import logging
	logging.basicConfig(level=logging.INFO, format='%(message)s')
	logger.info('Loading files...')
	with open(sequence_file, 'r', encoding='utf-8') as f:
		sequence_data = yaml.safe_load(f)
	with open(topology_file, 'r', encoding='utf-8') as f:
		topology = yaml.safe_load(f)
	with open(tracks_file, 'r', encoding='utf-8') as f:
		tracks_data = yaml.safe_load(f)
	with open(routes_file, 'r', encoding='utf-8') as f:
		routes_data = yaml.safe_load(f)
	
	G = build_graph(topology)
	train_positions = {}
	current_time = 0.0
	train_states = {}
	train_step_count = {}
	
	for step in sequence_data['sequence']:
		train_id = step.get('train_id')
		duration = step.get('duration', 0)
		
		if train_id not in train_positions:
			train_positions[train_id] = []
			train_step_count[train_id] = 0
		
		if step['type'] == 'route':
			# Get current position if train has moved before
			current_pos = train_states.get(train_id)
			if current_pos:
				logger.info(f'Train {train_id} starting route {step["route_id"]} from position ({current_pos[0]:.6f}, {current_pos[1]:.6f})')
			
			edges_list = compute_route_edges(
				step['route_id'],
				routes_data,
				tracks_data,
				topology,
				G,
				current_pos
			)
			
			if edges_list:
				logger.info(f'Route starts at ({edges_list[0][1]:.6f}, {edges_list[0][2]:.6f})')
				logger.info(f'Route ends at ({edges_list[-1][3]:.6f}, {edges_list[-1][4]:.6f})')
				
				total_length = sum(edge[5] for edge in edges_list)
				num_steps = int(duration / timestep)
				
				for i in range(1, num_steps + 1):
					t = current_time + i * timestep
					progress = i / num_steps if num_steps > 0 else 1.0
					target_distance = progress * total_length
					
					cumulative = 0.0
					position_found = False
					for edge_id, lat1, lon1, lat2, lon2, length in edges_list:
						if cumulative <= target_distance <= cumulative + length:
							edge_progress = (target_distance - cumulative) / length if length > 0 else 0
							lat = lat1 + (lat2 - lat1) * edge_progress
							lon = lon1 + (lon2 - lon1) * edge_progress
							train_positions[train_id].append((t, lat, lon))
							position_found = True
							break
						cumulative += length
					
					if not position_found:
						lat, lon = edges_list[-1][3:5]
						train_positions[train_id].append((t, lat, lon))
				
				train_states[train_id] = (edges_list[-1][3], edges_list[-1][4])
				logger.info(f'Train {train_id} ended at ({edges_list[-1][3]:.6f}, {edges_list[-1][4]:.6f})\n')
				train_step_count[train_id] += 1
		
		elif step['type'] == 'wait':
			if train_id in train_states:
				lat, lon = train_states[train_id]
			else:
				first_node = next(iter(topology['nodes'].values()))
				lat, lon = first_node['lat'], first_node['lon']
				train_states[train_id] = (lat, lon)
			
			num_steps = int(duration / timestep)
			for i in range(1, num_steps + 1):
				t = current_time + i * timestep
				train_positions[train_id].append((t, lat, lon))
		
		current_time += duration
	
	return train_positions


def create_animated_map(
	sequence_file: Path,
	topology_file: Path,
	tracks_file: Path,
	routes_file: Path,
	output_file: Path,
	timestep: float = 1.0
) -> None:
	"""Create animated Folium map with train movements."""
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
	
	lats = [node['lat'] for node in topology['nodes'].values()]
	lons = [node['lon'] for node in topology['nodes'].values()]
	center_lat = sum(lats) / len(lats)
	center_lon = sum(lons) / len(lons)
	
	m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
	
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]
		coords = [[node1['lat'], node1['lon']], [node2['lat'], node2['lon']]]
		folium.PolyLine(coords, color='gray', weight=2, opacity=0.5).add_to(m)
	
	base_time = datetime(2024, 1, 1, 0, 0, 0)
	features = []
	seen = set()
	
	for train_id, positions in train_positions.items():
		for t, lat, lon in positions:
			timestamp = base_time + timedelta(seconds=t)
			key = (timestamp.isoformat(), train_id)
			if key not in seen:
				seen.add(key)
				features.append({
					'type': 'Feature',
					'geometry': {
						'type': 'Point',
						'coordinates': [lon, lat]
					},
					'properties': {
						'time': timestamp.isoformat(),
						'popup': train_id,
						'icon': 'circle',
						'iconstyle': {
							'fillColor': 'red',
							'fillOpacity': 0.9,
							'stroke': 'true',
							'color': 'darkred',
							'weight': 2,
							'radius': 6
						}
					}
				})
	
	logger.info(f'Created {len(features)} animation frames')
	
	plugins.TimestampedGeoJson(
		{'type': 'FeatureCollection', 'features': features},
		period=f'PT{int(timestep)}S',
		add_last_point=False,
		auto_play=True,
		loop=False,
		max_speed=5,
		loop_button=True,
		date_options='HH:mm:ss',
		time_slider_drag_update=True
	).add_to(m)
	
	logger.info(f'Saving map to {output_file}...')
	m.save(str(output_file))
	logger.info('Animation complete!')
