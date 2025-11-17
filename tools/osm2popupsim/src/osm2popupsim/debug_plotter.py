"""Debug plotter for PopUpSim topology showing all edges and nodes with IDs."""

import logging
from pathlib import Path

import folium
import yaml

logger = logging.getLogger(__name__)


def plot_topology_debug(
	topology_file: Path,
	output_file: Path,
	title: str = 'Railway Network - Debug View',
) -> None:
	"""Plot PopUpSim topology with all edge and node IDs for debugging.

	Parameters
	----------
	topology_file : Path
		Path to topology YAML file
	output_file : Path
		Output HTML file path
	title : str
		Map title
	"""
	logger.info('Loading topology from %s', topology_file)
	with open(topology_file, 'r') as f:
		topology = yaml.safe_load(f)

	# Calculate center
	lats = [node['lat'] for node in topology['nodes'].values()]
	lons = [node['lon'] for node in topology['nodes'].values()]
	center_lat = sum(lats) / len(lats)
	center_lon = sum(lons) / len(lons)

	# Create map
	m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles='OpenStreetMap')

	# Add title
	title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
	m.get_root().html.add_child(folium.Element(title_html))

	# Plot edges with IDs
	for edge_id, edge_data in topology['edges'].items():
		nodes = edge_data['nodes']
		node1 = topology['nodes'][nodes[0]]
		node2 = topology['nodes'][nodes[1]]

		coords = [[node1['lat'], node1['lon']], [node2['lat'], node2['lon']]]
		
		# Calculate midpoint for label
		mid_lat = (node1['lat'] + node2['lat']) / 2
		mid_lon = (node1['lon'] + node2['lon']) / 2

		popup_text = f"<b>{edge_id}</b><br>Nodes: {nodes[0]}<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ {nodes[1]}<br>Length: {edge_data.get('length', 'N/A')}m"

		# Draw edge
		folium.PolyLine(
			coords,
			color='blue',
			weight=2,
			opacity=0.6,
			popup=folium.Popup(popup_text, max_width=250)
		).add_to(m)

		# Add edge ID label
		folium.Marker(
			location=[mid_lat, mid_lon],
			icon=folium.DivIcon(html=f'<div style="font-size: 8px; color: blue; background-color: white; padding: 1px 2px; border: 1px solid blue; border-radius: 2px;">{edge_id.replace("edge_", "")}</div>')
		).add_to(m)

	# Plot nodes with IDs
	for node_id, node_data in topology['nodes'].items():
		lat, lon = node_data['lat'], node_data['lon']
		node_type = node_data.get('type', 'junction')
		node_name = node_data.get('name', '')

		if node_type == 'switch':
			color = 'red'
			marker_size = 6
			label = node_name if node_name else node_id.replace('node_', '')
		elif node_type == 'buffer_stop':
			color = 'orange'
			marker_size = 5
			label = node_name if node_name else node_id.replace('node_', '')
		else:
			color = 'gray'
			marker_size = 3
			label = node_id.replace('node_', '')

		# Draw node
		folium.CircleMarker(
			location=[lat, lon],
			radius=marker_size,
			color=color,
			fill=True,
			fillColor=color,
			fillOpacity=0.8,
			popup=folium.Popup(f"<b>{node_id}</b><br>Type: {node_type}<br>Name: {node_name}", max_width=200)
		).add_to(m)

		# Add node label
		folium.Marker(
			location=[lat, lon],
			icon=folium.DivIcon(html=f'<div style="font-size: 9px; color: {color}; font-weight: bold; text-shadow: 1px 1px 1px white, -1px -1px 1px white, 1px -1px 1px white, -1px 1px 1px white;">{label}</div>')
		).add_to(m)

	# Add legend
	legend_html = '''
	<div style="position: fixed; bottom: 50px; left: 50px; width: 220px; height: auto; 
	background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px">
	<p><b>Debug View</b></p>
	<p><span style="color:red">●</span> Switches (with names)</p>
	<p><span style="color:orange">●</span> Buffer Stops</p>
	<p><span style="color:gray">●</span> Junctions (node IDs)</p>
	<p><span style="color:blue">━━━</span> Edges (edge IDs)</p>
	<p style="font-size:12px; margin-top:10px;">Click on edges/nodes for full IDs</p>
	</div>
	'''
	m.get_root().html.add_child(folium.Element(legend_html))

	# Save map
	logger.info('Saving debug map to %s', output_file)
	m.save(str(output_file))
	logger.info('Debug map saved successfully')
