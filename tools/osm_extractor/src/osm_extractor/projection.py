""""""

import numpy as np


def elliptical_mercator(lat: float, lon: float) -> tuple[float, float]:
	"""Convert WGS84 coordinates to elliptical Mercator projection.

	The projection uses the (true) mercator elliptical mercator
	projection using the major radius of 6378137.0 and minor radius of
	6356752.3142. The projection will have singularities at the poles
	and therefore latitutes greater 89.5 deg and smaller -89.5 deg are
	clamped.

	Parameters
	----------
	lat : float
	    Latitude in degrees
	lon : float
	    Longitude in degrees

	Returns
	-------
	tuple[float, float]
	    (x, y) coordinates in elliptical Mercator projection
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
