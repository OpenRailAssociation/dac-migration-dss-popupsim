"""Data models for OSM extraction."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class BoundingBox:
	"""Represents a geographic bounding box.

	Parameters
	----------
	south : float
	    Southern boundary (minimum latitude)
	west : float
	    Western boundary (minimum longitude)
	north : float
	    Northern boundary (maximum latitude)
	east : float
	    Eastern boundary (maximum longitude)
	"""

	south: float
	west: float
	north: float
	east: float

	def expand(self, buffer: float) -> 'BoundingBox':
		"""Expand bounding box by buffer distance.

		Parameters
		----------
		buffer : float
		    Buffer distance in degrees

		Returns
		-------
		BoundingBox
		    Expanded bounding box
		"""
		return BoundingBox(
			south=self.south - buffer,
			west=self.west - buffer,
			north=self.north + buffer,
			east=self.east + buffer,
		)


@dataclass(frozen=True)
class Polygon:
	"""Represents a geographic polygon.

	Parameters
	----------
	coordinates : List[Tuple[float, float]]
	    List of (latitude, longitude) coordinate pairs
	"""

	coordinates: List[Tuple[float, float]]

	def to_bbox(self) -> BoundingBox:
		"""Convert polygon to bounding box.

		Returns
		-------
		BoundingBox
		    Minimum bounding box containing the polygon
		"""
		lats = [coord[0] for coord in self.coordinates]
		lons = [coord[1] for coord in self.coordinates]

		return BoundingBox(
			south=min(lats), west=min(lons), north=max(lats), east=max(lons)
		)
