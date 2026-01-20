"""Builder for RetrofitWorkshopContext following Builder pattern."""

from typing import Any

from contexts.retrofit_workflow.application.event_collector import EventCollector
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.entities.workshop import create_workshop
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
from contexts.retrofit_workflow.infrastructure.resources.workshop_resource_manager import WorkshopResourceManager
import simpy


class RetrofitWorkshopContexttBuilder:  # pylint: disable=too-many-instance-attributes
    """Builder for creating configured RetrofitWorkshopContext."""

    def __init__(self, env: simpy.Environment, scenario: Any):
        """Initialize builder."""
        self._env = env
        self._scenario = scenario
        self._workshops: dict[str, Workshop] = {}
        self._locomotives: list[Locomotive] = []
        self._event_collector: EventCollector | None = None
        self._workshop_resources: WorkshopResourceManager | None = None
        self._locomotive_manager: LocomotiveResourceManager | None = None
        self._track_manager: Any = None

    def build_event_collector(self) -> 'RetrofitWorkshopContexttBuilder':
        """Build event collector."""
        self._event_collector = EventCollector()
        return self

    def build_entities(self) -> 'RetrofitWorkshopContexttBuilder':
        """Build domain entities."""
        # Create workshops
        for ws_config in self._scenario.workshops:
            workshop = create_workshop(
                workshop_id=ws_config.id,
                location=ws_config.track,
                bay_count=ws_config.retrofit_stations,
            )
            self._workshops[ws_config.id] = workshop

        # Create locomotives
        for loco_config in self._scenario.locomotives:
            loco = Locomotive(
                id=loco_config.id,
                home_track=loco_config.track,
                coupler_front=Coupler(CouplerType.HYBRID, 'FRONT'),
                coupler_back=Coupler(CouplerType.HYBRID, 'BACK'),
            )
            self._locomotives.append(loco)

        return self

    def build_resource_managers(self) -> 'RetrofitWorkshopContexttBuilder':
        """Build resource managers."""
        # Workshop resources
        workshop_capacities = {ws.id: ws.capacity for ws in self._workshops.values()}
        self._workshop_resources = WorkshopResourceManager(
            self._env,
            workshop_capacities,
            event_publisher=self._event_collector.add_resource_event if self._event_collector else None,
        )

        # Locomotive manager
        self._locomotive_manager = LocomotiveResourceManager(
            self._env,
            self._locomotives,
            event_publisher=self._event_collector.add_resource_event if self._event_collector else None,
        )

        return self

    def get_workshops(self) -> dict[str, Workshop]:
        """Get built workshops."""
        return self._workshops

    def get_locomotives(self) -> list[Locomotive]:
        """Get built locomotives."""
        return self._locomotives

    def get_event_collector(self) -> EventCollector | None:
        """Get built event collector."""
        return self._event_collector

    def get_workshop_resources(self) -> WorkshopResourceManager | None:
        """Get built workshop resources."""
        return self._workshop_resources

    def get_locomotive_manager(self) -> LocomotiveResourceManager | None:
        """Get built locomotive manager."""
        return self._locomotive_manager
