"""Configuration builder for step-by-step scenario building."""

from typing import Any

from contexts.configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from contexts.configuration.domain.models.scenario import Scenario
from contexts.configuration.infrastructure.file_loader import FileLoader
from shared.validation.base import ValidationIssue
from shared.validation.base import ValidationResult

from .models import ComponentInfo
from .models import ComponentStatus
from .models import ConfigurationState
from .models import ConfigurationStatus
from .models import LocomotiveConfig
from .models import ProcessTimesConfig
from .models import ScenarioMetadata
from .models import StrategiesConfig
from .models import TopologyConfig
from .models import TrackConfig
from .models import WorkshopConfig



class ConfigurationBuilder:  # pylint: disable=too-many-instance-attributes
    """Builds scenario configuration step-by-step."""

    def __init__(self, path_or_metadata: Any) -> None:
        if isinstance(path_or_metadata, ScenarioMetadata):
            self.metadata = path_or_metadata
            self._path = None
        else:
            self._path = path_or_metadata
            self.metadata = None
        self._workshops: list[WorkshopConfig] = []
        self._tracks: list[TrackConfig] = []
        self._locomotives: list[LocomotiveConfig] = []
        self._process_times: ProcessTimesConfig | None = None
        self._topology: TopologyConfig | None = None
        self._strategies: StrategiesConfig | None = None
        self._is_finalized = False

    def add_workshop(self, workshop: WorkshopConfig) -> ValidationResult:
        """Add workshop configuration."""
        # Validate workshop

        if workshop.retrofit_stations <= 0:
            issue = ValidationIssue(message='retrofit_stations must be greater than 0')
            return ValidationResult(is_valid=False, issues=[])

        # Check for duplicates
        if any(w.id == workshop.id for w in self._workshops):
            return ValidationResult(is_valid=False, issues=[f'Workshop {workshop.id} already exists'])

        self._workshops.append(workshop)
        return ValidationResult(is_valid=True, issues=[])

    def add_track(self, track: TrackConfig) -> ValidationResult:
        """Add track configuration."""
        # Validate track
        if track.capacity <= 0:
            return ValidationResult(is_valid=False, issues=['capacity must be greater than 0'])

        # Check for duplicates
        if any(t.id == track.id for t in self._tracks):
            return ValidationResult(is_valid=False, issues=[f'Track {track.id} already exists'])

        self._tracks.append(track)
        return ValidationResult(is_valid=True, issues=[])

    def add_locomotive(self, locomotive: LocomotiveConfig) -> ValidationResult:
        """Add locomotive configuration."""
        # Validate locomotive
        if locomotive.max_wagons <= 0:
            return ValidationResult(is_valid=False, issues=['max_wagons must be greater than 0'])

        # Check for duplicates
        if any(loco.id == locomotive.id for loco in self._locomotives):
            return ValidationResult(is_valid=False, issues=[f'Locomotive {locomotive.id} already exists'])

        self._locomotives.append(locomotive)
        return ValidationResult(is_valid=True, issues=[])

    def set_process_times(self, times: ProcessTimesConfig) -> ValidationResult:
        """Set process times configuration."""
        self._process_times = times
        return ValidationResult(is_valid=True, issues=[])

    def set_topology(self, topology: TopologyConfig) -> ValidationResult:
        """Set topology configuration."""
        # Validate topology connections reference existing tracks
        track_ids = {t.id for t in self._tracks}
        issues = []

        for conn in topology.connections:
            if conn.from_track not in track_ids:
                issues.append(f'Track {conn.from_track} not found')
            if conn.to_track not in track_ids:
                issues.append(f'Track {conn.to_track} not found')

        if issues:
            return ValidationResult(is_valid=False, issues=issues)

        self._topology = topology
        return ValidationResult(is_valid=True, issues=[])

    def set_strategies(self, strategies: StrategiesConfig) -> ValidationResult:
        """Set selection strategies configuration."""
        self._strategies = strategies
        return ValidationResult(is_valid=True, issues=[])

    def get_configuration_state(self) -> ConfigurationState:
        """Get current configuration state."""
        components = self._calculate_component_status()
        completion_percentage = self._calculate_completion_percentage(components)
        validation_issues = self._get_validation_issues()
        can_finalize = self._can_finalize(components, validation_issues)

        status = ConfigurationStatus.READY if can_finalize else ConfigurationStatus.DRAFT
        if validation_issues:
            status = ConfigurationStatus.INVALID

        return ConfigurationState(
            scenario_id=self.metadata.id,
            metadata=self.metadata,
            status=status,
            completion_percentage=completion_percentage,
            components=components,
            workshops=self._workshops.copy(),
            tracks=self._tracks.copy(),
            locomotives=self._locomotives.copy(),
            process_times=self._process_times,
            topology=self._topology,
            strategies=self._strategies,
            validation_issues=validation_issues,
            can_finalize=can_finalize,
        )

    def validate_completeness(self) -> ValidationResult:
        """Validate configuration completeness."""
        issues: list[ValidationIssue] = []

        if not self._workshops:
            issues.append('At least one workshop is required')
        if not self._tracks:
            issues.append('At least one track is required')
        if not self._locomotives:
            issues.append('At least one locomotive is required')
        if not self._process_times:
            issues.append('Process times must be configured')
        if not self._topology:
            issues.append('Topology must be configured')

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def build(self) -> Any:
        """Build scenario from file path."""
        if self._path:
            return FileLoader(self._path).load()
        return self.build_scenario()

    def build_scenario(self) -> Any:
        """Build final scenario object (MVP compatible)."""
        workshop_dtos = [
            WorkshopInputDTO(id=w.id, track=w.track, retrofit_stations=w.retrofit_stations) for w in self._workshops
        ]

        return Scenario(
            id=self.metadata.id,
            start_date=self.metadata.start_date,
            end_date=self.metadata.end_date,
            workshops=workshop_dtos,
            locomotives=None,
            tracks=None,
            topology=None,
            process_times=None,
            trains=None,
            routes=None,
        )

    def _calculate_component_status(self) -> dict[str, ComponentInfo]:
        """Calculate status for each component."""
        return {
            'workshops': ComponentInfo(
                name='workshops',
                status=ComponentStatus.COMPLETE if self._workshops else ComponentStatus.MISSING,
                count=len(self._workshops),
                validation_issues=[],
            ),
            'tracks': ComponentInfo(
                name='tracks',
                status=ComponentStatus.COMPLETE if self._tracks else ComponentStatus.MISSING,
                count=len(self._tracks),
                validation_issues=[],
            ),
            'locomotives': ComponentInfo(
                name='locomotives',
                status=ComponentStatus.COMPLETE if self._locomotives else ComponentStatus.MISSING,
                count=len(self._locomotives),
                validation_issues=[],
            ),
            'process_times': ComponentInfo(
                name='process_times',
                status=ComponentStatus.COMPLETE if self._process_times else ComponentStatus.MISSING,
                count=1 if self._process_times else 0,
                validation_issues=[],
            ),
            'topology': ComponentInfo(
                name='topology',
                status=ComponentStatus.COMPLETE if self._topology else ComponentStatus.MISSING,
                count=len(self._topology.connections) if self._topology else 0,
                validation_issues=[],
            ),
        }

    def _calculate_completion_percentage(self, components: dict[str, ComponentInfo]) -> int:
        """Calculate completion percentage."""
        total_components = len(components)
        completed_components = sum(1 for c in components.values() if c.status == ComponentStatus.COMPLETE)
        return int((completed_components / total_components) * 100) if total_components > 0 else 0

    def _get_validation_issues(self) -> list[str]:
        """Get current validation issues."""
        issues = []

        if len(self._locomotives) < len(self._workshops):
            issues.append(f'Only {len(self._locomotives)} locomotive(s) for {len(self._workshops)} workshop(s)')

        return issues

    def _can_finalize(self, components: dict[str, ComponentInfo], validation_issues: list[str]) -> bool:
        """Check if configuration can be finalized."""
        required_complete = all(
            c.status == ComponentStatus.COMPLETE
            for name, c in components.items()
            if name in ['workshops', 'tracks', 'locomotives', 'process_times']
        )
        no_critical_issues = not any('required' in issue.lower() for issue in validation_issues)
        return required_complete and no_critical_issues
