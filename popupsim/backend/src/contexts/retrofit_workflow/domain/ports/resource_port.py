"""Resource port for selectable resources."""

from abc import ABC
from abc import abstractmethod


class ResourcePort(ABC):
    """Port defining interface for selectable resources.

    Any resource (Workshop, Track, etc.) must implement this port
    to be compatible with resource selection services.
    """

    @abstractmethod
    def get_available_capacity(self) -> float:
        """Get current available capacity.

        Returns
        -------
        float
            Available capacity in appropriate units
        """

    @abstractmethod
    def get_queue_length(self) -> int:
        """Get current queue length.

        Returns
        -------
        int
            Number of items waiting
        """
