"""Custom exceptions for OSM extractor."""


class OSMExtractorError(Exception):
	"""Base exception for OSM extractor."""


class ExtractionError(OSMExtractorError):
	"""Error during data extraction from Overpass API."""


class RateLimitError(ExtractionError):
	"""Overpass API rate limit exceeded."""


class QueryTimeoutError(ExtractionError):
	"""Overpass API query timeout."""


class InvalidQueryError(ExtractionError):
	"""Invalid Overpass QL query syntax."""


class GeometryError(OSMExtractorError):
	"""Error during geometry operations."""


class ProjectionError(OSMExtractorError):
	"""Error during coordinate projection."""


class PlottingError(OSMExtractorError):
	"""Error during visualization."""
