"""Location tracking events for entity movement."""

from dataclasses import dataclass

from analytics.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True)
class WagonLocationChangedEvent:
    """Event fired when wagon changes location."""
    
    wagon_id: str
    from_location: str | None
    to_location: str
    timestamp: Timestamp
    context: str  # "yard", "popup", "transport"
    
    @classmethod
    def create(
        cls, 
        wagon_id: str, 
        from_location: str | None, 
        to_location: str, 
        timestamp: Timestamp,
        context: str
    ) -> 'WagonLocationChangedEvent':
        """Create wagon location changed event."""
        return cls(
            wagon_id=wagon_id,
            from_location=from_location,
            to_location=to_location,
            timestamp=timestamp,
            context=context
        )


@dataclass(frozen=True)
class LocomotiveLocationChangedEvent:
    """Event fired when locomotive changes location."""
    
    loco_id: str
    from_location: str | None
    to_location: str
    status: str  # "idle", "moving", "coupled"
    timestamp: Timestamp
    
    @classmethod
    def create(
        cls,
        loco_id: str,
        from_location: str | None,
        to_location: str,
        status: str,
        timestamp: Timestamp
    ) -> 'LocomotiveLocationChangedEvent':
        """Create locomotive location changed event."""
        return cls(
            loco_id=loco_id,
            from_location=from_location,
            to_location=to_location,
            status=status,
            timestamp=timestamp
        )