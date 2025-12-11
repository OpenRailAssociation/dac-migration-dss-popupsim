"""Yard operations domain events."""

from typing import Any

from infrastructure.events.base_event import DomainEvent


class WagonClassifiedEvent(DomainEvent):
    """Event fired when wagon is classified."""

    def __init__(
        self,
        wagon_id: str,
        decision_type: str,
        target_location: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.wagon_id = wagon_id
        self.decision_type = decision_type
        self.target_location = target_location


class WagonDistributedEvent(DomainEvent):
    """Event fired when wagon is distributed to workshop."""

    def __init__(self, wagon_id: str, workshop_id: str, batch_id: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.wagon_id = wagon_id
        self.workshop_id = workshop_id
        self.batch_id = batch_id


class WagonParkedEvent(DomainEvent):
    """Event fired when wagon is parked."""

    def __init__(self, wagon_id: str, parking_area_id: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.wagon_id = wagon_id
        self.parking_area_id = parking_area_id
