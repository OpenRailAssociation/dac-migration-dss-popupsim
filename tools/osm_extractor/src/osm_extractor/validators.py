"""Input validation utilities."""

from typing import List, Tuple

from .exceptions import OSMExtractorError


class ValidationError(OSMExtractorError):
	"""Validation error."""


def validate_coordinates(lat: float, lon: float) -> None:
	"""Validate latitude and longitude.

	Parameters
	----------
	lat : float
		Latitude in degrees
	lon : float
		Longitude in degrees

	Raises
	------
	ValidationError
		If coordinates are out of valid range
	"""
	if not -90 <= lat <= 90:
		raise ValidationError(f'Latitude {lat} out of range [-90, 90]')
	if not -180 <= lon <= 180:
		raise ValidationError(f'Longitude {lon} out of range [-180, 180]')


def validate_bbox(
	south: float, west: float, north: float, east: float
) -> None:
	"""Validate bounding box.

	Parameters
	----------
	south : float
		Southern latitude
	west : float
		Western longitude
	north : float
		Northern latitude
	east : float
		Eastern longitude

	Raises
	------
	ValidationError
		If bbox is invalid
	"""
	validate_coordinates(south, west)
	validate_coordinates(north, east)

	if south >= north:
		raise ValidationError(f'South {south} >= North {north}')
	if west >= east:
		raise ValidationError(f'West {west} >= East {east}')


def validate_polygon(coordinates: List[Tuple[float, float]]) -> None:
	"""Validate polygon coordinates.

	Parameters
	----------
	coordinates : List[Tuple[float, float]]
		List of (lat, lon) coordinate pairs

	Raises
	------
	ValidationError
		If polygon is invalid
	"""
	if len(coordinates) < 3:
		raise ValidationError(
			f'Polygon requires at least 3 points, got {len(coordinates)}'
		)

	for i, (lat, lon) in enumerate(coordinates):
		try:
			validate_coordinates(lat, lon)
		except ValidationError as e:
			raise ValidationError(f'Point {i}: {e}') from e
