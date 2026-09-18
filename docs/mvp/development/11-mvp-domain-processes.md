# 11. MVP Domain Processes

## Overview

This document describes the main process flows in the Retrofit Workflow Context.

## Wagon Flow Process

```
Train Arrival
    ↓
Arrival Coordinator (classify wagons)
    ↓
Collection Coordinator (form batches)
    ↓
Workshop Coordinator (retrofit)
    ↓
Parking Coordinator (to parking)
    ↓
Complete
```

## Detailed Process Flows

### 1. Train Arrival Process

**Coordinator:** ArrivalCoordinator

**Steps:**
1. Receive TrainArrivedEvent from External Trains
2. Classify each wagon on intake — **the eligibility gate**: loaded wagons and wagons that don't need a retrofit (e.g. already-DAC) are rejected here (`REJECTED_LOADED` / `REJECTED_NO_RETROFIT_NEEDED`) and never become wagon entities
3. For eligible wagons, select a collection track (via the Railway Infrastructure track-selection service)
4. Place wagons on the collection track — if no track has room, the wagon is rejected on **capacity** (`NO_COLLECTION_TRACK` / `COLLECTION_TRACK_FULL`)
5. Hand placed wagons to the collection queue

> Note: the eligibility rejection (loaded / no-retrofit) happens at classification (step 2),
> *before* track placement. The only rejection at placement (step 4) is capacity (track-full).

**Domain Services Used:**
- Wagon eligibility / classification (`WagonEligibilityService`) — the accept/reject gate at arrival
- Track selection (`TrackSelectionService`)

### 2. Collection Process

**Coordinator:** CollectionCoordinator

**Steps:**
1. Wait for wagons in collection queue
2. Collect batch (up to batch_size)
3. Allocate locomotive
4. Form rake (couple wagons)
5. Form train (locomotive + rake)
6. Transport to retrofit track
7. Decouple wagons
8. Release locomotive

**Domain Services Used:**
- BatchFormationService
- RakeFormationService
- TrainFormationService
- RouteService

### 3. Workshop Process

**Coordinator:** WorkshopCoordinator

**Steps:**
1. Wait for batch on retrofit track
2. Select workshop with capacity
3. Allocate locomotive
4. Transport batch to workshop track
5. Decouple wagons sequentially
6. Assign each wagon to retrofit station
7. Execute retrofit (parallel)
8. Couple completed wagons
9. Transport to retrofitted track
10. Release locomotive

**Domain Services Used:**
- WorkshopSchedulingService
- CouplingService
- RouteService

### 4. Parking Process

**Coordinator:** ParkingCoordinator

**Steps:**
1. Wait for wagons on retrofitted track
2. Form batch
3. Allocate locomotive
4. Transport to parking track
5. Place wagons
6. Release locomotive

**Domain Services Used:**
- BatchFormationService
- RouteService

## State Machines

### Wagon State Machine

The `WagonStatus` enum (`contexts/retrofit_workflow/domain/entities/wagon.py`) defines the
states:

```
ARRIVED → CLASSIFIED → READY_FOR_RETROFIT → RETROFITTING → RETROFITTED → PARKED
```

Wagons that are loaded or do not need a retrofit are rejected during classification
(recorded as a `REJECTED` event in the wagon journey).

## Timing

Timing parameters are defined in `ProcessTimes`
(`contexts/configuration/domain/models/process_times.py`):

- `wagon_retrofit_time`
- `screw_coupling_time` / `screw_decoupling_time`
- `dac_coupling_time` / `dac_decoupling_time`
- `train_to_hump_delay`, `wagon_hump_interval`

## Resource Constraints

- **Locomotives:** Limited pool, allocated on demand
- **Tracks:** Capacity based on length and fill factor
- **Workshops:** Limited retrofit stations

## Error Handling

- **Insufficient capacity:** Wagon waits in queue
- **No locomotive available:** Process blocks until available
- **Invalid route:** Simulation error

---
