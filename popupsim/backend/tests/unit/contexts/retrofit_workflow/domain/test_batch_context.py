"""Test BatchContext value object."""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.batch_context import BatchContext
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType


class TestBatchContext:
    """Test BatchContext value object."""

    def test_batch_context_creation(self) -> None:
        """Test BatchContext creation with wagons."""
        # Create test wagons
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [
            Wagon(id='W1', length=20.0, coupler_a=coupler_a, coupler_b=coupler_b),
            Wagon(id='W2', length=15.0, coupler_a=coupler_a, coupler_b=coupler_b),
        ]

        # Create batch context
        batch_context = BatchContext(wagons=wagons, workshop_id='WS1')

        # Verify properties
        assert batch_context.wagons == wagons
        assert batch_context.workshop_id == 'WS1'
        assert batch_context.locomotive is None
        assert batch_context.bay_requests is None
        assert batch_context.batch_length == 35.0
        assert batch_context.wagon_count == 2

    def test_batch_context_with_locomotive(self) -> None:
        """Test BatchContext with locomotive assigned."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]
        mock_loco = 'LOCO_001'  # Mock locomotive

        batch_context = BatchContext(wagons=wagons, workshop_id='WS1', locomotive=mock_loco)

        assert batch_context.locomotive == mock_loco
        assert batch_context.batch_length == 10.0
        assert batch_context.wagon_count == 1

    def test_batch_context_with_bay_requests(self) -> None:
        """Test BatchContext with bay requests."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]
        bay_requests = ['BAY_REQ_1', 'BAY_REQ_2']  # Mock bay requests

        batch_context = BatchContext(wagons=wagons, workshop_id='WS1', bay_requests=bay_requests)

        assert batch_context.bay_requests == bay_requests

    def test_empty_batch_context(self) -> None:
        """Test BatchContext with empty wagon list."""
        batch_context = BatchContext(wagons=[], workshop_id='WS1')

        assert batch_context.batch_length == 0.0
        assert batch_context.wagon_count == 0
