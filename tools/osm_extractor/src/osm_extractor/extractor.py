"""OSM railway data extractor."""

import logging
from typing import Any, Dict, Union

import overpy

from .exceptions import InvalidQueryError, QueryTimeoutError, RateLimitError
from .geometry import filter_osm_data
from .models import BoundingBox, Polygon

logger = logging.getLogger(__name__)


class OSMRailwayExtractor:
	"""Extract railway data from OSM with boundary-crossing track support.

	This extractor fetches railway infrastructure data from OSM using the
	Overpass API, including tracks that cross specified boundaries.
	It supports both polygon and bounding box queries with configurable buffer
	zones.

	Parameters
	----------
	overpass_url : str, optional
	    Overpass API endpoint URL, by default
	    "https://overpass-api.de/api/interpreter"
	timeout : int, optional
	    Request timeout in seconds, by default 60
	railway_types : list[str]
	    List containing the type of railway elements to be extracted.
	    Defaults to ['rail', 'siding', 'yard', 'spur']
	node_types : list[str], optional
	    List containing the type of railway nodes to be extracted.
	    Defaults to ['switch', 'buffer_stop']
	"""

	def __init__(
		self,
		overpass_url: str = 'https://overpass-api.de/api/interpreter',
		timeout: int = 60,
		railway_types: list | None = None,
		node_types: list | None = None,
		include_disused: bool = False,
		include_razed: bool = False,
	) -> None:
		self.api = overpy.Overpass(url=overpass_url)
		self.timeout = timeout
		self.railway_types = railway_types or ['rail', 'siding', 'yard', 'spur']
		self.node_types = node_types or ['switch', 'buffer_stop']
		self.include_disused = include_disused
		self.include_razed = include_razed
		logger.info(
			'Initialized OSMRailwayExtractor with URL=%s, timeout=%ds',
			overpass_url,
			timeout,
		)

	def _build_overpass_query(
		self, boundary: Union[BoundingBox, Polygon]
	) -> str:
		"""Build Overpass QL query for railway data extraction.

		Constructs an Overpass QL query to extract railway ways and nodes
		within the specified boundary. Uses recursive down relation to
		include all intermediate nodes for complete track geometry.

		Parameters
		----------
		boundary : Union[BoundingBox, Polygon]
		    Geographic boundary for data extraction

		Returns
		-------
		str
		    Overpass QL query string with filters for railway types and nodes
		"""
		if isinstance(boundary, BoundingBox):
			bbox_str = (
				f'{boundary.south},{boundary.west},'
				f'{boundary.north},{boundary.east}'
			)
			area_filter = f'({bbox_str})'
		else:
			coords_str = ' '.join(
				[f'{lat} {lon}' for lat, lon in boundary.coordinates]
			)
			area_filter = f'(poly:"{coords_str}")'

		railway_regex = '|'.join(self.railway_types)
		node_regex = '|'.join(self.node_types)

		query_parts = [f'way["railway"~"^({railway_regex})$"]{area_filter};']
		if self.include_disused:
			query_parts.extend([
				f'way["disused:railway"~"^({railway_regex})$"]{area_filter};',
				f'way["abandoned:railway"~"^({railway_regex})$"]{area_filter};'
			])
		if self.include_razed:
			query_parts.append(f'way["railway"="razed"]{area_filter};')
		query_parts.append(f'node["railway"~"^({node_regex})$"]{area_filter};')
		
		query = f"""
        [out:json][timeout:{self.timeout}];
        (
          {chr(10).join('          ' + p for p in query_parts)}
        );
        (._;>;);
        out geom;
        """
		logger.debug('Built Overpass query: %s', query.strip())
		return query

	def extract(
		self,
		boundary: Union[BoundingBox, Polygon],
		filter_geometry: bool = True,
		hierarchical: bool = False,
	) -> Dict[str, Any]:
		"""Extract railway data within specified boundary.

		Queries the Overpass API for railway infrastructure data within
		the specified boundary area, including all intermediate nodes.
		Optionally filters geometry to remove segments outside boundary.

		Parameters
		----------
		boundary : Union[BoundingBox, Polygon]
		    Geographic boundary defining extraction area
		filter_geometry : bool, optional
		    Whether to filter out geometry outside boundary. Defaults to
		    True
		hierarchical : bool, optional
		    Whether to return hierarchical format (nodes, edges, ways).
		    Defaults to False

		Returns
		-------
		Dict[str, Any]
		    JSON response from Overpass API containing railway ways, nodes
		    and geometry

		Raises
		------
		overpy.exception.OverpassTooManyRequests
		    If rate limit is exceeded
		overpy.exception.OverpassGatewayTimeout
		    If the query takes too long to execute
		overpy.exception.OverpassBadRequest
		    If the query syntax is invalid
		"""
		boundary_type = type(boundary).__name__
		logger.info('Starting extraction for %s boundary', boundary_type)

		query = self._build_overpass_query(boundary)

		try:
			logger.debug('Querying Overpass API...')
			result = self.api.query(query)
			logger.info(
				'Received %d nodes and %d ways from Overpass API',
				len(result.nodes),
				len(result.ways),
			)
			data = self._convert_to_hierarchical_json(result) if hierarchical else self._convert_to_json(result)
		except overpy.exception.OverpassTooManyRequests as e:
			logger.error('Rate limit exceeded')
			raise RateLimitError(
				'Rate limit exceeded. Please wait and try again.'
			) from e
		except overpy.exception.OverpassGatewayTimeout as e:
			logger.error('Query timeout exceeded')
			raise QueryTimeoutError(
				'Query timeout. Try reducing the area or filters.'
			) from e
		except overpy.exception.OverpassBadRequest as e:
			logger.error('Invalid query: %s', e)
			raise InvalidQueryError(f'Invalid query: {e}') from e

		# Filter inactive tracks
		if not self.include_disused or not self.include_razed:
			data = self._filter_inactive_tracks(data)
		
		if filter_geometry:
			logger.debug('Filtering geometry to boundary')
			original_count = len(data['elements'])
			data = filter_osm_data(data, boundary)
			filtered_count = len(data['elements'])
			logger.info(
				'Filtered %d -> %d elements',
				original_count,
				filtered_count,
			)

		# Always remove orphaned nodes at the end
		data = self._remove_orphaned_nodes(data)

		return data

	def _convert_to_json(self, result: overpy.Result) -> Dict[str, Any]:
		"""Convert overpy Result to JSON format.

		Parameters
		----------
		result : overpy.Result
		    Overpy query result

		Returns
		-------
		Dict[str, Any]
		    JSON formatted data compatible with filter_osm_data
		"""
		logger.debug('Converting overpy Result to JSON format')
		elements = []

		for node in result.nodes:
			elements.append(
				{
					'type': 'node',
					'id': node.id,
					'lat': float(node.lat),
					'lon': float(node.lon),
					'tags': node.tags,
				}
			)

		for way in result.ways:
			geometry = [
				{'lat': float(node.lat), 'lon': float(node.lon)}
				for node in way.nodes
			]
			elements.append(
				{
					'type': 'way',
					'id': way.id,
					'geometry': geometry,
					'tags': way.tags,
				}
			)

		return {'elements': elements}

	def _convert_to_hierarchical_json(
		self, result: overpy.Result
	) -> Dict[str, Any]:
		"""Convert overpy Result to hierarchical JSON format.

		Creates a hierarchical structure: nodes, edges (segments), and ways.
		Each edge inherits the track label from its parent way.

		Parameters
		----------
		result : overpy.Result
			Overpy query result

		Returns
		-------
		Dict[str, Any]
			Hierarchical JSON with nodes, edges, and ways
		"""
		logger.debug('Converting to hierarchical JSON format')
		nodes = []
		edges = []
		ways = []

		for node in result.nodes:
			nodes.append(
				{
					'type': 'node',
					'id': node.id,
					'lat': float(node.lat),
					'lon': float(node.lon),
					'tags': node.tags,
				}
			)

		for way in result.ways:
			track_label = way.tags.get('railway:track_ref', '')
			way_nodes = [
				{'lat': float(n.lat), 'lon': float(n.lon)} for n in way.nodes
			]

			# Create edges (segments) from consecutive node pairs
			way_edges = []
			for i in range(len(way.nodes) - 1):
				edge_id = f'{way.id}_{i}'
				edge = {
					'type': 'edge',
					'id': edge_id,
					'way_id': way.id,
					'start': {
						'lat': float(way.nodes[i].lat),
						'lon': float(way.nodes[i].lon),
					},
					'end': {
						'lat': float(way.nodes[i + 1].lat),
						'lon': float(way.nodes[i + 1].lon),
					},
					'track_label': track_label,
				}
				edges.append(edge)
				way_edges.append(edge_id)

			ways.append(
				{
					'type': 'way',
					'id': way.id,
					'geometry': way_nodes,
					'edges': way_edges,
					'tags': way.tags,
				}
			)

		return {'nodes': nodes, 'edges': edges, 'ways': ways}
	
	def _filter_inactive_tracks(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Filter out disused/abandoned/razed tracks and orphaned nodes."""
		elements = data.get('elements', [])
		
		# Filter ways
		active_ways = []
		for elem in elements:
			if elem['type'] == 'way':
				tags = elem.get('tags', {})
				is_disused = 'disused:railway' in tags or 'abandoned:railway' in tags
				is_razed = tags.get('railway') == 'razed'
				
				if is_razed and not self.include_razed:
					continue
				if is_disused and not self.include_disused:
					continue
				
				active_ways.append(elem)
		
		# Get node IDs used by active ways
		used_node_ids = set()
		for way in active_ways:
			for geom_node in way.get('geometry', []):
				# Match by coordinates
				for elem in elements:
					if (elem['type'] == 'node' and 
						abs(elem['lat'] - geom_node['lat']) < 1e-7 and 
						abs(elem['lon'] - geom_node['lon']) < 1e-7):
						used_node_ids.add(elem['id'])
		
		# Filter nodes - keep only those used by active ways
		active_nodes = []
		orphaned = 0
		for elem in elements:
			if elem['type'] == 'node':
				if elem['id'] in used_node_ids:
					active_nodes.append(elem)
				else:
					orphaned += 1
		
		filtered = active_nodes + active_ways
		if len(filtered) < len(elements):
			logger.info('Filtered %d -> %d elements (removed inactive tracks)', 
					   len(elements), len(filtered))
			if orphaned > 0:
				logger.info('Removed %d orphaned nodes', orphaned)
		return {'elements': filtered}
	
	def _remove_orphaned_nodes(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Remove nodes not connected to any ways (including orphaned switches)."""
		elements = data.get('elements', [])
		
		# Build coordinate to node mapping for faster lookup
		coord_to_node = {}
		for elem in elements:
			if elem['type'] == 'node':
				key = (round(elem['lat'], 7), round(elem['lon'], 7))
				coord_to_node[key] = elem
		
		# Collect all node IDs used in way geometries
		used_node_ids = set()
		for elem in elements:
			if elem['type'] == 'way' and 'geometry' in elem:
				for geom_node in elem['geometry']:
					key = (round(geom_node['lat'], 7), round(geom_node['lon'], 7))
					if key in coord_to_node:
						used_node_ids.add(coord_to_node[key]['id'])
		
		# Keep only used nodes and all ways
		filtered = []
		orphaned = 0
		orphaned_switches = []
		for elem in elements:
			if elem['type'] == 'way':
				filtered.append(elem)
			elif elem['type'] == 'node':
				if elem['id'] in used_node_ids:
					filtered.append(elem)
				else:
					orphaned += 1
					if elem.get('tags', {}).get('railway') == 'switch':
						switch_name = elem.get('tags', {}).get('ref') or elem.get('tags', {}).get('local_ref') or f"node_{elem['id']}"
						orphaned_switches.append(switch_name)
		
		if orphaned > 0:
			logger.info('Removed %d orphaned nodes after geometry filtering', orphaned)
			if orphaned_switches:
				logger.info('Orphaned switches: %s', ', '.join(orphaned_switches))
		return {'elements': filtered}
