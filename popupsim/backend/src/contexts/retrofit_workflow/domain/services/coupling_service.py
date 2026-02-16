"""Coupling Service - calculates coupling/decoupling times for rakes and locomotives."""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class CouplingService:
    """Service for calculating coupling/decoupling times.

    Handles both rake coupling (wagon-to-wagon) and locomotive coupling (loco-to-rake).
    Times are based on coupler types (SCREW vs DAC).
    """

    def __init__(self, process_times: any) -> None:
        """Initialize coupling service.

        Args:
            process_times: Process times configuration with coupling/decoupling times
        """
        self.process_times = process_times

    def get_rake_coupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate time to couple wagons into rake: (n-1) * coupling_time.

        Args:
            wagons: List of wagons to couple

        Returns
        -------
            Coupling time in simulation ticks
        """
        if len(wagons) <= 1:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value
        time_per_coupling = self.process_times.get_coupling_ticks(coupler_type)
        return (len(wagons) - 1) * time_per_coupling

    def get_rake_decoupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate time to decouple rake: (n-1) * decoupling_time.

        Args:
            wagons: List of wagons to decouple

        Returns
        -------
            Decoupling time in simulation ticks
        """
        if len(wagons) <= 1:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value
        time_per_decoupling = self.process_times.get_decoupling_ticks(coupler_type)
        return (len(wagons) - 1) * time_per_decoupling

    def get_loco_coupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate time to couple locomotive to rake.

        Based on first wagon's coupler type.

        Args:
            wagons: List of wagons in rake

        Returns
        -------
            Loco coupling time in simulation ticks
        """
        if not wagons:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value
        return self.process_times.get_coupling_ticks(coupler_type)

    def get_loco_decoupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate time to decouple locomotive from rake.

        Based on first wagon's coupler type.

        Args:
            wagons: List of wagons in rake

        Returns
        -------
            Loco decoupling time in simulation ticks
        """
        if not wagons:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value
        return self.process_times.get_decoupling_ticks(coupler_type)
