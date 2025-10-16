"""OSM railway data extractor."""

import logging
from typing import Any
from typing import Dict
from typing import Union

import overpy

from .exceptions import InvalidQueryError
from .exceptions import QueryTimeoutError
from .exceptions import RateLimitError
from .geometry import filter_osm_data
from .models import BoundingBox
from .models import Polygon

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
		railway_types: list = ['rail', 'siding', 'yard', 'spur'],
		node_types: list = ['switch', 'buffer_stop'],
	) -> None:
		self.api = overpy.Overpass(url=overpass_url)
		self.timeout = timeout
		self.railway_types = railway_types
		self.node_types = node_types
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

		query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["railway"~"^({railway_regex})$"]{area_filter};
          node["railway"~"^({node_regex})$"]{area_filter};
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
			data = self._convert_to_json(result)
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
