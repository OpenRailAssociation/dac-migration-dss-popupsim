"""Geometry utilities for filtering OSM data."""

import logging
from typing import Any
from typing import Dict
from typing import Union

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box

from .models import BoundingBox
from .models import Polygon
from .validators import validate_bbox
from .validators import validate_polygon

logger = logging.getLogger(__name__)


def _create_shapely_geometry(
	boundary: Union[BoundingBox, Polygon],
) -> Union[ShapelyPolygon, box]:
	"""Create Shapely geometry from boundary.

	Parameters
	----------
	boundary : Union[BoundingBox, Polygon]
	    Geographic boundary to convert

	Returns
	-------
	Union[ShapelyPolygon, box]
	    Shapely geometry object
	"""
	if isinstance(boundary, BoundingBox):
		validate_bbox(
			boundary.south, boundary.west, boundary.north, boundary.east
		)
		return box(
			boundary.west, boundary.south, boundary.east, boundary.north
		)
	validate_polygon(boundary.coordinates)
	return ShapelyPolygon([(lon, lat) for lat, lon in boundary.coordinates])


def filter_way_geometry(
	way: Dict[str, Any], boundary: Union[BoundingBox, Polygon]
) -> Dict[str, Any] | None:
	"""Filter way geometry to only include segments within boundary.

	Clips railway way geometry to boundary using geometric intersection.
	Handles tracks that cross boundaries multiple times by creating
	separate segments for each continuous portion inside the boundary.

	Parameters
	----------
	way : Dict[str, Any]
	    OSM way element with geometry
	boundary : Union[BoundingBox, Polygon]
	    Geographic boundary for filtering

	Returns
	-------
	Dict[str, Any]
	    Filtered way with geometry clipped to boundary, or None if no
	    valid segments remain
	"""
	if 'geometry' not in way or len(way['geometry']) < 2:
		return way

	shapely_boundary = _create_shapely_geometry(boundary)
	coords = [(node['lon'], node['lat']) for node in way['geometry']]
	line = LineString(coords)

	# Get intersection with boundary
	intersection = line.intersection(shapely_boundary)

	if intersection.is_empty:
		return None

	if hasattr(intersection, 'geoms'):
		segments = list(intersection.geoms)
	elif intersection.geom_type == 'LineString':
		segments = [intersection]
	else:
		return None

	# Convert back to OSM format
	filtered_nodes = []
	for segment in segments:
		if len(segment.coords) >= 2:
			for lon, lat in segment.coords:
				filtered_nodes.append({'lat': lat, 'lon': lon})

	if len(filtered_nodes) >= 2:
		way['geometry'] = filtered_nodes
		return way

	return None


def filter_osm_data(
	data: Dict[str, Any], boundary: Union[BoundingBox, Polygon]
) -> Dict[str, Any]:
	"""Filter OSM data to remove elements outside boundary.

	Removes all nodes and ways that lie completely outside the specified
	boundary. For ways that cross the boundary, clips geometry to only
	include segments within the boundary.

	Parameters
	----------
	data : Dict[str, Any]
	    OSM JSON data from Overpass API
	boundary : Union[BoundingBox, Polygon]
	    Geographic boundary for filtering

	Returns
	-------
	Dict[str, Any]
	    Filtered OSM data with only elements within boundary
	"""
	logger.debug('Filtering OSM data to boundary')
	shapely_boundary = _create_shapely_geometry(boundary)
	filtered_elements = []
	node_count = 0
	way_count = 0

	for element in data.get('elements', []):
		if element['type'] == 'node':
			point = Point(element['lon'], element['lat'])
			if shapely_boundary.contains(point):
				filtered_elements.append(element)
				node_count += 1

		elif element['type'] == 'way':
			filtered_way = filter_way_geometry(element, boundary)
			if filtered_way:
				filtered_elements.append(filtered_way)
				way_count += 1

	logger.debug(
		'Filtered to %d nodes and %d ways within boundary',
		node_count,
		way_count,
	)
	return {**data, 'elements': filtered_elements}
