"""Dependency injection container for SOLID principles compliance."""

from collections.abc import Callable
from typing import Any
from typing import TypeVar

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}

    def register_singleton(self, interface: type[T], implementation: T) -> None:
        """Register a singleton instance."""
        self._singletons[interface] = implementation

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function."""
        self._factories[interface] = factory

    def register_transient(self, interface: type[T], implementation_type: type[T]) -> None:
        """Register a transient service."""
        self._services[interface] = implementation_type

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service instance."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check factories
        if interface in self._factories:
            return self._factories[interface]()

        # Check transient services
        if interface in self._services:
            implementation_type = self._services[interface]
            return implementation_type()

        raise ValueError(f'Service {interface} not registered')

    def create_child_container(self) -> 'DIContainer':
        """Create a child container that inherits registrations."""
        child = DIContainer()
        # pylint: disable=protected-access  # Accessing own protected members
        child._services = self._services.copy()
        child._factories = self._factories.copy()
        child._singletons = self._singletons.copy()
        return child
