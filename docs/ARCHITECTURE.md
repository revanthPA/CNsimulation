# System Architecture

## Overview

The Energy-Aware Routing Protocol simulator follows a modular, layered architecture that separates concerns and enables interchangeable components.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                              CLI (main.py)                       │
└─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                           EXPERIMENTS (runner.py)                │
└─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                         VISUALIZATION (charts.py)               │
└─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                         SIMULATOR (simulator.py)                │
│  - Dependency Injection: Network, RoutingStrategy, EnergyModel  │
│  - Implements EXACT failed-hop energy accounting (3 cases)    │
└─────────────────────────────────────────────────────────────┘
               │               │               │               │
               ▼               ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   NETWORK        │ │   ROUTING        │ │   ENERGY MODEL   │
│ (topology.py,    │ │ (base.py,        │ │ (energy_model.py)│
│  graph.py)       │ │  shortest_path,  │ │                 │
│                 │ │  energy_aware)   │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                           DATA MODELS                           │
│  - Packet.path: Tuple[int, ...] (immutable)                    │
│  - SimulationParameters (not SimulationConfig)                 │
│  - avg_hop_count (not avg_path_length)                        │
└─────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### 1. Configuration (`config.py`)
- Centralized configuration management using dataclasses
- Validation in `__post_init__` methods
- YAML loading/saving support

### 2. Data Models (`models/`)
- **Node**: Sensor node with position, energy, statistics
- **Packet**: Immutable packet with path tracking (Tuple[int, ...])
- **Result**: Simulation results with metrics (FND, HND, LND, PDR, etc.)

### 3. Network (`network/`)
- **Topology**: Static node positions, base station with infinite energy
- **Graph**: NetworkX graph with distance edges, alive subgraph extraction

### 4. Routing (`routing/`)
- **RoutingStrategy** (ABC): Interface for routing algorithms
- **ShortestPathRouting**: Dijkstra's algorithm using distance weights
- **EnergyAwareRouting**: Weighted cost (α·distance + β·energy)
- **Factory**: `create_routing_strategy()` for instantiation

### 5. Simulation (`simulation/`)
- **EnergyModel**: First-order radio model (TX: k·E_elec + k·E_amp·d², RX: k·E_elec)
- **Simulator**: Core engine with exact 3-case energy accounting:
  1. Failed before TX → NO energy consumed
  2. Successful TX + dead receiver → TX consumed, RX NOT consumed
  3. Successful TX + successful RX → Both consumed

### 6. Metrics (`metrics/`)
- **MetricsCollector**: Aggregates results across runs
- **AggregatedMetrics**: Mean/std for FND, HND, LND, PDR, hop count, etc.
- **Algorithm comparison**: Percentage improvements

### 7. Experiments (`experiments/`)
- **Experiment**: Configurable experiment with parameter variations
- **ExperimentRunner**: Executes experiments, saves results
- **Definitions**: 5 standard experiments (routing_comparison, network_size, etc.)

### 8. Visualization (`visualization/`)
- **Network plots**: Topology with alive/dead nodes, energy heatmaps
- **Charts**: Time series, comparisons, scaling plots

## Key Architectural Principles

1. **Routing strategies are interchangeable** - Same simulator works with any RoutingStrategy
2. **Energy model is replaceable** - EnergyModel can be swapped without changing simulator
3. **Simulator has no hard-coded routing** - Uses dependency injection
4. **Visualization separate from simulation** - No control flow in visualization
5. **Experiments don't modify simulation internals** - Clean separation
6. **Domain models independent of simulation logic** - Pure data classes
7. **No circular imports** - Strict layering
8. **Configuration centralized** - Single SimulationSettings object
9. **Topology structurally static** - Dead nodes marked, not removed
10. **Dead nodes represented by state** - `is_alive` flag, excluded from routing
11. **Packet paths immutable** - Tuple[int, ...], modified via `dataclasses.replace()`
12. **Deterministic execution** - Same seed → same results