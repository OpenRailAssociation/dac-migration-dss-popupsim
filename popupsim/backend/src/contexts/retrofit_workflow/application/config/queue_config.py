"""Queue configuration for retrofit workflow context."""

from dataclasses import dataclass

import simpy


@dataclass
class QueueConfig:
    """Configuration for SimPy queues used in coordination."""

    collection_queue: simpy.FilterStore
    retrofit_queue: simpy.FilterStore
    retrofitted_queue: simpy.FilterStore

    def get_queue_sizes(self) -> dict[str, int]:
        """Get current sizes of all queues."""
        return {
            'collection': len(self.collection_queue.items),
            'retrofit': len(self.retrofit_queue.items),
            'retrofitted': len(self.retrofitted_queue.items),
        }

    def get_total_wagons(self) -> int:
        """Get total number of wagons in all queues."""
        return sum(self.get_queue_sizes().values())
