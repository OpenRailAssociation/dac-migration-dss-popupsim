# GitHub Actions Workflows

This directory contains the CI/CD workflows for PopUp-Sim.

## Workflows

### `python-backend.yaml`
Comprehensive quality assurance pipeline for Python backend code.

**Triggers:**
- Pull requests to `main` branch
- Pushes to `main` branch
- Path filters: `backend/**`, workflow files, composite actions, `pyproject.toml`, `uv.lock`

**Jobs:**
1. **Code Formatting** - Ruff formatter validation
2. **Ruff Linting** - Fast linting with complexity metrics
3. **Pylint Analysis** - Comprehensive code quality analysis
4. **MyPy Type Checking** - Static type analysis
5. **Security Scan** - Vulnerability scanning with Syft + Grype
6. **Tests & Coverage** - Automated testing with coverage reporting

**Execution Time:** ~2 minutes (parallel execution)

### `scorecard.yml`
Repository-wide security posture assessment using OpenSSF Scorecard.

**Triggers:**
- Weekly schedule (Sundays at 2 AM UTC)
- Pushes to `main` branch
- Manual trigger (`workflow_dispatch`)

**Jobs:**
1. **Analysis** - OpenSSF security best practices evaluation

**Execution Time:** ~1 minute
**Scope:** Entire repository (branch protection, security policies, etc.)

## Composite Actions

### `.github/actions/`
Reusable setup actions for Python environments:

- **`setup-python-dev/action.yml`** - Development environment with all dependencies
- **`setup-python-prod/action.yml`** - Production environment (dependencies only)

## Problem Matchers

### `.github/problem-matchers/`
Custom problem matchers for enhanced GitHub integration:

- **`mypy.json`** - MyPy error pattern matching for annotations

## Documentation

For detailed pipeline documentation, see [`docs/ci-cd-pipeline.md`](../docs/ci-cd-pipeline.md).

## Quick Reference

### Running Locally
```bash
# Backend pipeline simulation
.\scripts\test-ci-locally.ps1

# Individual checks
uv run ruff format --check --diff .
uv run ruff check .
uv run pylint backend/src/
uv run mypy backend/src/
uv run pytest

# Pre-commit hooks (all checks)
uv run pre-commit run --all-files
```

### Adding New Rules
1. Update `pyproject.toml` configuration
2. Test locally
3. Commit and verify in PR

### Debugging Pipeline Issues
1. Check workflow summary
2. Review job annotations
3. Download artifacts for detailed reports
