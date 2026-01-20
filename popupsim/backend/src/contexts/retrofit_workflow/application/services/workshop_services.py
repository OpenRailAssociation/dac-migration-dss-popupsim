"""Concrete implementations of segregated workshop interfaces."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.commands.transport_commands import BatchFromWorkshopTransport
from contexts.retrofit_workflow.application.commands.transport_commands import BatchToWorkshopTransport
from contexts.retrofit_workflow.application.config.transport_config import EventPublishers
from contexts.retrofit_workflow.application.config.transport_config import TransportConfig
from contexts.retrofit_workflow.application.config.workshop_service_config import WorkshopEventPublishers
from contexts.retrofit_workflow.application.config.workshop_service_config import WorkshopServiceConfig
from contexts.retrofit_workflow.application.interfaces.workshop_interfaces import BatchProcessor
from contexts.retrofit_workflow.application.interfaces.workshop_interfaces import TransportOrchestrator
from contexts.retrofit_workflow.application.interfaces.workshop_interfaces import WorkshopResourceAllocator
from contexts.retrofit_workflow.application.interfaces.workshop_interfaces import WorkshopScheduler
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.value_objects.batch_context import BatchContext
import simpy


class WorkshopBatchProcessor(BatchProcessor):  # pylint: disable=too-few-public-methods
    """Concrete implementation for batch processing."""

    def __init__(self, config: WorkshopServiceConfig, event_publishers: WorkshopEventPublishers) -> None:
        """Initialize batch processor.

        Parameters
        ----------
        config : WorkshopServiceConfig
            Workshop service configuration
        event_publishers : WorkshopEventPublishers
            Event publishing configuration
        """
        self.config = config
        self.publishers = event_publishers

    def process_batch(self, batch_context: BatchContext, workshop: Workshop) -> Generator[Any, Any]:
        """Process a batch of wagons in workshop."""
        # Start retrofit for all wagons simultaneously
        start_time = self.config.env.now
        for wagon in batch_context.wagons:
            wagon.start_retrofit(workshop.id, start_time)
            workshop.assign_to_bay(wagon.id, start_time)

            # Publish RETROFIT_STARTED event
            if self.publishers.wagon_event_publisher:
                self.publishers.wagon_event_publisher(
                    WagonJourneyEvent(
                        timestamp=start_time,
                        wagon_id=wagon.id,
                        event_type='RETROFIT_STARTED',
                        location=workshop.id,
                        status='RETROFITTING',
                    )
                )

        # Wait for retrofit to complete
        yield self.config.env.timeout(self.config.retrofit_time)

        # Complete retrofit for all wagons
        end_time = self.config.env.now
        for wagon in batch_context.wagons:
            wagon.complete_retrofit(end_time)
            bay = workshop.get_wagon_bay(wagon.id)
            if bay:
                workshop.complete_retrofit(bay.id)

            # Publish RETROFIT_COMPLETED event
            if self.publishers.wagon_event_publisher:
                self.publishers.wagon_event_publisher(
                    WagonJourneyEvent(
                        timestamp=end_time,
                        wagon_id=wagon.id,
                        event_type='RETROFIT_COMPLETED',
                        location=workshop.id,
                        status='COMPLETED',
                    )
                )


class WorkshopBayAllocator(WorkshopResourceAllocator):
    """Concrete implementation for workshop resource allocation."""

    def __init__(self, config: WorkshopServiceConfig) -> None:
        """Initialize bay allocator.

        Parameters
        ----------
        config : WorkshopServiceConfig
            Workshop service configuration
        """
        self.config = config

    def allocate_bays(self, workshop_id: str, wagon_count: int) -> Generator[Any, Any, list[Any]]:
        """Allocate workshop bays for wagons."""
        bay_requests = []
        for _ in range(wagon_count):
            req = yield from self.config.workshop_resources.request_bay(workshop_id)
            bay_requests.append(req)
        return bay_requests

    def release_bays(self, workshop_id: str, bay_requests: list[Any]) -> None:
        """Release workshop bays."""
        for req in bay_requests:
            self.config.workshop_resources.release_bay(workshop_id, req)


class CommandBasedTransportOrchestrator(TransportOrchestrator):
    """Transport orchestrator using command pattern."""

    def __init__(
        self,
        transport_config: TransportConfig,
        retrofitted_queue: simpy.FilterStore,
        event_publishers: EventPublishers,
    ) -> None:
        """Initialize transport orchestrator.

        Parameters
        ----------
        transport_config : TransportConfig
            Core transport dependencies and configuration
        retrofitted_queue : simpy.FilterStore
            Queue for retrofitted wagons
        event_publishers : EventPublishers
            Event publishing configuration
        """
        self.transport_config = transport_config
        self.retrofitted_queue = retrofitted_queue
        self.event_publishers = event_publishers

    def transport_to_workshop(self, batch_context: BatchContext) -> Generator[Any, Any]:
        """Transport batch to workshop."""
        command = BatchToWorkshopTransport(
            transport_config=self.transport_config,
            batch_context=batch_context,
            event_publishers=self.event_publishers,
        )
        yield from command.execute()

    def transport_from_workshop(self, batch_context: BatchContext) -> Generator[Any, Any]:
        """Transport batch from workshop."""
        command = BatchFromWorkshopTransport(
            transport_config=self.transport_config,
            batch_context=batch_context,
            retrofitted_queue=self.retrofitted_queue,
            event_publishers=self.event_publishers,
        )
        yield from command.execute()


class StrategyBasedWorkshopScheduler(WorkshopScheduler):
    """Workshop scheduler using strategy pattern."""

    def __init__(self, config: WorkshopServiceConfig) -> None:
        """Initialize workshop scheduler.

        Parameters
        ----------
        config : WorkshopServiceConfig
            Workshop service configuration
        """
        self.config = config

    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select next workshop for processing."""
        result = self.config.assignment_strategy.select_next_workshop(workshops, current_index)
        return result  # type: ignore[no-any-return]

    def can_process_batch(self, workshop: Workshop, wagons: list[Wagon]) -> bool:
        """Check if workshop can process batch."""
        result = self.config.batch_service.can_form_batch(wagons, workshop.available_capacity)
        return result  # type: ignore[no-any-return]
