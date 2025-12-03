"""Location tracking service for entity visualization."""

from dataclasses import dataclass
from typing import Any

from analytics.domain.events.location_events import LocomotiveLocationChangedEvent
from analytics.domain.events.location_events import WagonLocationChangedEvent


@dataclass
class LocationInfo:
    """Location information for an entity."""
    
    entity_id: str
    location: str
    context: str
    timestamp: float


class LocationTracker:
    """Tracks all entity locations across contexts for visualization."""
    
    def __init__(self) -> None:
        self.wagon_locations: dict[str, LocationInfo] = {}
        self.loco_locations: dict[str, LocationInfo] = {}
    
    def on_wagon_location_changed(self, event: WagonLocationChangedEvent) -> None:
        """Handle wagon location change event."""
        self.wagon_locations[event.wagon_id] = LocationInfo(
            entity_id=event.wagon_id,
            location=event.to_location,
            context=event.context,
            timestamp=event.timestamp.value
        )
    
    def on_locomotive_location_changed(self, event: LocomotiveLocationChangedEvent) -> None:
        """Handle locomotive location change event."""
        self.loco_locations[event.loco_id] = LocationInfo(
            entity_id=event.loco_id,
            location=event.to_location,
            context="shunting",
            timestamp=event.timestamp.value
        )
    
    def get_wagon_location(self, wagon_id: str) -> str:
        """Get current wagon location."""
        return self.wagon_locations.get(wagon_id, LocationInfo("", "unknown", "", 0.0)).location
    
    def get_wagons_at_location(self, location: str) -> list[str]:
        """Get all wagons at a specific location."""
        return [
            info.entity_id 
            for info in self.wagon_locations.values() 
            if info.location == location
        ]
    
    def get_all_wagon_locations(self) -> dict[str, LocationInfo]:
        """Get all wagon locations."""
        return self.wagon_locations.copy()
    
    def get_yard_snapshot(self) -> dict[str, Any]:
        """Get snapshot of yard entities for visualization."""
        return {
            "wagons": self.get_wagons_at_location("yard"),
            "locomotives": [
                info.entity_id 
                for info in self.loco_locations.values() 
                if info.location == "yard"
            ]
        }