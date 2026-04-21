"""Wagon accumulation service for collecting wagons to thresholds."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class WagonAccumulationService:
    """Domain service for wagon accumulation strategies."""

    def accumulate_to_threshold(
        self, first_wagon: Wagon, queue: Any, threshold_length: float
    ) -> Generator[Any, Any, list[Wagon]]:
        """Accumulate wagons to specified threshold length.

        Args:
            first_wagon: First wagon already retrieved
            queue: Queue to get additional wagons from
            threshold_length: Target accumulation length

        Yields
        ------
            SimPy events for wagon retrieval

        Returns
        -------
            List of accumulated wagons
        """
        wagons = [first_wagon]
        total_length = first_wagon.length

        while total_length < threshold_length and len(queue.items) > 0:
            next_wagon: Wagon = yield queue.get()
            wagons.append(next_wagon)
            total_length += next_wagon.length

        return wagons

    def collect_wagons_for_capacity(
        self, first_wagon: Wagon, queue: Any, available_capacity: float
    ) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available capacity.

        Args:
            first_wagon: First wagon already retrieved
            queue: Queue to get additional wagons from
            available_capacity: Available capacity to fill

        Yields
        ------
            SimPy events for wagon retrieval

        Returns
        -------
            List of wagons that fit in capacity
        """
        wagons = [first_wagon]
        total_length = first_wagon.length

        while len(queue.items) > 0:
            next_wagon_length = queue.items[0].length
            if total_length + next_wagon_length <= available_capacity:
                next_wagon: Wagon = yield queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

        return wagons
