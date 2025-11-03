# Medium Scenario 251027

> 📖 **Main Documentation:** [PopUp-Sim Backend README](../../../popupsim/backend/README.md)

This directory contains a medium-scale simulation scenario for PopUp-Sim, designed for realistic testing of DAC migration operations.

## Scenario Overview

- **Scenario ID:** `medium_251027`
- **Duration:** July 1 - October 11, 2031 (~3 months)
- **Trains:** Multiple trains with ~1000 wagons total
- **Locations:** XYZ workshop, ABC_D marshalling yard, Werk RT, mainline
- **Purpose:** Realistic DAC migration scenario with complex shunting, workshop processing, and marshalling yard operations

## Required Files

### 1. `test_train_schedule_medium_2025_10_23.csv` (Train Schedule)
Specifies arrival times and wagon composition:
- **Total Wagons:** ~1000 wagons
- **Delimiter:** Semicolon (`;`)

#### Table
| Column | Description |
|--------|-------------|
| train_id | Train identifier |
| wagon_id | Wagon identifier |
| length | Wagon length in meters |
| selector | Location selector code |
| arrival_time | Arrival timestamp (YYYY-MM-DD HH:MM:SS) |
| is_loaded | Whether wagon is loaded (true/false) |
| needs_retrofit | Whether wagon needs DAC retrofit (true/false) |

#### Format
```csv
train_id;wagon_id;length;selector;arrival_time;length;is_loaded;needs_retrofit
;1078;14.27;ABC_D;2031-07-04 15:45:00;14.27;true;false
```

### 2. `track_list_medium_251027.csv` (Track Configuration)
Defines track layout across multiple locations:
- **Locations:**
  - **XYZ:** Workshop tracks (2), retrofit tracks (2), parking tracks (9), station heads, circulating track
  - **ABC_D:** Collection track, dispenser tracks (B1-B11), hump selector, control tracks
  - **Werk RT:** Workshop parking tracks (7) plus main track
  - **1234:** Mainline track
- **Delimiter:** Semicolon (`;`)

#### Table
| Column | Description |
|--------|-------------|
| id | Track identifier |
| location_code | Location code |
| name | Track name |
| lenth | Track length in meters |
| type | Track type (workshop, parking, station_head_1, etc.) |
| sh_1 | Station head 1 connection |
| sh_1_id | Station head 1 ID |
| sh_n | Station head n connection |
| sh_n_Id | Station head n ID |
| vaild_from | Validity start date (YYYY-MM-DD HH:MM) |
| valid_to | Validity end date (YYYY-MM-DD HH:MM) |
| pos_x | X position coordinate |
| pos_y | Y position coordinate |

#### Format
```csv
id;location_code;name;lenth;type;sh_1;sh_1_id;sh_n;sh_n_Id;vaild_from;valid_to;pos_x;pos_y
1;XYZ;1;260;workshop;1;5;0;;;;1;7
```

### 3. `process_times_medium_251027.csv` (Process Times)
Defines timing parameters for operations:
- **Process Groups:**
  - **Group 1:** Train operations (approach, preparation, departure, arrival, detach, drive-off)
  - **Group 2:** Shunting operations (approach, preparation, movement, detach, drive-off)
  - **Group 3:** Workshop operations (lot size: 3 wagons, processing time: 180 min)
  - **Group 4:** Delays and waiting times (selector delay, job readiness, waiting periods)
- **Delimiter:** Semicolon (`;`)

#### Table
| Column | Description |
|--------|-------------|
| id | Process identifier |
| group | Process group number |
| number | Process number within group |
| location | Location code (0 for general) |
| process_step | Process step name |
| time_sc | Time in minutes for screw coupler |
| time_dac | Time in minutes for DAC |
| other unit | Other unit count |
| loco | Locomotive required (0/1) |
| inspector | Inspector required (0/1) |
| track | Track required (0/1) |
| station_head | Station head required (0/1) |
| comment | Additional comments |

#### Format
```csv
id;group;number;location;process_step;time_sc;time_dac;other unit;loco;inspector;track;station_head;comment
;1;1;0;train_approach_loco;3;3;;1;0;1;1;loco drives to wagons
```

## Usage

Run this scenario using the PopUp-Sim backend:

```bash
# From project root
python popupsim/backend/src/main.py --scenarioPath Data/examples/medium_scenario_251027/ --outputPath Data/results/medium_scenario_251027
```

## Notes

- All CSV files use semicolon (`;`) as delimiter
- Time values are in minutes
- Tracks include temporal validity periods (`vaild_from`, `valid_to`)
- Workshop processes 3 wagons per lot with 180 min processing time

---

**Need help?** See the [main backend documentation](../../../popupsim/backend/README.md) for setup and development instructions.
