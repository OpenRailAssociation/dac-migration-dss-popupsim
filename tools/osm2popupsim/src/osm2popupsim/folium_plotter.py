"""Folium plotter for PopUpSim topology and tracks."""

import logging
from pathlib import Path
from typing import Optional

import folium
import yaml

logger = logging.getLogger(__name__)

TRACK_COLORS = {
	'retrofit': 'magenta',
	'ressourceparking': '#8B4513',
	'parking': 'blue',
	'retrofitted': 'red',
	'circulating': 'yellow',
	'mainline': 'orange',
	'workshop': 'purple',
	'unused': 'lightgray',
}


def plot_popupsim_folium(
	topology_file: Path,
	tracks_file: Path,
	output_file: Path,
	title: str = 'Railway Network',
	throats_file: Optional[Path] = None,
) -> None:
	"""Plot PopUpSim railway network on interactive Folium map.

	Parameters
	----------
	topology_file : Path
		Path to topology YAML file
	tracks_file : Path
		Path to tracks YAML file
	output_file : Path
		Output HTML file path
	title : str
		Map title
	throats_file : Optional[Path]
		Path to throats YAML file (optional)
	"""
	logger.info('Loading topology from %s', topology_file)
	with open(topology_file, 'r') as f:
		topology = yaml.safe_load(f)

	logger.info('Loading tracks from %s', tracks_file)
	with open(tracks_file, 'r') as f:
		tracks_data = yaml.safe_load(f)

	# Build switch name to node ID mapping
	switch_name_to_node = {}
	for node_id, node_data in topology['nodes'].items():
		if node_data.get('type') == 'switch':
			switch_name = node_data.get('name')
			if switch_name:
				switch_name_to_node[switch_name] = node_id

	# Build track to edges mapping
	track_to_edges = {}
	for track in tracks_data['tracks']:
		track_to_edges[track['id']] = set(track.get('edges', []))

	# Load throats if provided
	throats_data = None
	throat_switches = set()
	throat_edges = set()
	if throats_file and throats_file.exists():
		logger.info('Loading throats from %s', throats_file)
		with open(throats_file, 'r') as f:
			throats_data = yaml.safe_load(f)
			for throat in throats_data.get('throats', []):
				throat_switch_names = throat.get('switches', [])
				throat_switches.update(throat_switch_names)
				
				# Get node IDs for throat switches
				throat_node_ids = set()
				for switch_name in throat_switch_names:
					if switch_name in switch_name_to_node:
						throat_node_ids.add(switch_name_to_node[switch_name])
				
				# Build graph excluding named track edges (except circulating)
				throat_graph = {}  # node -> set of connected nodes
				throat_graph_edges = {}  # (node1, node2) -> edge_id
				
				for edge_id, edge_data in topology['edges'].items():
					nodes = edge_data['nodes']
					
					# Check if edge belongs to a named track (entry/exit)
					is_excluded = False
					for track_id, track_edges in track_to_edges.items():
						if edge_id in track_edges:
							track_info = next((t for t in tracks_data['tracks'] if t['id'] == track_id), None)
							if track_info:
								track_type = track_info.get('type', '')
								track_name = track_info.get('name', '')
								# Exclude mainline and any named tracks except circulating (1a, 3a)
								if track_type == 'mainline' or (track_name and not track_name.endswith('a')):
									is_excluded = True
									break
					
					if not is_excluded:
						# Add edge to graph
						if nodes[0] not in throat_graph:
							throat_graph[nodes[0]] = set()
						if nodes[1] not in throat_graph:
							throat_graph[nodes[1]] = set()
						throat_graph[nodes[0]].add(nodes[1])
						throat_graph[nodes[1]].add(nodes[0])
						throat_graph_edges[(nodes[0], nodes[1])] = edge_id
						throat_graph_edges[(nodes[1], nodes[0])] = edge_id
				
				# Find connected component containing throat switches using BFS
				throat_component_nodes = set()
				visited = set()
				queue = list(throat_node_ids)
				
				while queue:
					node = queue.pop(0)
					if node in visited:
						continue
					visited.add(node)
					throat_component_nodes.add(node)
					
					if node in throat_graph:
						for neighbor in throat_graph[node]:
							if neighbor not in visited:
								queue.append(neighbor)
				
				# Collect all edges in the throat component
				for (n1, n2), edge_id in throat_graph_edges.items():
					if n1 in throat_component_nodes and n2 in throat_component_nodes:
						throat_edges.add(edge_id)

	# Build edge to track type mapping
	edge_to_track = {}
	for track in tracks_data['tracks']:
		track_type = track.get('type', 'unused')
		track_name = track.get('name', track['id'])
		for edge_id in track.get('edges', []):
			edge_to_track[edge_id] = {'type': track_type, 'name': track_name}

	# Calculate center from all nodes
	lats = [node['lat'] for node in topology['nodes'].values()]
	lons = [node['lon'] for node in topology['nodes'].values()]
	center_lat = sum(lats) / len(lats)
	center_lon = sum(lons) / len(lons)

	# Create map
	m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles='OpenStreetMap')

	# Add title
	title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
	m.get_root().html.add_child(folium.Element(title_html))

	# Plot edges by track type
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]

		coords = [[node1['lat'], node1['lon']], [node2['lat'], node2['lon']]]

		# Check if edge is part of a throat
		is_throat_edge = edge_id in throat_edges

		if is_throat_edge:
			color = 'cyan'
			weight = 5
			opacity = 0.9
			popup_text = f"THROAT EDGE<br>Edge: {edge_id}<br>Length: {edge_data.get('length', 'N/A')}m"
		else:
			track_info = edge_to_track.get(edge_id, {'type': 'unused', 'name': 'Unknown'})
			color = TRACK_COLORS.get(track_info['type'], 'gray')
			weight = 3
			opacity = 0.8
			popup_text = f"Track: {track_info['name']}<br>Type: {track_info['type']}<br>Length: {edge_data.get('length', 'N/A')}m"

		folium.PolyLine(
			coords,
			color=color,
			weight=weight,
			opacity=opacity,
			popup=folium.Popup(popup_text, max_width=200)
		).add_to(m)



	# Plot nodes
	for node_id, node_data in topology['nodes'].items():
		lat, lon = node_data['lat'], node_data['lon']
		node_type = node_data.get('type', 'junction')
		node_name = node_data.get('name', node_id)
		in_throat = node_name in throat_switches

		if node_type == 'switch':
			color = 'cyan' if in_throat else 'red'
			folium.CircleMarker(
				location=[lat, lon],
				radius=6 if in_throat else 5,
				color=color,
				fill=True,
				fillColor=color,
				fillOpacity=0.9 if in_throat else 0.8,
				popup=folium.Popup(f"Switch: {node_name}{'<br>(Throat)' if in_throat else ''}", max_width=150)
			).add_to(m)
			# Add switch label
			folium.Marker(
				location=[lat, lon],
				icon=folium.DivIcon(html=f'<div style="font-size: 10px; color: {color}; font-weight: bold; text-shadow: 1px 1px 1px white, -1px -1px 1px white, 1px -1px 1px white, -1px 1px 1px white;">{node_name}</div>')
			).add_to(m)
		elif node_type == 'buffer_stop':
			folium.CircleMarker(
				location=[lat, lon],
				radius=4,
				color='orange',
				fill=True,
				fillColor='orange',
				fillOpacity=0.8,
				popup=folium.Popup(f"Buffer Stop: {node_name}", max_width=150)
			).add_to(m)
			# Add buffer stop label
			folium.Marker(
				location=[lat, lon],
				icon=folium.DivIcon(html=f'<div style="font-size: 9px; color: orange; font-weight: bold; text-shadow: 1px 1px 1px white, -1px -1px 1px white, 1px -1px 1px white, -1px 1px 1px white;">{node_name}</div>')
			).add_to(m)

	# Add legend
	legend_html = '''
	<div style="position: fixed; bottom: 50px; left: 50px; width: 220px; height: auto; 
	background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px">
	<p><b>Track Types</b></p>
	'''
	legend_html += '<p><span style="color:cyan; font-weight:bold">━━━</span> Throat</p>'
	for track_type, color in TRACK_COLORS.items():
		legend_html += f'<p><span style="color:{color}">━━━</span> {track_type.capitalize()}</p>'
	legend_html += '</div>'
	m.get_root().html.add_child(folium.Element(legend_html))

	# Save map
	logger.info('Saving map to %s', output_file)
	m.save(str(output_file))
	logger.info('Map saved successfully')
