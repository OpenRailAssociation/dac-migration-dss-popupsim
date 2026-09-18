<!--
SPDX-FileCopyrightText: 2025 OpenRail Association AISBL

SPDX-License-Identifier: CC-BY-4.0
-->

# Contributing

This Project welcomes contributions, suggestions, and feedback. All contributions, suggestions, and feedback you submitted are accepted under the [Project's license](./LICENSE). You represent that if you do not own copyright in the code that you have the authority to submit it under the [Project's license](./LICENSE). All feedback, suggestions, or contributions are not confidential.

## Development Setup (Backend)

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Quick Start
```bash
git clone https://github.com/OpenRailAssociation/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim
uv sync --all-extras --dev
uv run pre-commit install
```

## Code Quality Requirements (Backend)

**Quick checklist:**
- **Formatting**: Ruff (120 chars, tabs, single quotes)
- **Linting**: Ruff + Pylint (score ≥8.0)
- **Type Checking**: MyPy strict mode
- **Testing**: 90% coverage minimum
- **Security**: No high/critical vulnerabilities

Run locally: `uv run pre-commit run --all-files`

## How to Contribute

1. **Fork & Branch**: Create feature branch from `main`
2. **Develop**: Follow code standards, add tests
3. **Test**: Ensure all CI checks pass locally
4. **PR**: Submit with clear description and link issues
5. **Review**: Address feedback from maintainers

### PR Requirements
- [ ] Tests added/updated with 90% coverage
- [ ] Documentation updated if needed
- [ ] CI pipeline passes

## Railway Simulation Guidelines

- **Units**: Use metric system (SI units: meters, kg, m/s)
- **Standards**: Follow UIC and ERA specifications
- **Terminology**: Use official DAC migration terminology

## Contribution workflow
1. Fork the repository.
2. Create a new branch for your feature or bug fix: git checkout -b feature-or-fix-name
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your forked repository: git push origin feature-or-fix-name
5. Open a Pull Request on the main repository.
It is assumed that you contribute under the main license of the project and own all the rights to the content you submit.
---
Based on [GitHub's Minimum Viable Governance (MVG)](https://github.com/github/MVG). Licensed under the [CC-BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).
