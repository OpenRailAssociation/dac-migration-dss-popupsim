"""Policy loader for external configuration files."""

import json
from pathlib import Path

import yaml

from contexts.configuration.domain.policy_config import (
    PolicyConfiguration,
)
from shared.validation.base import ValidationResult


class PolicyLoader:
    """Load and validate policy configurations from external files."""

    def load_from_file(
        self, file_path: str | Path
    ) -> tuple[PolicyConfiguration | None, ValidationResult]:
        """Load policy configuration from YAML/JSON file."""
        try:
            path = Path(file_path)

            if not path.exists():
                return None, ValidationResult(
                    is_valid=False, issues=[f"Policy file not found: {path}"]
                )

            # Load configuration data
            with open(path, encoding="utf-8") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    config_data = yaml.safe_load(f)
                elif path.suffix.lower() == ".json":
                    config_data = json.load(f)
                else:
                    return None, ValidationResult(
                        is_valid=False,
                        issues=[f"Unsupported file format: {path.suffix}"],
                    )

            # Extract policies section
            policies_data = config_data.get("policies", config_data)

            # Create policy configuration
            policy_config = PolicyConfiguration.model_validate(policies_data)

            return policy_config, ValidationResult(is_valid=True, issues=[])

        except yaml.YAMLError as e:
            return None, ValidationResult(
                is_valid=False, issues=[f"YAML parsing error: {e}"]
            )
        except json.JSONDecodeError as e:
            return None, ValidationResult(
                is_valid=False, issues=[f"JSON parsing error: {e}"]
            )
        except (OSError, ValueError, KeyError, TypeError) as e:
            return None, ValidationResult(
                is_valid=False, issues=[f"Policy loading error: {e}"]
            )

    def create_default_config(self) -> PolicyConfiguration:
        """Create default policy configuration."""
        return PolicyConfiguration()

    def save_to_file(
        self, policy_config: PolicyConfiguration, file_path: str | Path
    ) -> ValidationResult:
        """Save policy configuration to YAML file."""
        try:
            path = Path(file_path)

            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict and wrap in policies section
            config_data = {"policies": policy_config.model_dump()}

            # Save as YAML
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            return ValidationResult(is_valid=True, issues=[])

        except (OSError, ValueError) as e:
            return ValidationResult(
                is_valid=False, issues=[f"Policy saving error: {e}"]
            )
