"""Configuration domain exceptions."""


class DataSourceError(Exception):
    """Exception raised when data source operations fail.

    This exception is raised when data cannot be loaded from a source,
    the source is invalid, or other data source-related errors occur.
    """
