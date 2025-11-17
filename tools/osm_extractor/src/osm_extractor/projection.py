"""Elliptical Mercator projection for railway network coordinates.

This module implements a true elliptical Mercator projection using the
WGS84 ellipsoid parameters. The projection converts geographic coordinates
(latitude, longitude) to Cartesian coordinates (x, y) in meters, suitable
for railway simulation and distance calculations.

Projection parameters:
- Semi-major axis (a): 6378137.0 m
- Semi-minor axis (b): 6356752.3142 m
- Eccentricity: sqrt(1 - (b/a)²) ≈ 0.0818

The projection preserves angles (conformal) and is suitable for local
area calculations typical in railway operations.
"""

import numpy as np


def elliptical_mercator(lat: float, lon: float) -> tuple[float, float]:
	"""Convert WGS84 coordinates to elliptical Mercator projection.

	The projection uses the true elliptical Mercator projection based on
	the WGS84 ellipsoid with semi-major axis a=6378137.0m and semi-minor
	axis b=6356752.3142m. This is suitable for railway network simulations
	as it preserves local distances and angles reasonably well.

	Note: This is NOT the same as Web Mercator (EPSG:3857) which uses a
	spherical approximation. This implementation uses the full ellipsoidal
	formula for higher accuracy.

	The projection has singularities at the poles, so latitudes greater
	than 89.5° and smaller than -89.5° are clamped.

	Parameters
	----------
	lat : float
	    Latitude in degrees (WGS84/EPSG:4326)
	lon : float
	    Longitude in degrees (WGS84/EPSG:4326)

	Returns
	-------
	tuple[float, float]
	    (x, y) coordinates in meters in elliptical Mercator projection
	"""
	r_major = 6378137.0
	r_minor = 6356752.3142

	if lat > 89.5:
		lat = 89.5
	if lat < -89.5:
		lat = -89.5

	x = r_major * np.radians(lon)

	eccent = np.sqrt(1 - (r_minor / r_major) ** 2)
	phi = np.radians(lat)
	sinphi = np.sin(phi)
	con = eccent * sinphi
	com = 0.5 * eccent
	con = ((1.0 - con) / (1.0 + con)) ** com
	ts = np.tan(0.5 * (0.5 * np.pi - phi)) / con
	y = -r_major * np.log(ts)

	return x, y
