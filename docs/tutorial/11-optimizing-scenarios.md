# Optimizing Scenarios

Besides running a single simulation, PopUpSim can automatically search for better
**task-priority** settings using the `optimize` command. This is useful when you want the
tool to suggest transport priorities rather than tuning them by hand.

## What gets optimized

The optimizer only tunes the **task priorities** for the four transport tasks in a scenario:

- `collection_to_retrofit`
- `retrofit_to_workshop`
- `workshop_to_retrofitted`
- `retrofitted_to_parking`

For each task it explores a small, discrete search space (base priority, optional
hold conditions/thresholds, and priority rules). All other configuration
(topology, tracks, workshops, locomotives, routes, train schedule) stays fixed — the
optimizer reads them from your scenario directory unchanged.

> **Tip:** Scenarios that already contain a `task_priorities` section (for example
> `Data/examples/ten_trains_two_days_priority_dispatch/` or `ten_trains_two_days_var1/`)
> are the most useful starting points.

## How it works

The search runs in two phases and never simulates the same configuration twice
(every evaluated configuration is cached by a canonical key):

1. **Phase 1 - Random search.** Draws up to `--n-random` unique random configurations from
   the search space and evaluates them in parallel.
2. **Phase 2 - Coordinate descent.** Starts from the top `--k-starts` configurations and
   repeatedly varies one task's priority at a time (for up to `--max-rounds` rounds),
   keeping any change that improves the score.

### Scoring

Each configuration is scored from two simulation metrics:

```
score = weight_completion * completion_rate_pct + weight_loco * loco_utilization_pct
```

By default `--weight-completion` is `0.9` and `--weight-loco` is `-0.1`, so the search
favors high wagon completion while lightly penalizing locomotive over-utilization. Adjust
these weights to change what "better" means for your study.

## Command

```bash
cd dac-migration-dss-popupsim

uv run python popupsim/backend/src/main.py optimize \
  --scenario Data/examples/ten_trains_two_days_var1/ \
  --results-json output/optimization_results.json
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--scenario` | (required) | Path to the scenario directory (containing `scenario.json`) |
| `--seed` | `42` | Random seed for reproducible sampling |
| `--n-random` | `500` | Number of random configurations to sample in Phase 1 |
| `--n-workers` | `10` | Number of parallel worker processes |
| `--k-starts` | `5` | Number of top configurations used to start Phase 2 descent |
| `--max-rounds` | `5` | Maximum rounds of coordinate descent per start |
| `--weight-completion` | `0.9` | Weight for completion rate in the score |
| `--weight-loco` | `-0.1` | Weight for locomotive utilization in the score |
| `--results-json` | `optimization_results.json` | Where to write the ranked results |

> **Note:** Optimization runs many simulations in parallel, so it is considerably more
> expensive than a single `run`. Start with a smaller `--n-random` (for example `50`) to get
> a feel for the runtime on your machine before scaling up.

## Results

The command prints the top configurations to the console and writes all evaluated
configurations to the `--results-json` file, sorted by descending score. Each entry contains:

- `parameters` - the task-priority settings for that configuration
- `completion` - wagon completion rate (%)
- `loco_utilization` - locomotive utilization (%)
- `score` - the combined score used for ranking

To use a suggested configuration, copy its `task_priorities` block into your scenario's
`scenario.json` and re-run a normal simulation with the `run` command
(see [Chapter 10](10-running-simulation.md)) to inspect the full results in the dashboard.

## Next Steps

- Review [Chapter 10: Running Your Simulation](10-running-simulation.md) to analyze a chosen
  configuration in detail.
- See the architecture docs for how the optimizer relates to the rest of the system.
