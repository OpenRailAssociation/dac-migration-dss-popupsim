# Business Rules

## Overview

This document consolidates all business rules for the PopUpSim MVP. These rules must be validated during implementation.

**Status:** 📋 FOR REVIEW - Rules need validation by domain experts

---

## Track Capacity Rules

### Rule BR-TC-001: Track Capacity Limit
**Description:** TODO: Define maximum wagon capacity per track

**Validation:** TODO: How is capacity enforced?

**Exception:** TODO: Any exceptions?

---

### Rule BR-TC-002: Track Function Restrictions
**Description:** TODO: Define which operations are allowed per track function

**Validation:** TODO: How are restrictions enforced?

**Exception:** TODO: Any exceptions?

---

## Retrofit Time Rules

### Rule BR-RT-001: Retrofit Duration
**Description:** Retrofit takes approximately 30 minutes per wagon

**Validation:** TODO: Is this fixed or variable?

**Exception:** TODO: Different wagon types?

---

### Rule BR-RT-002: Werkstattgleis Retrofit Time
**Description:** Only werkstattgleis tracks have retrofit_time_min > 0

**Validation:** Enforced by Pydantic validation in WorkshopTrack model

**Exception:** None

---

## Workshop Validation Rules

### Rule BR-WV-001: Minimum Werkstattgleis
**Description:** Workshop must have at least one WERKSTATTGLEIS track

**Validation:** Enforced by Pydantic validation in Workshop model

**Exception:** None

---

### Rule BR-WV-002: Unique Track IDs
**Description:** All track IDs within a workshop must be unique

**Validation:** Enforced by Pydantic validation in Workshop model

**Exception:** None

---

### Rule BR-WV-003: Balanced Feeder/Exit Tracks
**Description:** If werkstattzufuehrung exists, werkstattabfuehrung must exist (and vice versa)

**Validation:** Enforced by Pydantic validation in Workshop model

**Exception:** None

---

## Train Processing Rules

### Rule BR-TP-001: Train Arrival Processing
**Description:** TODO: Define how trains are processed on arrival

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

### Rule BR-TP-002: Wagon Decoupling
**Description:** TODO: Define wagon decoupling rules

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

## Wagon Flow Rules

### Rule BR-WF-001: Wagon State Transitions
**Description:** TODO: Define valid state transitions for wagons

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

### Rule BR-WF-002: Track Allocation Priority
**Description:** TODO: Define priority rules for track allocation

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

## Capacity Management Rules

### Rule BR-CM-001: Workshop Overflow
**Description:** TODO: Define what happens when workshop is at capacity

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

### Rule BR-CM-002: Queue Management
**Description:** TODO: Define how waiting wagons are queued

**Validation:** TODO: How is this enforced?

**Exception:** TODO: Any exceptions?

---

## Simulation Rules

### Rule BR-SIM-001: Deterministic Behavior
**Description:** Same inputs must produce identical results

**Validation:** TODO: How is determinism ensured?

**Exception:** None

---

### Rule BR-SIM-002: Time Progression
**Description:** TODO: Define how simulation time progresses

**Validation:** TODO: SimPy discrete event scheduling

**Exception:** TODO: Any exceptions?

---

## Data Validation Rules

### Rule BR-DV-001: Date Range Validation
**Description:** end_date must be after start_date

**Validation:** Enforced by Pydantic validation in ScenarioConfig model

**Exception:** None

---

### Rule BR-DV-002: Scenario ID Format
**Description:** Scenario ID must match pattern ^[a-zA-Z0-9_-]+$ with length 1-50

**Validation:** Enforced by Pydantic validation in ScenarioConfig model

**Exception:** None

---

## Review Checklist

- [ ] All rules validated by domain experts
- [ ] All TODOs filled in
- [ ] Rules implemented in code
- [ ] Rules covered by tests
- [ ] Exceptions documented
- [ ] Cross-references to code added

---

