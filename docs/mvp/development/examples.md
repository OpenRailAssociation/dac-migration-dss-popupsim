# MVP Examples (Synthetic)

## Overview

This document provides concrete examples for MVP implementation. All values are **synthetic** for development purposes.

**Note:** Actual performance will be measured during MVP implementation.

---

## Workshop Configurations

### Small Workshop

**Configuration:**
- **Tracks:** 2 werkstattgleis
- **Capacity per track:** 3 wagons
- **Retrofit time:** 30 minutes per wagon
- **Operating hours:** 24/7

**Expected Performance (Synthetic):**
- **Throughput:** ~48 wagons/day
- **Utilization:** ~75%
- **Average waiting time:** TODO
- **Peak queue length:** TODO

**Use Case:** Small Pop-Up site, limited space

---

### Medium Workshop

**Configuration:**
- **Tracks:** 4 werkstattgleis
- **Capacity per track:** 4 wagons
- **Retrofit time:** 30 minutes per wagon
- **Operating hours:** 24/7

**Expected Performance (Synthetic):**
- **Throughput:** ~96 wagons/day
- **Utilization:** ~80%
- **Average waiting time:** TODO
- **Peak queue length:** TODO

**Use Case:** Standard Pop-Up site

---

### Large Workshop

**Configuration:**
- **Tracks:** 6 werkstattgleis
- **Capacity per track:** 4 wagons
- **Retrofit time:** 30 minutes per wagon
- **Operating hours:** 24/7

**Expected Performance (Synthetic):**
- **Throughput:** ~144 wagons/day
- **Utilization:** ~85%
- **Average waiting time:** TODO
- **Peak queue length:** TODO

**Use Case:** Large Pop-Up site, high volume

---

## Train Schedules

### Light Schedule

**Configuration:**
- **Trains per day:** 4
- **Wagons per train:** 10
- **Total wagons:** 40/day
- **Arrival pattern:** Evenly distributed

**Suitable for:** Small workshop testing

---

### Medium Schedule

**Configuration:**
- **Trains per day:** 8
- **Wagons per train:** 12
- **Total wagons:** 96/day
- **Arrival pattern:** Peak hours (morning/evening)

**Suitable for:** Medium workshop testing

---

### Heavy Schedule

**Configuration:**
- **Trains per day:** 12
- **Wagons per train:** 15
- **Total wagons:** 180/day
- **Arrival pattern:** Continuous with peaks

**Suitable for:** Large workshop stress testing

---

## Scenario Examples

### Scenario 1: Baseline Test

**Purpose:** Verify basic simulation functionality

**Configuration:**
```json
{
  "scenario_id": "baseline_test",
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "function": "werkstattgleis",
        "capacity": 3,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK02",
        "function": "werkstattgleis",
        "capacity": 3,
        "retrofit_time_min": 30
      }
    ]
  },
  "train_schedule_file": "light_schedule.csv"
}
```

**Expected Result:** All wagons processed, no queue buildup

---

### Scenario 2: Capacity Test

**Purpose:** Test workshop at 90% capacity

**Configuration:**
```json
{
  "scenario_id": "capacity_test",
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "function": "werkstattgleis",
        "capacity": 4,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK02",
        "function": "werkstattgleis",
        "capacity": 4,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK03",
        "function": "werkstattgleis",
        "capacity": 4,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK04",
        "function": "werkstattgleis",
        "capacity": 4,
        "retrofit_time_min": 30
      }
    ]
  },
  "train_schedule_file": "medium_schedule.csv"
}
```

**Expected Result:** High utilization, minimal waiting

---

### Scenario 3: Overload Test

**Purpose:** Test workshop beyond capacity

**Configuration:**
```json
{
  "scenario_id": "overload_test",
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "function": "werkstattgleis",
        "capacity": 3,
        "retrofit_time_min": 30
      },
      {
        "id": "TRACK02",
        "function": "werkstattgleis",
        "capacity": 3,
        "retrofit_time_min": 30
      }
    ]
  },
  "train_schedule_file": "heavy_schedule.csv"
}
```

**Expected Result:** Queue buildup, increased waiting times

---

## KPI Examples (Synthetic)

### Throughput Calculation

**Formula:** `wagons_processed / simulation_hours`

**Example:**
- Wagons processed: 96
- Simulation duration: 24 hours
- Throughput: 96 / 24 = 4 wagons/hour

---

### Utilization Calculation

**Formula:** `busy_time / total_time * 100`

**Example:**
- Track busy time: 19.2 hours
- Total time: 24 hours
- Utilization: 19.2 / 24 * 100 = 80%

---

### Waiting Time Calculation

**Formula:** `sum(waiting_times) / wagon_count`

**Example:**
- Total waiting time: 240 minutes
- Wagons: 96
- Average waiting: 240 / 96 = 2.5 minutes

---

## Performance Benchmarks (Synthetic)

### Small Scenario (100 wagons)

**Expected Performance:**
- **Execution time:** < 5 seconds
- **Memory usage:** < 100 MB
- **CPU usage:** Single-threaded

---

### Medium Scenario (1000 wagons)

**Expected Performance:**
- **Execution time:** < 30 seconds
- **Memory usage:** < 500 MB
- **CPU usage:** Single-threaded

---

### Large Scenario (5000 wagons)

**Expected Performance:**
- **Execution time:** To be measured
- **Memory usage:** To be measured
- **CPU usage:** Single-threaded

---

## Error Scenarios

### Example 1: Invalid Configuration

**Input:**
```json
{
  "scenario_id": "invalid",
  "start_date": "2025-01-02",
  "end_date": "2025-01-01",
  "workshop": {
    "tracks": []
  }
}
```

**Expected Error:**
```
ValidationError: 2 validation errors
- end_date must be after start_date
- workshop must have at least one track
```

---

### Example 2: Missing Required Track

**Input:**
```json
{
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "function": "sammelgleis",
        "capacity": 5,
        "retrofit_time_min": 0
      }
    ]
  }
}
```

**Expected Error:**
```
ValidationError: Workshop must have at least one werkstattgleis track
```

---

## Test Data Files

### Example: light_schedule.csv

```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-01-01,08:00,W001,15.5,true,true
TRAIN001,2025-01-01,08:00,W002,15.5,false,true
TRAIN002,2025-01-01,14:00,W003,18.0,true,true
TRAIN002,2025-01-01,14:00,W004,18.0,false,true
```

### Example: medium_schedule.csv

```csv
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-01-01,06:00,W001,15.5,true,true
TRAIN001,2025-01-01,06:00,W002,15.5,true,true
TRAIN001,2025-01-01,06:00,W003,15.5,false,true
TRAIN002,2025-01-01,09:00,W004,18.0,true,true
TRAIN002,2025-01-01,09:00,W005,18.0,true,true
TRAIN002,2025-01-01,09:00,W006,18.0,false,true
```

---

