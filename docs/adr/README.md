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

## Index

### Performance Optimizations

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| [001](001-resource-pool-incremental-utilization.md) | Resource Pool Incremental Utilization Tracking | Accepted | 2024 | 30-3000x speedup |
| [002](002-wagon-collector-memory-leak-fix.md) | Wagon Collector Memory Leak Fix and Simplification | Accepted | 2024 | 5000x memory reduction |
| [003](003-csv-adapter-dict-grouping.md) | CSV Adapter Dict Grouping for Train Processing | Accepted | 2024 | 10-16x speedup |
| [004](004-event-type-routing.md) | Event Type Routing for Metrics Collection | Accepted | 2024 | 1.7x speedup |
| [005](005-track-selection-cached-ratios.md) | Track Selection Cached Ratios Optimization | Accepted | 2024 | 1.57x speedup (large) |
| [006](006-batch-collection-immediate-break.md) | Batch Collection Immediate Break Optimization | Accepted | 2024 | 15% avg speedup |
| [007](007-lazy-logging-string-formatting.md) | Lazy Logging String Formatting | Accepted | 2024 | ~1% improvement |
| [008](008-track-length-caching.md) | Track Length Caching | Accepted | 2024 | Avoid recomputation |
| [009](009-json-loading-strategy.md) | JSON Loading Strategy and Future Scalability | Accepted | 2024 | Future planning |

## Summary of Performance Improvements

### Phase 1: Critical Fixes (Completed)

**Issue #1: Resource Pool Utilization**
- Problem: O(n*m) quadratic complexity
- Solution: Incremental tracking with O(1) updates
- Result: 3,128x speedup for large scenarios
- ADR: [001](001-resource-pool-incremental-utilization.md)

**Issue #2: Wagon Collector Memory Leak**
- Problem: Unbounded dictionary growth (50MB leak)
- Solution: Cleanup on exit + design simplification
- Result: 5,000x memory reduction
- ADR: [002](002-wagon-collector-memory-leak-fix.md)

**Issue #3: CSV Adapter Performance**
- Problem: O(n*m) pandas iterrows() with nested filtering
- Solution: Pure Python dict grouping O(n+m)
- Result: 10.7x speedup for large scenarios
- ADR: [003](003-csv-adapter-dict-grouping.md)

### Phase 2: High Priority Optimizations (In Progress)

**Issue #4: Event Broadcasting**
- Problem: Broadcasting all events to all collectors
- Solution: Event type registration and routing
- Result: 1.7x speedup, 67% fewer method calls
- ADR: [004](004-event-type-routing.md)

**Issue #5: Track Selection Lookups**
- Problem: 4 dictionary lookups per track in LEAST_OCCUPIED strategy
- Solution: Cache occupancy ratios during filtering
- Result: 1.57x speedup for large scenarios (20+ tracks)
- ADR: [005](005-track-selection-cached-ratios.md)

**Issue #7: Batch Collection Timeouts**
- Problem: Timeout events created when collecting wagon batches
- Solution: Immediate break when queue empty (no timeout)
- Result: 15% average speedup, simpler code
- ADR: [006](006-batch-collection-immediate-break.md)

### Phase 3: Polish (In Progress)

**Issue #8: Lazy Logging String Formatting**
- Problem: F-strings evaluated even when log level filters them out
- Solution: Use %-formatting for lazy evaluation
- Result: ~1% improvement when debug logging disabled
- ADR: [007](007-lazy-logging-string-formatting.md)

**Issue #9: Track Length Caching**
- Problem: Track total length recalculated if needed elsewhere
- Solution: Cache computed length in Track entity
- Result: Avoid recomputation, better encapsulation
- ADR: [008](008-track-length-caching.md)

### Phase 4: Future Considerations

**Issue #10: JSON Loading Strategy**
- Problem: Large JSON files loaded entirely into memory
- Decision: Keep current for post-MVP (<50MB files)
- Future: Streaming, file splitting, database, or distributed architecture
- ADR: [009](009-json-loading-strategy.md)

### Combined Impact

For a typical large scenario (20 resources, 10 trains, 500 wagons, 10,000 events):
- **Resource Pool:** 12.04 ms → 3.85 μs (3,128x faster)
- **Wagon Collector:** 50 MB leak → 10 KB stable (5,000x reduction)
- **CSV Loading:** 25.35 ms → 2.37 ms (10.7x faster)

**Total improvement:** Simulation initialization and metrics calculation are now **orders of magnitude faster** with **minimal memory footprint**.

## References

- [Performance Analysis](../performance/PERFORMANCE_ANALYSIS.md)
- [Benchmark Results](../performance/)
- [Test Suite](../../popupsim/backend/tests/unit/performance/)
