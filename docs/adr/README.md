# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records for the PopUpSim project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:
- **Status:** Proposed | Accepted | Deprecated | Superseded
- **Date:** When the decision was made
- **Context:** What is the issue we're seeing that is motivating this decision
- **Decision:** What is the change that we're proposing/doing
- **Consequences:** What becomes easier or more difficult to do because of this change

## Performance Optimizations Summary

The PopUpSim project has undergone significant performance optimizations:

### Critical Fixes

**Resource Pool Utilization**
- Problem: O(n*m) quadratic complexity
- Solution: Incremental tracking with O(1) updates
- Result: 3,128x speedup for large scenarios

**Wagon Collector Memory Management**
- Problem: Unbounded dictionary growth (50MB leak)
- Solution: Cleanup on exit + design simplification
- Result: 5,000x memory reduction

**CSV Adapter Performance**
- Problem: O(n*m) pandas iterrows() with nested filtering
- Solution: Pure Python dict grouping O(n+m)
- Result: 10.7x speedup for large scenarios

### High Priority Optimizations

**Event Broadcasting**
- Problem: Broadcasting all events to all collectors
- Solution: Event type registration and routing
- Result: 1.7x speedup, 67% fewer method calls

**Track Selection Lookups**
- Problem: 4 dictionary lookups per track in LEAST_OCCUPIED strategy
- Solution: Cache occupancy ratios during filtering
- Result: 1.57x speedup for large scenarios (20+ tracks)

**Batch Collection Timeouts**
- Problem: Timeout events created when collecting wagon batches
- Solution: Immediate break when queue empty (no timeout)
- Result: 15% average speedup, simpler code

### Combined Impact

For a typical large scenario (20 resources, 10 trains, 500 wagons, 10,000 events):
- **Resource Pool:** 12.04 ms → 3.85 μs (3,128x faster)
- **Wagon Collector:** 50 MB leak → 10 KB stable (5,000x reduction)
- **CSV Loading:** 25.35 ms → 2.37 ms (10.7x faster)

**Total improvement:** Simulation initialization and metrics calculation are now **orders of magnitude faster** with **minimal memory footprint**.

## Note

Detailed ADR documents are maintained separately. This summary provides an overview of key architectural decisions and their impact on performance.
