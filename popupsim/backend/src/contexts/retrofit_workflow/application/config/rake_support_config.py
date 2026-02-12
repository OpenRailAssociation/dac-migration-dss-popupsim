"""Rake Support Configuration for Phase 4 Integration."""

from dataclasses import dataclass


@dataclass
class RakeSupportConfig:
    """Configuration for rake support integration."""

    enabled: bool = True
    """Whether to enable rake-first approach."""

    use_enhanced_timing: bool = True
    """Whether to use enhanced timing calculations."""

    separate_transport_processing: bool = True
    """Whether to separate rake transport from batch processing."""

    log_rake_operations: bool = True
    """Whether to log detailed rake operations."""

    validate_coupling_constraints: bool = True
    """Whether to validate physical coupling constraints."""

    @classmethod
    def create_default(cls) -> 'RakeSupportConfig':
        """Create default rake support configuration."""
        return cls(
            enabled=True,
            use_enhanced_timing=True,
            separate_transport_processing=True,
            log_rake_operations=True,
            validate_coupling_constraints=True,
        )

    @classmethod
    def create_disabled(cls) -> 'RakeSupportConfig':
        """Create configuration with rake support disabled."""
        return cls(
            enabled=False,
            use_enhanced_timing=False,
            separate_transport_processing=False,
            log_rake_operations=False,
            validate_coupling_constraints=False,
        )

    def get_coordinator_type(self) -> str:
        """Get coordinator type based on configuration."""
        return 'RAKE_FIRST' if self.enabled else 'ORIGINAL'

    def should_use_rake_transport(self) -> bool:
        """Check if rake transport should be used."""
        return self.enabled and self.separate_transport_processing

    def should_log_operations(self) -> bool:
        """Check if operations should be logged."""
        return self.enabled and self.log_rake_operations
