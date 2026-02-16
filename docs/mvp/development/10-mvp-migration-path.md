# 10. MVP Migration Path

## Overview

Path from MVP (4 contexts, desktop) to full version (web-based, distributed).

## Current MVP Architecture

```
4 Bounded Contexts:
├── Configuration (file loading)
├── Retrofit Workflow (simulation)
├── Railway Infrastructure (track management)
└── External Trains (arrivals)

Integration: Direct calls + Event bus
Storage: File-based (JSON/CSV)
UI: CLI + Matplotlib
Deployment: Desktop
```

## Full Version Target

```
Multiple Contexts (TBD):
├── Configuration
├── Simulation Engine
├── Railway Infrastructure
├── Train Operations
├── Workshop Management
├── Resource Management
└── Analytics

Integration: Event-driven (async messaging)
Storage: Database + Event Store
UI: Web interface (interactive)
Deployment: Cloud-ready
```

## Migration Phases

### Phase 1: Event-Driven Architecture

**Current:** Direct method calls + simple event bus

**Target:** Full event-driven with async messaging

**Changes:**
- Replace direct calls with domain events
- Add event store for persistence
- Implement saga pattern for workflows

**Effort:** 2-3 weeks

### Phase 2: Database Integration

**Current:** File-based configuration

**Target:** Database storage with repository pattern

**Changes:**
- Add repository interfaces
- Implement database repositories
- Migrate file loading to database queries

**Effort:** 1-2 weeks

### Phase 3: Web Interface

**Current:** CLI + Matplotlib charts

**Target:** Web UI with interactive visualization

**Changes:**
- Add REST API layer
- Implement web frontend
- Real-time simulation updates

**Effort:** 4-6 weeks

### Phase 4: Context Refinement

**Current:** 4 contexts

**Target:** More specialized contexts

**Changes:**
- Split Retrofit Workflow into smaller contexts
- Add new contexts as needed
- Refine boundaries based on learnings

**Effort:** 2-3 weeks

## Technical Debt to Address

### High Priority

1. **SimPy Abstraction**
   - Current: Direct SimPy usage in coordinators
   - Target: Full abstraction layer
   - Effort: 3 days

2. **Service Interfaces**
   - Current: Concrete implementations
   - Target: Interface-based design
   - Effort: 5 days

### Medium Priority

3. **Repository Pattern**
   - Current: Direct file access
   - Target: Repository interfaces
   - Effort: 3 days

4. **Error Handling**
   - Current: Basic exception handling
   - Target: Comprehensive error strategy
   - Effort: 2 days

## Compatibility Strategy

### Backward Compatibility

- Keep file-based configuration support
- Maintain CLI interface alongside web UI
- Support both local and cloud deployment

### Data Migration

- Provide migration scripts for file → database
- Support hybrid mode during transition
- Maintain data format compatibility

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking changes | Maintain MVP as stable branch |
| Performance degradation | Benchmark before/after |
| Complexity increase | Incremental migration |
| Team learning curve | Training and documentation |

---
