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

The following ADRs document performance optimizations made to the PopUpSim codebase:

| # | Title | Status | Impact |
|---|-------|--------|--------|
| 001 | Resource Pool Incremental Utilization Tracking | Accepted | 30-3000x speedup |
| 002 | Wagon Collector Memory Leak Fix and Simplification | Accepted | 5000x memory reduction |
| 003 | CSV Adapter Dict Grouping for Train Processing | Accepted | 10-16x speedup |
| 004 | Event Type Routing for Metrics Collection | Accepted | 1.7x speedup |
| 005 | Track Selection Cached Ratios Optimization | Accepted | 1.57x speedup (large) |
| 006 | Batch Collection Immediate Break Optimization | Accepted | 15% avg speedup |
| 007 | Lazy Logging String Formatting | Accepted | ~1% improvement |
| 008 | Track Length Caching | Accepted | Avoid recomputation |
| 009 | JSON Loading Strategy and Future Scalability | Accepted | Future planning |

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

### Phase 3: Polish (In Progress)

**Issue #8: Lazy Logging String Formatting**
- Problem: F-strings evaluated even when log level filters them out
- Solution: Use %-formatting for lazy evaluation
- Result: ~1% improvement when debug logging disabled

**Issue #9: Track Length Caching**
- Problem: Track total length recalculated if needed elsewhere
- Solution: Cache computed length in Track entity
- Result: Avoid recomputation, better encapsulation

### Phase 4: Future Considerations

**Issue #10: JSON Loading Strategy**
- Problem: Large JSON files loaded entirely into memory
- Decision: Keep current for post-MVP (<50MB files)
- Future: Streaming, file splitting, database, or distributed architecture

### Combined Impact

For a typical large scenario (20 resources, 10 trains, 500 wagons, 10,000 events):
- **Resource Pool:** 12.04 ms → 3.85 μs (3,128x faster)
- **Wagon Collector:** 50 MB leak → 10 KB stable (5,000x reduction)
- **CSV Loading:** 25.35 ms → 2.37 ms (10.7x faster)

**Total improvement:** Simulation initialization and metrics calculation are now **orders of magnitude faster** with **minimal memory footprint**.
