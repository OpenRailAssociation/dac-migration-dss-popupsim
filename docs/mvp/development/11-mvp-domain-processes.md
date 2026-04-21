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
2. Classify wagons (needs retrofit vs. doesn't need)
3. Select collection track using TrackSelector
4. Place wagons on collection track
5. Add wagons to collection queue

**Domain Services Used:**
- WagonSelector (classify)
- WagonStateManager (update status)

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

```
ARRIVING → SELECTING → SELECTED → MOVING → 
ON_COLLECTION_TRACK → MOVING → ON_RETROFIT_TRACK → 
MOVING → RETROFITTING → RETROFITTED → MOVING → 
ON_RETROFITTED_TRACK → MOVING → PARKING
```

### Locomotive State Machine

```
AVAILABLE → ALLOCATED → IN_USE → RETURNING → AVAILABLE
```

## Timing

All timing parameters defined in ProcessTimes:
- coupling_time
- decoupling_time
- retrofit_time_per_wagon
- train_preparation_time

## Resource Constraints

- **Locomotives:** Limited pool, allocated on demand
- **Tracks:** Capacity based on length and fill factor
- **Workshops:** Limited retrofit stations

## Error Handling

- **Insufficient capacity:** Wagon waits in queue
- **No locomotive available:** Process blocks until available
- **Invalid route:** Simulation error

---
