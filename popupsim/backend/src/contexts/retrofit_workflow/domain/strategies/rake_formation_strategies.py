"""Strategy patterns for different rake types."""

from abc import ABC
from abc import abstractmethod
from typing import Any

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class RakeFormationStrategy(ABC):
    """Abstract strategy for rake formation."""

    @abstractmethod
    def form_rake(self, wagons: list[Wagon], context: Any) -> Rake:
        """Form rake using specific strategy."""

    @abstractmethod
    def can_handle(self, rake_type: RakeType) -> bool:
        """Check if strategy can handle rake type."""


class CollectionRakeStrategy(RakeFormationStrategy):
    """Strategy for collection-to-retrofit rakes."""

    def form_rake(self, wagons: list[Wagon], context: Any) -> Rake:
        """Form collection rake."""
        return Rake(
            id=f'COL-{len(wagons)}-{context.get("timestamp", 0)}',
            wagon_ids=[w.id for w in wagons],
            rake_type=RakeType.COLLECTION_RAKE,
            formation_track=context.get('formation_track', 'collection'),
            target_track=context.get('target_track', 'retrofit'),
        )

    def can_handle(self, rake_type: RakeType) -> bool:
        """Check if can handle collection rakes."""
        return rake_type == RakeType.COLLECTION_RAKE


class WorkshopRakeStrategy(RakeFormationStrategy):
    """Strategy for workshop transport rakes."""

    def form_rake(self, wagons: list[Wagon], context: Any) -> Rake:
        """Form workshop rake."""
        return Rake(
            id=f'WS-{len(wagons)}-{context.get("timestamp", 0)}',
            wagon_ids=[w.id for w in wagons],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track=context.get('formation_track', 'retrofit'),
            target_track=context.get('target_track', 'workshop'),
        )

    def can_handle(self, rake_type: RakeType) -> bool:
        """Check if can handle workshop rakes."""
        return rake_type == RakeType.WORKSHOP_RAKE


class RakeFormationStrategyFactory:
    """Factory for rake formation strategies."""

    def __init__(self) -> None:
        self._strategies = [CollectionRakeStrategy(), WorkshopRakeStrategy()]

    def get_strategy(self, rake_type: RakeType) -> RakeFormationStrategy:
        """Get strategy for rake type."""
        for strategy in self._strategies:
            if strategy.can_handle(rake_type):
                return strategy

        raise ValueError(f'No strategy found for rake type: {rake_type}')

    def register_strategy(self, strategy: RakeFormationStrategy) -> None:
        """Register custom strategy."""
        self._strategies.append(strategy)
