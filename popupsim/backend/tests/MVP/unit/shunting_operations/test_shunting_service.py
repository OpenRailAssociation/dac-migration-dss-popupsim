"""Unit tests for shunting service."""

from popupsim.backend.src.MVP.shunting_operations.application.shunting_service import (
    DefaultShuntingService,
    ShuntingService,
)


def test_shunting_service_interface() -> None:
    """Test that ShuntingService is properly defined as interface."""
    # Verify interface methods exist
    assert hasattr(ShuntingService, "allocate_shunting_locomotive")
    assert hasattr(ShuntingService, "release_shunting_locomotive")
    assert hasattr(ShuntingService, "execute_shunting_move")
    assert hasattr(ShuntingService, "execute_coupling")
    assert hasattr(ShuntingService, "execute_decoupling")


def test_default_shunting_service_initialization() -> None:
    """Test DefaultShuntingService initialization."""
    service = DefaultShuntingService()
    assert isinstance(service, DefaultShuntingService)


def test_allocate_locomotive_method_exists() -> None:
    """Test that allocate_shunting_locomotive method exists."""
    service = DefaultShuntingService()
    assert hasattr(service, "allocate_shunting_locomotive")
    assert callable(service.allocate_shunting_locomotive)


def test_release_locomotive_method_exists() -> None:
    """Test that release_shunting_locomotive method exists."""
    service = DefaultShuntingService()
    assert hasattr(service, "release_shunting_locomotive")
    assert callable(service.release_shunting_locomotive)
