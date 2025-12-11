"""Hump yard domain service for wagon classification logic."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from contexts.configuration.domain.models.process_times import ProcessTimes
from shared.domain.services.railway_capacity_service import RailwayCapacityService
from shared.infrastructure.time_converters import to_ticks


class YardType(Enum):
    """Types of yards with different capabilities."""

    HUMP_YARD = 'hump_yard'
    FLAT_YARD = 'flat_yard'
    CLASSIFICATION_YARD = 'classification_yard'


@dataclass
class YardConfiguration:
    """Configuration for a specific yard."""

    yard_id: str
    yard_type: YardType
    has_hump: bool
    classification_tracks: list[str]
    collection_track_capacity: int
    current_collection_count: int = 0


@dataclass
class ClassificationResult:
    """Result of wagon classification."""

    accepted_wagons: list[Any]
    rejected_wagons: list[Any]
    classification_track: str = 'collection'
    yard_id: str = 'main_yard'


@dataclass
class ProcessingSchedule:
    """Schedule for processing wagons through hump yard."""

    train_to_hump_delay: float
    wagon_intervals: list[float]
    total_duration: float


class HumpYardService:
    """Domain service for yard operations - supports multiple yard types."""

    def __init__(self, railway_capacity_service: RailwayCapacityService | None = None) -> None:
        self._railway_capacity_service = railway_capacity_service

    def classify_wagons(
        self, wagons: list[Any], yard_config: YardConfiguration | None = None, selected_track: str | None = None
    ) -> ClassificationResult:
        """Classify wagons based on business rules."""
        accepted_wagons = []
        rejected_wagons = []

        # Use selected track or determine from config
        collection_track = selected_track or self._determine_classification_track(yard_config)

        # Check collection track capacity using railway infrastructure for the SELECTED track
        available_capacity = self._get_available_capacity_from_railway(yard_config, collection_track)

        for i, wagon in enumerate(wagons):
            # Check if we have capacity and wagon should be accepted
            if i < available_capacity and self._should_accept_wagon(wagon):
                wagon.status = 'COLLECTION'
                wagon.track = collection_track
                accepted_wagons.append(wagon)
            else:
                wagon.status = 'REJECTED'
                if i >= available_capacity:
                    wagon.rejection_reason = 'COLLECTION_TRACK_FULL'
                    wagon.detailed_rejection_reason = (
                        f'Collection track capacity exceeded ({available_capacity} wagons max)'
                    )
                else:
                    wagon.rejection_reason = 'CLASSIFICATION_REJECTED'
                    # detailed_rejection_reason already set by _should_accept_wagon
                rejected_wagons.append(wagon)

        yard_id = yard_config.yard_id if yard_config else 'main_yard'
        classification_track = self._determine_classification_track(yard_config)

        return ClassificationResult(
            accepted_wagons=accepted_wagons,
            rejected_wagons=rejected_wagons,
            classification_track=classification_track,
            yard_id=yard_id,
        )

    def calculate_processing_schedule(
        self,
        wagon_count: int,
        process_times: ProcessTimes | None,
        yard_config: YardConfiguration | None = None,
    ) -> ProcessingSchedule:
        """Calculate timing schedule for hump yard processing."""
        if not process_times or not self._has_hump_capability(yard_config):
            # Flat yards or no process times - minimal delays
            return ProcessingSchedule(
                train_to_hump_delay=0.0,
                wagon_intervals=[0.0] * wagon_count,
                total_duration=0.0,
            )

        # Convert process times to simulation ticks
        train_delay = to_ticks(process_times.train_to_hump_delay)
        wagon_interval = to_ticks(process_times.wagon_hump_interval)

        # Calculate intervals for each wagon
        intervals = []
        for i in range(wagon_count):
            if i == 0:
                intervals.append(0.0)  # First wagon has no additional delay
            else:
                intervals.append(wagon_interval)

        total_duration = train_delay + (wagon_count - 1) * wagon_interval

        return ProcessingSchedule(
            train_to_hump_delay=train_delay,
            wagon_intervals=intervals,
            total_duration=total_duration,
        )

    def _should_accept_wagon(self, wagon: Any) -> bool:
        """Business rule for wagon acceptance."""
        needs_retrofit = getattr(wagon, 'needs_retrofit', True)
        is_loaded = getattr(wagon, 'is_loaded', False)

        # Set detailed rejection reason on wagon
        if not needs_retrofit:
            wagon.detailed_rejection_reason = "Wagon doesn't need retrofit"
        elif is_loaded:
            wagon.detailed_rejection_reason = 'Wagon is loaded'

        return needs_retrofit and not is_loaded

    def _has_hump_capability(self, yard_config: YardConfiguration | None) -> bool:
        """Check if yard has hump capability for timing calculations."""
        if not yard_config:
            return True  # Default to hump yard behavior for backward compatibility
        return yard_config.has_hump

    def _get_available_capacity_from_railway(
        self, yard_config: YardConfiguration | None, track_id: str | None = None
    ) -> int:
        """Get available capacity from railway infrastructure context."""
        # Use railway capacity service if available
        if self._railway_capacity_service:
            classification_track = track_id or self._determine_classification_track(yard_config)
            available_meters = self._railway_capacity_service.get_maximum_acceptable_count(classification_track)
            # Return meters directly - caller will handle wagon-specific sizing
            return int(available_meters)

        # Fallback to default capacity if no railway service
        if yard_config:
            return max(
                0,
                yard_config.collection_track_capacity - yard_config.current_collection_count,
            )

        return 100  # Default large capacity for backward compatibility

    def _get_available_capacity(self, yard_config: YardConfiguration | None) -> int:
        """Get available capacity on collection track (legacy method)."""
        if not yard_config:
            return 100  # Default large capacity for backward compatibility

        return max(
            0,
            yard_config.collection_track_capacity - yard_config.current_collection_count,
        )

    def update_collection_track_count(self, yard_config: YardConfiguration, change: int) -> None:
        """Update current collection track count."""
        yard_config.current_collection_count = max(0, yard_config.current_collection_count + change)

    def _determine_classification_track(self, yard_config: YardConfiguration | None) -> str:
        """Determine appropriate classification track based on yard type."""
        if not yard_config:
            return 'collection'

        # Use first classification track from config
        if yard_config.classification_tracks:
            return yard_config.classification_tracks[0]

        # Fallback based on yard type
        if yard_config.yard_type == YardType.HUMP_YARD:
            return 'collection'
        if yard_config.yard_type == YardType.FLAT_YARD:
            return 'staging'
        return 'collection'
