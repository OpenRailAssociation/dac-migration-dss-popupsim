"""Convert OSM railway data to PopUpSim format."""

import html
import logging
import math
from datetime import datetime
from datetime import timezone
from typing import Any

import matplotlib.pyplot as plt
import yaml

logger = logging.getLogger(__name__)


def _calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
	"""Calculate Euclidean distance between two points."""
	return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _calculate_angle(x1: float, y1: float, x2: float, y2: float) -> float:
	"""Calculate angle in radians from point 1 to point 2."""
	return math.atan2(y2 - y1, x2 - x1)


def _angle_difference(angle1: float, angle2: float) -> float:
	"""Calculate smallest angle difference between two angles."""
	diff = abs(angle1 - angle2)
	if diff > math.pi:
		diff = 2 * math.pi - diff
	return diff


def _detect_switch_topology(
	node_id: int,
	node_data: dict[str, Any],
	edge_indices: list[int],
	edges_list: list[dict[str, Any]],
	is_projected: bool
) -> dict[str, Any]:
	"""Detect stem and branches for a switch using angle analysis."""
	if len(edge_indices) < 2:
		return {}

	node_x, node_y = node_data['x'], node_data['y']

	# Calculate angle for each connected edge
	edge_angles = []
	for edge_idx in edge_indices:
		edge = edges_list[edge_idx]
		if edge['start_id'] == node_id:
			other_x, other_y = edge['end']['x'], edge['end']['y']
		else:
			other_x, other_y = edge['start']['x'], edge['start']['y']
		angle = _calculate_angle(node_x, node_y, other_x, other_y)
		edge_angles.append((edge_idx, angle))

	if len(edge_angles) == 2:
		# 2 edges: both are part of the switch (no clear stem/branch distinction)
		return {
			'stem': f"edge_{edge_angles[0][0]}",
			'branches': [f"edge_{edge_angles[1][0]}"]
		}

	if len(edge_angles) == 3:
		# 3 edges: find straightest pair for main line
		min_straightness = float('inf')
		main_pair = (0, 1)
		for i in range(len(edge_angles)):
			for j in range(i + 1, len(edge_angles)):
				diff = _angle_difference(edge_angles[i][1], edge_angles[j][1])
				straightness = abs(diff - math.pi)
				if straightness < min_straightness:
					min_straightness = straightness
					main_pair = (i, j)
		branch_idx = [k for k in range(3) if k not in main_pair][0]
		return {
			'stem': f"edge_{edge_angles[main_pair[0]][0]}",
			'branches': [
				f"edge_{edge_angles[main_pair[1]][0]}",
				f"edge_{edge_angles[branch_idx][0]}"
			]
		}

	# Find all pairs close to 180° (straight through lines)
	straight_pairs = []
	for i in range(len(edge_angles)):
		for j in range(i + 1, len(edge_angles)):
			diff = _angle_difference(edge_angles[i][1], edge_angles[j][1])
			straightness = abs(diff - math.pi)
			if straightness < 0.3:  # ~17° tolerance for "straight"
				straight_pairs.append((i, j, straightness))

	# Sort by straightness
	straight_pairs.sort(key=lambda x: x[2])

	if len(edge_angles) == 4 and len(straight_pairs) >= 2:
		# Double slip or scissors: 2 main lines
		used = set()
		main_lines = []
		for i, j, _ in straight_pairs:
			if i not in used and j not in used:
				main_lines.append((i, j))
				used.add(i)
				used.add(j)
				if len(main_lines) == 2:
					break

		if len(main_lines) == 2:
			return {
				'stem': f"edge_{edge_angles[main_lines[0][0]][0]}",
				'branches': [
					f"edge_{edge_angles[main_lines[0][1]][0]}",
					f"edge_{edge_angles[main_lines[1][0]][0]}",
					f"edge_{edge_angles[main_lines[1][1]][0]}"
				]
			}

	# Simple switch: 1 main line
	if straight_pairs:
		i, j, _ = straight_pairs[0]
		stem_idx = edge_angles[i][0]
		branch_indices = [edge_angles[k][0] for k in range(len(edge_angles)) if k not in (i, j)]
		return {
			'stem': f"edge_{stem_idx}",
			'branches': [f"edge_{idx}" for idx in branch_indices]
		}

	# Fallback: no clear main line
	return {
		'stem': f"edge_{edge_angles[0][0]}",
		'branches': [f"edge_{edge_angles[i][0]}" for i in range(1, len(edge_angles))]
	}


def _build_graph(elements: list[dict[str, Any]]) -> dict[str, Any]:
	"""Build node-edge graph from OSM elements."""
	nodes_dict = {}
	edges_list = []
	node_to_edges: dict[int, list[int]] = {}

	# Collect all OSM nodes first
	for elem in elements:
		if elem['type'] == 'node':
			node_id = elem['id']
			nodes_dict[node_id] = elem
			node_to_edges[node_id] = []

	# Build edges from ways
	for elem in elements:
		if elem['type'] == 'way' and 'geometry' in elem:
			way_id = elem['id']
			geometry = elem['geometry']
			tags = elem.get('tags', {})

			# Match geometry points to OSM nodes by coordinates
			for i in range(len(geometry) - 1):
				start = geometry[i]
				end = geometry[i + 1]

				# Find matching OSM node IDs
				start_id = next((nid for nid, n in nodes_dict.items() 
					if abs(n['lat'] - start['lat']) < 1e-7 and abs(n['lon'] - start['lon']) < 1e-7), None)
				end_id = next((nid for nid, n in nodes_dict.items() 
					if abs(n['lat'] - end['lat']) < 1e-7 and abs(n['lon'] - end['lon']) < 1e-7), None)

				if start_id and end_id:
					edge_idx = len(edges_list)
					edges_list.append({
						'way_id': way_id,
						'start_id': start_id,
						'end_id': end_id,
						'start': start,
						'end': end,
						'tags': tags
					})
					node_to_edges[start_id].append(edge_idx)
					node_to_edges[end_id].append(edge_idx)

	return {'nodes': nodes_dict, 'edges': edges_list, 'node_to_edges': node_to_edges}


def extract_tracks_from_osm(osm_data: dict[str, Any], topology_ref: str) -> dict[str, Any]:
	"""Extract track definitions from OSM railway data.

	Parameters
	----------
	osm_data : dict[str, Any]
		OSM data with projected coordinates
	topology_ref : str
		Path to topology YAML file

	Returns
	-------
	dict[str, Any]
		Tracks format data
	"""
	elements = osm_data.get('elements', [])
	graph = _build_graph(elements)

	# Group edges by track reference
	track_groups: dict[str, list[int]] = {}
	for idx, edge_data in enumerate(graph['edges']):
		tags = edge_data['tags']
		track_ref = tags.get('railway:track_ref') or tags.get('ref')
		if track_ref:
			if track_ref not in track_groups:
				track_groups[track_ref] = []
			track_groups[track_ref].append(idx)

	# Create track definitions
	tracks = []
	for track_name, edge_indices in sorted(track_groups.items()):
		# Clean HTML entities from track name and ensure it's a string
		clean_name = str(html.unescape(str(track_name)))
		track_id = f"track_{clean_name.replace(' ', '_')}"
		edge_ids = [f"edge_{idx}" for idx in edge_indices]
		tracks.append({
			'id': track_id,
			'name': clean_name,
			'edges': edge_ids,
			'type': None
		})

	metadata = {
		'description': 'Extracted tracks',
		'version': '1.0.0',
		'topology_reference': topology_ref
	}

	return {'metadata': metadata, 'tracks': tracks}


def convert_osm_to_popupsim(
	osm_data: dict[str, Any],
	description: str = "Railway network",
	include_disused: bool = False,
	include_razed: bool = False
) -> dict[str, Any]:
	"""Convert OSM railway data to PopUpSim format.

	Parameters
	----------
	osm_data : dict[str, Any]
		OSM data with projected coordinates (x, y)
	description : str
		Network description
	include_disused : bool
		Include disused/abandoned tracks (default: False)
	include_razed : bool
		Include razed (demolished) tracks (default: False)

	Returns
	-------
	dict[str, Any]
		PopUpSim format data
	"""
	elements = osm_data.get('elements', [])

	# Build graph
	graph = _build_graph(elements)

	# Collect node IDs that are actually used in edges
	used_node_ids = set()
	for edge_data in graph['edges']:
		used_node_ids.add(edge_data['start_id'])
		used_node_ids.add(edge_data['end_id'])

	# Create nodes (only those connected to edges)
	nodes = {}
	orphaned_count = 0
	for node_id, node_data in graph['nodes'].items():
		# Skip orphaned nodes
		if node_id not in used_node_ids:
			orphaned_count += 1
			continue

		node_key = f"node_{node_id}"
		railway_type = node_data.get('tags', {}).get('railway', 'junction')

		node_entry: dict[str, Any] = {
			'type': railway_type,
			'coords': [node_data['x'], node_data['y']],
			'lat': node_data['lat'],
			'lon': node_data['lon']
		}

		# Add name from ref for switches and buffer stops
		tags = node_data.get('tags', {})
		if railway_type in ('switch', 'buffer_stop'):
			if 'ref' in tags:
				node_entry['name'] = html.unescape(tags['ref'])
			elif 'local_ref' in tags:
				node_entry['name'] = html.unescape(tags['local_ref'])
		if 'name' in tags and 'name' not in node_entry:
			node_entry['name'] = html.unescape(tags['name'])

		# Add switch config if switch
		if railway_type == 'switch':
			connected_edges = graph['node_to_edges'].get(node_id, [])
			if len(connected_edges) >= 2:
				switch_config = _detect_switch_topology(
					node_id, node_data, connected_edges, graph['edges'], True
				)
				if switch_config:
					# Add switch type from OSM tags
					switch_type = node_data.get('tags', {}).get('railway:switch', 'unknown')
					switch_config['switch_type'] = switch_type
					node_entry['switch_config'] = switch_config

		nodes[node_key] = node_entry

	if orphaned_count > 0:
		logger.info('Filtered out %d orphaned nodes', orphaned_count)

	# Create edges
	edges = {}
	for idx, edge_data in enumerate(graph['edges']):
		tags = edge_data['tags']
		is_disused = 'disused:railway' in tags or 'abandoned:railway' in tags
		is_razed = 'razed:railway' in tags

		# Skip based on filters
		if is_razed and not include_razed:
			continue
		if is_disused and not include_disused:
			continue

		edge_key = f"edge_{idx}"
		start = edge_data['start']
		end = edge_data['end']

		# Use length from input if available, otherwise compute
		if 'length' in edge_data:
			length = edge_data['length']
		else:
			length = _calculate_distance(start['x'], start['y'], end['x'], end['y'])

		railway_type = tags.get('railway', 'rail')
		if is_razed:
			status = 'razed'
		elif is_disused:
			status = 'disused'
		else:
			status = 'active'

		edges[edge_key] = {
			'nodes': [f"node_{edge_data['start_id']}", f"node_{edge_data['end_id']}"],
			'length': round(length, 2),
			'direction': 'bi-directional',
			'type': railway_type,
			'status': status
		}

	# Create metadata
	metadata = {
		'description': description,
		'version': '1.0.0',
		'level': 'microscopic',
		'projection': 'elliptical_mercator',
		'projection_method': 'WGS84 elliptical mercator (a=6378137.0m, b=6356752.3142m)',
		'crs': 'EPSG:4326',
		'projected_crs': 'Custom elliptical mercator',
		'units': {
			'length': 'meters',
			'coordinates': 'meters',
			'geographic': 'degrees'
		},
		'source': 'OpenStreetMap',
		'extracted_at': datetime.now(timezone.utc).isoformat()
	}

	return {'metadata': metadata, 'nodes': nodes, 'edges': edges}


def plot_popupsim_network(
	topology_file: str,
	tracks_file: str = None,
	output_file: str = None
) -> None:
	"""Plot PopUpSim railway network.
	
	Parameters
	----------
	topology_file : str
		Path to topology YAML file
	tracks_file : str, optional
		Path to tracks YAML file for track labels
	output_file : str, optional
		Output image file path
	"""
	# Load topology
	with open(topology_file, 'r') as f:
		topology = yaml.safe_load(f)
	
	# Load tracks if provided
	tracks = None
	if tracks_file:
		with open(tracks_file, 'r') as f:
			tracks = yaml.safe_load(f)
	
	fig, ax = plt.subplots(figsize=(12, 8))
	
	# Plot edges
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]
		
		x_coords = [node1['coords'][0], node2['coords'][0]]
		y_coords = [node1['coords'][1], node2['coords'][1]]
		
		ax.plot(x_coords, y_coords, 'b-', linewidth=1, alpha=0.7)
	
	# Plot track labels if tracks are provided
	if tracks:
		for track in tracks['tracks']:
			track_name = track['name']
			edge_ids = track['edges']
			
			if not edge_ids:
				continue
			
			# Find center edge for label placement
			center_idx = len(edge_ids) // 2
			center_edge_id = edge_ids[center_idx]
			
			if center_edge_id in topology['edges']:
				edge_data = topology['edges'][center_edge_id]
				nodes = edge_data['nodes']
				node1 = topology['nodes'][nodes[0]]
				node2 = topology['nodes'][nodes[1]]
				
				# Calculate midpoint of edge
				mid_x = (node1['coords'][0] + node2['coords'][0]) / 2
				mid_y = (node1['coords'][1] + node2['coords'][1]) / 2
				
				# Add track label
				ax.text(mid_x, mid_y, track_name, fontsize=8, 
					ha='center', va='center', 
					bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
	
	# Plot nodes
	for node_id, node_data in topology['nodes'].items():
		x, y = node_data['coords']
		node_type = node_data.get('type', 'junction')
		
		if node_type == 'switch':
			ax.plot(x, y, 'ro', markersize=4)
		elif node_type == 'buffer_stop':
			ax.plot(x, y, 'ks', markersize=4)
		else:
			ax.plot(x, y, 'ko', markersize=2)
	
	ax.set_aspect('equal')
	ax.grid(True, alpha=0.3)
	ax.set_title('Railway Network')
	ax.set_xlabel('X (meters)')
	ax.set_ylabel('Y (meters)')
	
	if output_file:
		plt.savefig(output_file, dpi=300, bbox_inches='tight')
	else:
		plt.show()
