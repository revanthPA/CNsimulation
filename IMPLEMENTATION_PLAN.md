# Energy-Aware Routing Protocol: Implementation Plan
*Comprehensive Engineering Plan for WSN Simulation - Version 4.0*

---

## 🎯 PROJECT OVERVIEW

**Project:** Energy-Aware Routing Protocol for Wireless Sensor Networks – Comparative Simulation

**Type:** Pure software simulation (no hardware, radios, MQTT, or cloud)

**Core Research Question:** Does incorporating residual node energy into routing decisions increase WSN lifetime compared with shortest-path routing under **identical** conditions?

---

## 🔧 CORE SPECIFICATIONS

### 1. Exact Failed-Hop Energy Accounting (CRITICAL)
The simulator implements **exactly three cases** for energy consumption:

| Case | Condition | TX Energy | RX Energy | Status |
|------|-----------|-----------|-----------|--------|
| 1 | Failed before TX (transmitter dead or insufficient energy) | ❌ NO | ❌ NO | LOST |
| 2 | Successful TX + dead receiver | ✅ YES | ❌ NO | LOST |
| 3 | Successful TX + successful RX | ✅ YES | ✅ YES | DELIVERED |

**Implementation (`simulation/simulator.py`):**
```python
def _deliver_hop(self, current: int, next_hop: int, distance: float) -> bool:
    # CASE 1: Failed before TX → no energy consumed
    tx_cost = self.energy_model.transmit_cost(distance)
    if not self.nodes[current].can_transmit(tx_cost):
        return False  # ❌ NO TX, ❌ NO RX

    # CASE 2 & 3: TX energy consumed
    self.nodes[current].consume_energy(tx_cost)

    # CASE 2: Dead receiver → TX consumed, RX NOT consumed
    if not self.nodes[next_hop].is_alive:
        return False  # ✅ TX consumed, ❌ RX NOT consumed

    # CASE 3: Successful RX → both consumed
    rx_cost = self.energy_model.receive_cost()
    self.nodes[next_hop].consume_energy(rx_cost)
    return True  # ✅ TX consumed, ✅ RX consumed
```

---

### 2. All User Corrections Incorporated

| # | Correction | Status |
|---|------------|--------|
| 1 | `SimulationConfig` → `SimulationParameters` | ✅ Applied |
| 2 | `Packet.path: List[int]` → `Tuple[int, ...]` | ✅ Applied |
| 3 | **Exact failed-hop energy accounting (3 cases)** | ✅ Applied |
| 4 | Network-size experiments: same seed, **different topologies** | ✅ Applied |
| 5 | `avg_path_length` → `avg_hop_count` | ✅ Applied |
| 6 | Multi-seed runs for main comparison | ✅ Applied |
| 7 | Streamlit explicitly **optional and post-core** | ✅ Applied |
| 8 | Focused tests after logical units, full pytest after each stage | ✅ Applied |

---

## 🏗️ ARCHITECTURE

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

---

## 📁 REPOSITORY STRUCTURE

```
energy-aware-routing/
│
├── .gitignore
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
│
├── configs/
│   ├── base.yaml
│   ├── small.yaml
│   └── large.yaml
│
├── results/
│   ├── raw/
│   ├── summary/
│   └── plots/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ALGORITHM.md
│   ├── ENERGY_MODEL.md
│   ├── EXPERIMENTS.md
│   ├── LIMITATIONS.md
│   └── DEVELOPMENT.md
│
├── src/
│   └── energy_routing/
│       ├── __init__.py
│       ├── config.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── node.py
│       │   ├── packet.py
│       │   └── result.py
│       │
│       ├── network/
│       │   ├── __init__.py
│       │   ├── topology.py
│       │   └── graph.py
│       │
│       ├── routing/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── shortest_path.py
│       │   └── energy_aware.py
│       │
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── energy_model.py
│       │   └── simulator.py
│       │
│       ├── metrics/
│       │   ├── __init__.py
│       │   └── collector.py
│       │
│       ├── experiments/
│       │   ├── __init__.py
│       │   └── runner.py
│       │
│       └── visualization/
│           ├── __init__.py
│           ├── network_plot.py
│           └── charts.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models/
    │   ├── __init__.py
    │   ├── test_node.py
    │   ├── test_packet.py
    │   └── test_result.py
    ├── test_network/
    │   ├── __init__.py
    │   ├── test_topology.py
    │   └── test_graph.py
    ├── test_routing/
    │   ├── __init__.py
    │   ├── test_shortest_path.py
    │   └── test_energy_aware.py
    ├── test_simulation/
    │   ├── __init__.py
    │   ├── test_energy_model.py
    │   └── test_simulator.py
    ├── test_metrics/
    │   └── test_collector.py
    └── test_experiments/
        └── test_runner.py
```

---

## 📋 TODO LIST

---

### 🚀 PHASE 1: FOUNDATION (Stages 0-3)

#### Stage 0: Project Bootstrap
- [ ] Create repository: `energy-aware-routing/`
- [ ] Create directory structure (src/, tests/, configs/, results/, docs/)
- [ ] Create `.gitignore`
- [ ] Create `requirements.txt`
- [ ] Create `requirements-dev.txt`
- [ ] Create `pyproject.toml`
- [ ] Create `README.md` (stub)
- [ ] Initialize Git: `git init`
- [ ] Create initial commit

**Definition of Done:** Repository exists, all directories created, Git initialized

---

#### Stage 1: Domain Models
- [ ] Implement `Node` class in `models/node.py`
- [ ] Implement `Packet` class in `models/packet.py`
  - [ ] Use `Tuple[int, ...]` for path (immutable)
- [ ] Implement `RoundMetrics` in `models/result.py`
- [ ] Implement `SimulationResult` in `models/result.py`
  - [ ] Include `avg_hop_count` (not avg_path_length)
- [ ] Implement config classes in `config.py`
  - [ ] `NetworkConfig`, `EnergyConfig`, `SimulationParameters`, `RoutingConfig`, `OutputConfig`, `SimulationSettings`
- [ ] Write tests in `tests/test_models/`

**Definition of Done:** All models implemented, all model tests pass

---

#### Stage 2: Network Topology and Graph
- [ ] Implement `Topology` class and `generate_topology()` in `network/topology.py`
- [ ] Implement `build_graph()` and `get_alive_subgraph()` in `network/graph.py`
- [ ] Write tests in `tests/test_network/`

**Definition of Done:** Topology generation works, graph building works, all network tests pass

---

#### Stage 3: Energy Model
- [ ] Implement `EnergyModel` in `simulation/energy_model.py`
- [ ] Write tests in `tests/test_simulation/test_energy_model.py`

**Definition of Done:** Energy calculations correct, all energy tests pass

---

### 🏗️ PHASE 2: CORE SIMULATION (Stages 4-7)

#### Stage 4: Routing Abstraction + Shortest Path
- [ ] Implement `RoutingStrategy` ABC in `routing/base.py`
- [ ] Implement `ShortestPathRouting` in `routing/shortest_path.py`
- [ ] Implement routing factory in `routing/__init__.py`
- [ ] Write tests in `tests/test_routing/test_shortest_path.py`

**Definition of Done:** Shortest-path routing works, all routing tests pass

---

#### Stage 5: Energy-Aware Routing
- [ ] Implement `EnergyAwareRouting` in `routing/energy_aware.py`
  - [ ] Handle base station explicitly (avoid inf/inf)
- [ ] Write tests in `tests/test_routing/test_energy_aware.py`

**Definition of Done:** Energy-aware routing works, all tests pass

---

#### Stage 6: Simulation Engine
- [ ] Implement `Simulator` in `simulation/simulator.py`
  - [ ] **Implement EXACT failed-hop energy accounting (3 cases)**
- [ ] Write tests in `tests/test_simulation/test_simulator.py`

**Definition of Done:** Simulator runs end-to-end, exact energy accounting implemented, all tests pass

---

#### Stage 7: Metrics Collection
- [ ] Implement `MetricsCollector` in `metrics/collector.py`
  - [ ] Calculate `avg_hop_count` (not avg_path_length)
- [ ] Write tests in `tests/test_metrics/test_collector.py`

**Definition of Done:** Metrics collected correctly, all metrics tests pass

---

### 📊 PHASE 3: EXPERIMENTS & VISUALIZATION (Stages 8-9)

#### Stage 8: Experiment Runner
- [ ] Implement `Experiment` and `ExperimentRunner` in `experiments/runner.py`
- [ ] Implement experiment factories in `experiments/definitions.py`
  - [ ] **Multi-seed (5 seeds) for routing_comparison**
  - [ ] **Same seed, different topologies for network_size**
- [ ] Implement experiment registry in `experiments/__init__.py`
- [ ] Write tests in `tests/test_experiments/test_runner.py`

**Definition of Done:** All experiments run, results saved, all experiment tests pass

---

#### Stage 9: Visualization
- [ ] Implement `ResultVisualizer` in `visualization/charts.py`
- [ ] Implement `plot_network_topology()` in `visualization/network_plot.py`
- [ ] Write tests in `tests/test_visualization/`

**Definition of Done:** All visualizations work, all visualization tests pass

---

### 🎯 PHASE 4: VALIDATION & DOCUMENTATION (Stages 10-11)

#### Stage 10: Formal Experiments
- [ ] Create config files (`configs/base.yaml`, `configs/small.yaml`)
- [ ] Run all 5 experiments
- [ ] Verify reproducibility
- [ ] Generate all visualizations

**Definition of Done:** All experiments run successfully, results reproducible

---

#### Stage 11: Documentation and Cleanup
- [ ] Complete `README.md`
- [ ] Write `docs/ARCHITECTURE.md`
- [ ] Write `docs/ALGORITHM.md`
  - [ ] Document exact failed-hop energy accounting
- [ ] Write `docs/ENERGY_MODEL.md`
- [ ] Write `docs/EXPERIMENTS.md`
  - [ ] Document multi-seed runs
  - [ ] Document same seed, different topologies
- [ ] Write `docs/LIMITATIONS.md`
- [ ] Write `docs/DEVELOPMENT.md`
  - [ ] Document test strategy
- [ ] Add docstrings to all code
- [ ] Add type hints to all code
- [ ] Run full test suite
- [ ] Clean up code

**Definition of Done:** All documentation complete, all tests pass, code clean

---

### ✨ PHASE 5: OPTIONAL (Stage 12)

#### Stage 12: Streamlit Dashboard (OPTIONAL - POST-CORE)
- [ ] Add `streamlit` to `requirements.txt`
- [ ] Implement `dashboard.py`
- [ ] Write tests in `tests/test_dashboard.py`

**Definition of Done:** Dashboard works (optional)

**NOTE:** This stage is **explicitly optional and post-core**. Do NOT block core implementation on this.

---

## 🎯 TEST EXECUTION PROTOCOL

| When | Test Scope | Command | Purpose |
|------|------------|---------|---------|
| After each logical unit | Focused unit tests | `pytest tests/test_<module>/<file>.py -v` | Verify specific functionality |
| After each module | Module tests | `pytest tests/test_<module>/ -v` | Verify module integration |
| **After each stage** | **Full test suite** | `pytest tests/ -v` | **Verify no regressions** |

**Example:**
```bash
# After implementing Node
pytest tests/test_models/test_node.py -v

# After completing Stage 1
pytest tests/test_models/ -v
pytest tests/ -v  # Full suite
```

---

## ⚠️ CRITICAL REMINDERS

### For Implementation:
- ✅ **Exact failed-hop energy accounting:** Implement the 3 cases precisely
- ✅ **Multi-seed for main comparison:** 5 seeds for routing_comparison
- ✅ **Same seed, different topologies:** For network_size experiment
- ✅ **Use avg_hop_count:** Not avg_path_length
- ✅ **Streamlit is optional:** Only Stage 12, can be skipped

### For All Code:
- ✅ **No fabricated results:** All from actual `Simulator.run()`
- ✅ **No hard-coded outcomes:** Comparisons use actual results
- ✅ **Deterministic:** Same seed → same results
- ✅ **Fair comparisons:** Identical conditions for algorithm comparisons
- ✅ **Static topology:** Dead nodes marked, not removed

---

## 📊 IMPLEMENTATION CHECKLIST

### Before Each Stage:
- [ ] Review stage requirements
- [ ] Check git status: `git status`

### After Each Stage:
- [ ] Run focused tests for new code
- [ ] Run **full test suite**: `pytest tests/ -v`
- [ ] Verify all acceptance criteria
- [ ] Review changes: `git diff`
- [ ] Commit: `git add . && git commit -m "Stage N: description"`

### Final Verification:
- [ ] All stages complete (0-11, optional 12)
- [ ] All tests pass
- [ ] All experiments run successfully
- [ ] All visualizations generate correctly
- [ ] All documentation complete
- [ ] Git history clean

---

## 🎯 PRIORITY ORDER

| Priority | Stages | Description |
|----------|--------|-------------|
| P0 (Critical) | 0-7 | Core simulation |
| P1 (High) | 8-9 | Experiments and visualization |
| P2 (Medium) | 10 | Formal experiments and validation |
| P3 (Low) | 11 | Documentation and cleanup |
| P4 (Optional) | 12 | Streamlit dashboard |

---

## 📅 ESTIMATED TIMELINE

| Phase | Stages | Estimated Time | Deliverables |
|-------|--------|----------------|--------------|
| Foundation | 0-3 | 8-10 hours | Project setup, models, network, energy |
| Core Simulation | 4-7 | 15-20 hours | Routing, simulator, metrics |
| Experiments & Viz | 8-9 | 10-12 hours | Experiment runner, visualizations |
| Validation | 10 | 5-8 hours | All experiments run, results verified |
| Documentation | 11 | 6-8 hours | All docs complete |
| **Total (Core)** | **0-11** | **44-66 hours** | **Complete project** |
| Optional | 12 | 4-6 hours | Streamlit dashboard |

---

## 📌 QUICK START

### 1. Set up the project
```bash
mkdir energy-aware-routing
cd energy-aware-routing
git init
# Create all directories as per repository structure
```

### 2. Create config files
```bash
# configs/base.yaml
network:
  num_nodes: 50
  area_width: 100.0
  area_height: 100.0
  communication_range: 20.0
  seed: 42
  base_station_x: 50.0
  base_station_y: 50.0
  topology: "random"

energy:
  initial_energy: 1.0
  E_elec: 50.0
  E_amp: 0.0013
  packet_size: 512

simulation:
  num_rounds: 1000
  packets_per_round: 1
  packet_size: 512

routing:
  algorithm: "shortest_path"
  alpha: 0.5
  beta: 0.5

output:
  results_dir: "results"
  save_results: true
  generate_plots: true
  plot_format: "png"
```

### 3. Install dependencies
```bash
pip install networkx numpy pandas matplotlib pyyaml pytest
```

### 4. Begin implementation with Stage 0

---

## 🏆 DEFINITION OF DONE

The project is **complete** when:
- ✅ Simulator runs end-to-end with both routing algorithms
- ✅ Results are reproducible (same seed → same results)
- ✅ Exact failed-hop energy accounting implemented (3 cases)
- ✅ All metrics calculated correctly (FND, HND, LND, PDR, avg_hop_count)
- ✅ All 5 experiments run successfully
- ✅ All visualizations generate correctly
- ✅ All tests pass
- ✅ All documentation complete
- ✅ No fabricated results
- ✅ Git history clean

---

*Last updated: August 30, 2026*
*Version: 4.0*
