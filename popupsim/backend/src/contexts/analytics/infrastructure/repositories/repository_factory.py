"""Factory for creating analytics repositories."""

from pathlib import Path
from typing import Literal

from contexts.analytics.domain.repositories.analytics_repository import AnalyticsRepository

from .csv_analytics_repository import CSVAnalyticsRepository
from .in_memory_analytics_repository import InMemoryAnalyticsRepository
from .json_analytics_repository import JSONAnalyticsRepository

RepositoryType = Literal['memory', 'csv', 'json']


class AnalyticsRepositoryFactory:
    """Factory for creating analytics repositories."""

    @staticmethod
    def create(repository_type: RepositoryType = 'memory', storage_path: Path | None = None) -> AnalyticsRepository:
        """Create analytics repository based on type.

        Args:
            repository_type: Type of repository ('memory', 'csv', 'json')
            storage_path: Path for file-based repositories

        Returns
        -------
            AnalyticsRepository instance
        """
        if repository_type == 'memory':
            return InMemoryAnalyticsRepository()

        if repository_type == 'csv':
            if not storage_path:
                storage_path = Path('output/analytics/csv')
            return CSVAnalyticsRepository(storage_path)

        if repository_type == 'json':
            if not storage_path:
                storage_path = Path('output/analytics/json')
            return JSONAnalyticsRepository(storage_path)

        msg = f'Unknown repository type: {repository_type}'
        raise ValueError(msg)
