# 6. Laufzeitsicht (MVP)

## 6.1 MVP Simulation Flow

### MVP Execution Sequence

```mermaid
sequenceDiagram
    participant User as User
    participant Main as main.py
    participant Config as Configuration
    participant Workshop as Workshop
    participant SimPy as SimPy
    participant Output as Output
    
    User->>Main: python main.py
    
    Main->>Config: load_scenario()
    Config->>Config: read JSON/CSV
    Config->>Main: return config
    
    Main->>Workshop: setup_workshop(config)
    Workshop->>Workshop: create stations
    Workshop->>Main: return workshop
    
    Main->>SimPy: run_simulation(24h)
    
    loop Every Hour
        SimPy->>Workshop: train_arrival()
        Workshop->>Workshop: process_wagons()
        Workshop->>SimPy: retrofit_complete()
    end
    
    SimPy->>Main: simulation_done
    
    Main->>Output: generate_results()
    Output->>Output: create CSV
    Output->>Output: create charts
    Output->>Main: files_created
```

## 6.2 MVP Szenario: Basis-Simulation

### 24h Simulation mit 4 Stationen

**Input:**
- 4 Werkstatt-Stationen
- Stündliche Zugankünfte
- 20 Wagen pro Zug

**Ablauf:**
1. **Konfiguration laden** (0.1s)
2. **Workshop setup** (0.1s)
3. **24h Simulation** (10-30s)
4. **Ergebnisse generieren** (2-5s)

**Output:**
- `simulation_results.csv` - KPI Daten
- `kpi_charts.png` - Matplotlib Charts
- `simulation_log.json` - Event Timeline

## 6.3 MVP Performance

### Timing Breakdown

| Phase | Duration | Aktivität |
|-------|----------|-----------|
| Configuration | 0.1s | JSON/CSV laden |
| Setup | 0.1s | Workshop erstellen |
| Simulation | 10-30s | SimPy ausführen |
| Output | 2-5s | CSV + Charts |

### Skalierbarkeit

- **Klein**: 100 Wagen < 5s
- **Mittel**: 1000 Wagen < 30s  
- **Groß**: 5000 Wagen < 2min
- **MVP Limit**: 10000 Wagen < 5min

---

**Navigation:** [← MVP Bausteinsicht](05-building-blocks.md) | [MVP Verteilungssicht →](07-deployment.md)