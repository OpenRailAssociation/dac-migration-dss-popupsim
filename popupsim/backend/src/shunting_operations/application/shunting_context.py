"""Shunting Operations Context - Main entry point for shunting operations."""

from shunting_operations.application.shunting_locomotive_service import ShuntingLocomotiveService
from shunting_operations.application.shunting_service import DefaultShuntingService
from shunting_operations.application.shunting_service import ShuntingService
from workshop_operations.application.services.locomotive_service import LocomotiveService


class ShuntingOperationsContext:
    """Main context for shunting operations.

    Provides services for yard shunting locomotives (as opposed to transport locomotives
    that move between yards).
    """

    def __init__(self, shunting_service: ShuntingService | None = None):
        self.shunting_service = shunting_service or DefaultShuntingService()
        self._locomotive_service = ShuntingLocomotiveService(self.shunting_service)

    def get_shunting_locomotive_service(self) -> LocomotiveService:
        """Get service for yard shunting locomotives.

        These locomotives handle coupling, decoupling, and moving wagons within the workshop yard.
        """
        return self._locomotive_service

    def get_shunting_service(self) -> ShuntingService:
        """Get the native shunting service for advanced operations."""
        return self.shunting_service
