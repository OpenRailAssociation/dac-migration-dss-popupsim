"""Track resource manager for locomotive coordination."""

from typing import Any


class TrackResourceManager:
    """Manages track occupation using SimPy Resources."""

    def __init__(
        self, engine: Any, tracks: list[Any], loco_parking_capacity: int = 3
    ) -> None:
        self.engine = engine
        self.track_resources: dict[str, Any] = {}

        for track in tracks:
            if track.id in ("loco_parking", "track_19"):
                capacity = loco_parking_capacity
            else:
                capacity = 1
            self.track_resources[track.id] = engine.create_resource(capacity)

    def request_track(self, track_id: str) -> Any:
        """Request access to a track (blocking)."""
        return self.track_resources[track_id].request()

    def release_track(self, track_id: str, request: Any) -> None:
        """Release a track."""
        self.track_resources[track_id].release(request)
