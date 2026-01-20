"""Train Aggregate - DDD Aggregate Root that owns wagons during arrival."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class TrainStatus(Enum):
    """Train status enum."""

    ARRIVING = 'ARRIVING'
    CLASSIFYING = 'CLASSIFYING'
    CLASSIFIED = 'CLASSIFIED'
    DEPARTED = 'DEPARTED'


@dataclass
class Train:
    """Train Aggregate Root.

    A train owns its wagons during arrival and classification.
    After classification, wagons become independent entities.

    This enforces the business rule that wagons belong to a train
    until they are classified and distributed.

    Attributes
    ----------
        id: Unique train identifier
        arrival_time: Simulation time when train arrives
        wagons: List of wagons (owned by train)
    """

    id: str
    arrival_time: float
    wagons: list[Wagon] = field(default_factory=list)

    # Private state
    _status: TrainStatus = field(default=TrainStatus.ARRIVING, init=False)
    _classification_time: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Validate train."""
        if not self.wagons:
            raise ValueError(f'Train {self.id} must have at least one wagon')

        # Set train_id on all wagons
        for wagon in self.wagons:
            wagon.train_id = self.id

    @property
    def status(self) -> TrainStatus:
        """Get train status."""
        return self._status

    @property
    def wagon_count(self) -> int:
        """Get number of wagons."""
        return len(self.wagons)

    @property
    def total_length(self) -> float:
        """Get total length in meters."""
        total: float = sum(w.length for w in self.wagons)
        return total

    @property
    def wagon_ids(self) -> list[str]:
        """Get list of wagon IDs."""
        return [w.id for w in self.wagons]

    def add_wagon(self, wagon: Wagon) -> None:
        """Add wagon to train.

        Args:
            wagon: Wagon to add

        Raises
        ------
            ValueError: If train already departed
        """
        if self._status == TrainStatus.DEPARTED:
            raise ValueError(f'Cannot add wagon to departed train {self.id}')

        wagon.train_id = self.id
        self.wagons.append(wagon)

    def remove_wagon(self, wagon_id: str) -> Wagon | None:
        """Remove wagon from train.

        Args:
            wagon_id: Wagon to remove

        Returns
        -------
            Removed wagon or None if not found

        Raises
        ------
            ValueError: If train is arriving
        """
        if self._status == TrainStatus.ARRIVING:
            raise ValueError(f'Cannot remove wagon from arriving train {self.id}')

        for wagon in self.wagons:
            if wagon.id == wagon_id:
                self.wagons.remove(wagon)
                return wagon

        return None

    def start_classification(self, classification_time: float) -> None:
        """Start classification process.

        Args:
            classification_time: Simulation time when classification starts

        Raises
        ------
            ValueError: If train not in ARRIVING status
        """
        if self._status != TrainStatus.ARRIVING:
            raise ValueError(f'Cannot start classification for train {self.id} in status {self._status}')

        self._status = TrainStatus.CLASSIFYING
        self._classification_time = classification_time

    def complete_classification(self) -> list[Wagon]:
        """Complete classification and release wagons.

        After classification, wagons become independent entities.
        Train no longer owns them.

        Returns
        -------
            List of classified wagons (ownership transferred)

        Raises
        ------
            ValueError: If train not classifying
        """
        if self._status != TrainStatus.CLASSIFYING:
            raise ValueError(f'Cannot complete classification for train {self.id} in status {self._status}')

        # Classify all wagons
        for wagon in self.wagons:
            wagon.classify()

        # Transfer ownership - return wagons
        classified_wagons = self.wagons.copy()

        self._status = TrainStatus.CLASSIFIED

        return classified_wagons

    def depart(self) -> None:
        """Mark train as departed.

        Raises
        ------
            ValueError: If train not classified
        """
        if self._status != TrainStatus.CLASSIFIED:
            raise ValueError(f'Cannot depart train {self.id} in status {self._status}')

        self._status = TrainStatus.DEPARTED

        # Clear wagon list (ownership already transferred)
        self.wagons.clear()

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f'Train(id={self.id}, status={self._status.value}, '
            f'wagons={self.wagon_count}, length={self.total_length:.1f}m)'
        )
