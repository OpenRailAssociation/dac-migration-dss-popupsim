# PopUpSim Configuration Tutorial

This tutorial guides you through installing and configuring PopUpSim using the `ten_trains_two_days` example scenario. You'll learn about each configuration file, available parameters, and how they affect the simulation.

## Tutorial Contents

0. [Installation Guide](00-installation.md) - Installing Python, uv, and PopUpSim (including non-admin scenarios)
1. [Overview](01-overview.md) - Understanding the scenario structure
2. [Scenario Configuration](02-scenario-configuration.md) - Main scenario settings and references
3. [Topology Configuration](03-topology-configuration.md) - Network nodes and edges
4. [Track Configuration](04-track-configuration.md) - Track types and properties
5. [Workshop Configuration](05-workshop-configuration.md) - Workshop setup and capacity
6. [Process Times Configuration](06-process-times-configuration.md) - Operation durations
7. [Locomotive Configuration](07-locomotive-configuration.md) - Shunting resources
8. [Routes Configuration](08-routes-configuration.md) - Movement paths between tracks
9. [Train Schedule Configuration](09-train-schedule-configuration.md) - Wagon arrivals and properties
10. [Running Your Simulation](10-running-simulation.md) - Executing and analyzing results

## Quick Start

**First time user?** Start with the [Installation Guide](00-installation.md) to set up Python, uv, and PopUpSim.

To run the example scenario used in this tutorial:

```bash
cd dac-migration-dss-popupsim
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days/ --output output/tutorial/
```

## Scenario Overview

The `ten_trains_two_days` scenario simulates:
- **10 trains** arriving over 2 days
- **224 wagons** requiring DAC retrofit
- **2 workshops** with 2 retrofit stations each
- **15 parking tracks** for wagon storage
- **2 collection tracks** for incoming trains
- **1 shunting locomotive** for wagon movements

This medium-complexity scenario demonstrates realistic workshop operations and helps you understand how to configure your own scenarios.

## Learning Path

If you're new to PopUpSim:
1. Start with [Installation Guide](00-installation.md) to set up your environment
2. Continue with [Overview](01-overview.md) to understand the file structure
3. Follow the chapters in order to learn each configuration aspect
4. Experiment by modifying values in the example files
5. Run simulations to see how changes affect results

If you're experienced:
- Jump to specific chapters for reference
- Use the [Parameter Reference](parameter-reference.md) for quick lookups (if available)
- Check [Common Patterns](common-patterns.md) for best practices (if available)

## Next Steps

Begin with [Chapter 0: Installation Guide](00-installation.md) if you haven't installed PopUpSim yet, or jump to [Chapter 1: Overview](01-overview.md) to understand the scenario structure and file organization.
