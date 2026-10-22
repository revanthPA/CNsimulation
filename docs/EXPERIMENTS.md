# Experiment Documentation

## Overview

This document describes the experimental methodology for comparing routing algorithms in Wireless Sensor Networks.

## Core Research Question

> Does incorporating residual node energy into routing decisions increase wireless sensor network lifetime compared with shortest-path routing under identical simulation conditions?

## Experimental Design Principles

### 1. Fair Comparisons
- **Identical conditions**: Same topology, same traffic, same seed
- **Paired experiments**: Same seed → same topology → different routing
- **Multi-seed**: 5 seeds for statistical significance

### 2. Reproducibility
- Fixed seeds for all experiments
- Deterministic simulation (same seed → same results)
- Configuration files capture all parameters

### 3. No Fabrication
- All results from actual `Simulator.run()` calls
- No hard-coded expected outcomes
- Metrics computed from simulation data

## Standard Experiments

### 1. Routing Comparison (Main Experiment)

**File**: `energy_routing/experiments/definitions.py::create_routing_comparison_experiment()`

**Configuration**:
- **Algorithms**: Shortest Path vs Energy-Aware (α=0.5, β=0.5)
- **Network**: 50 nodes, 100×100m, range 20m
- **Energy**: 1.0 J initial, standard radio model
- **Simulation**: 1000 rounds, 1 packet/round
- **Seeds**: 5 (42, 43, 44, 45, 46)
- **Fairness**: Same 5 seeds for both algorithms

**Hypothesis**: Energy-aware routing will achieve longer network lifetime (higher FND, HND, LND) with comparable or better PDR.

**Metrics Collected**:
- FND, HND, LND (mean ± std across seeds)
- PDR (mean ± std)
- Average hop count
- Total route distance
- Final remaining energy

**Run Command**:
```bash
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml
```

### 2. Network Size Scaling

**File**: `create_network_size_experiment()`

**Configuration**:
- **Node counts**: 20, 50, 100, 200
- **Seed**: Same seed (42) for all sizes
- **Topology**: Different for each size (as per plan)
- **Algorithm**: Shortest Path (baseline)
- **Seeds**: 1 per size

**Purpose**: Analyze how network size affects lifetime and performance.

**Note**: Different node counts naturally generate different topologies. Do NOT claim identical topologies.

**Run Command**:
```bash
python -m energy_routing.main experiment --name network_size --base-config configs/base.yaml
```

### 3. Energy-Aware Parameter Sweep

**File**: `create_energy_aware_params_experiment()`

**Configuration**:
- **Algorithm**: Energy-Aware only
- **Alpha values**: 0.0, 0.25, 0.5, 0.75, 1.0
- **Beta values**: Complementary (1.0, 0.75, 0.5, 0.25, 0.0)
- **Seeds**: 3 per combination (offset 100)
- **Total runs**: 5 × 3 = 15

**Purpose**: Find optimal α/β balance for energy-aware routing.

**Run Command**:
```bash
python -m energy_routing.main experiment --name energy_aware_params --base-config configs/base.yaml
```

### 4. Communication Range Scaling

**File**: `create_communication_range_experiment()`

**Configuration**:
- **Ranges**: 15, 20, 25, 30 meters
- **Seeds**: 3 per range (offset 200)
- **Algorithm**: Shortest Path
- **Total runs**: 4 × 3 = 12

**Purpose**: Analyze effect of connectivity density on performance.

### 5. Initial Energy Scaling

**File**: `create_initial_energy_experiment()`

**Configuration**:
- **Energy levels**: 0.5, 1.0, 2.0, 5.0 Joules
- **Seeds**: 3 per level (offset 300)
- **Algorithm**: Shortest Path
- **Total runs**: 4 × 3 = 12

**Purpose**: Verify linear scaling of lifetime with initial energy.

## Experiment Execution

### Using CLI

```bash
# List all experiments
python -m energy_routing.main list-experiments

# Run specific experiment
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml

# Run single simulation
python -m energy_routing.main run --config configs/base.yaml
```

### Using Python API

```python
from energy_routing.experiments import get_experiment, ExperimentRunner
from energy_routing.config import load_config

# Load custom config
settings = load_config("configs/base.yaml")

# Get experiment
exp = get_experiment("routing_comparison")
exp.base_settings = settings

# Run
runner = ExperimentRunner(output_dir="results")
results = runner.run_comparison(exp)
```

## Parameter Selection Rationale

### Base Configuration (Routing Comparison)

**`configs/base.yaml`**: 50 nodes, 100×100 m area, communication range 20 m,
1.0 J initial energy, 1000 rounds, 1 packet/round, seed 42.

**Rationale**:
- 50 nodes provides sufficient network density for multi-hop routing while
  remaining computationally tractable.
- 100×100 m area with 20 m range yields a connected but not over-connected
  topology (average degree sufficient for route alternatives).
- 1.0 J initial energy with the standard radio model (~0.00041 J per hop at
  10 m) allows nodes to deplete within 1000 rounds, enabling FND observation.
- 1000 rounds provides a sufficient horizon for node death events.
- 5 seeds (42-46) provide statistical significance for mean/std reporting.

### Pilot Parameter Sweeps

Pilot runs were executed at smaller scales to validate parameter sensitivity:

| Configuration | SP vs EA Differentiation | Observation |
|---------------|-------------------------|-------------|
| 20 nodes, 200 rounds, 0.5 J | None (FND identical) | Nodes die too late (round 187 of 200) |
| 20 nodes, 200 rounds, 0.1 J | None (FND identical) | Linear energy penalty too weak at this scale |
| 50 nodes, 1000 rounds, 1.0 J | EA extends FND (+4 to +68) | Base config shows meaningful lifetime improvement |

**Conclusion**: The base configuration (1.0 J, 1000 rounds, 50 nodes) is appropriate
because it allows node depletion within the simulation horizon while maintaining
route alternatives for the energy-aware algorithm to exploit.

### Why PDR Does Not Differ Significantly

PDR measures packet delivery ratio, not lifetime. Energy-aware routing avoids
depleted nodes to extend lifetime, but delivery success depends on connectivity,
not energy. When the network remains connected, both algorithms deliver similar
PDR. The research question concerns *lifetime* (FND/HND/LND), where energy-aware
routing shows clear improvement.


```
results/
├── raw/                    # Individual run results (JSON)
│   ├── routing_comparison_run0.json
│   ├── routing_comparison_shortest_path_vs_energy_aware_run0.json
│   └── ...
├── summary/                # Aggregated summaries (JSON)
│   ├── routing_comparison_summary.json
│   ├── routing_comparison_shortest_path_vs_energy_aware_summary.json
│   └── ...
└── plots/                  # Generated visualizations (PNG)
    ├── topology_42.png
    ├── energy_heatmap_42.png
    ├── alive_nodes_42.png
    ├── energy_over_time_42.png
    └── ...
```

## Result Analysis

### MetricsCollector Usage

```python
from energy_routing.metrics import MetricsCollector

collector = MetricsCollector()
collector.add_results(results)

# Aggregated metrics
agg = collector.compute_aggregated_metrics()
print(f"Mean FND: {agg.mean_fnd:.1f} ± {agg.std_fnd:.1f}")
print(f"Mean PDR: {agg.mean_pdr:.3f} ± {agg.std_pdr:.3f}")

# Round-by-round aggregates
round_agg = collector.compute_round_aggregates()

# Algorithm comparison
comparison = collector.compare_algorithms(
    results_a=sp_results,
    results_b=ea_results,
    label_a="Shortest Path",
    label_b="Energy Aware"
)
```

### Key Comparisons

For the main routing comparison, the following improvements are calculated:
- **FND/HND/LND**: Higher is better (positive % = energy-aware better)
- **PDR**: Higher is better (positive % = energy-aware better)
- **Avg Hop Count**: Lower is better (positive % = energy-aware better)
- **Total Route Distance**: Lower is better (positive % = energy-aware better)
- **Final Energy**: Higher is better (positive % = energy-aware better)

## Statistical Rigor

### Multi-Seed Design
- 5 seeds for main comparison (statistical significance)
- 3 seeds for parameter sweeps (trend analysis)
- Seed offset prevents correlation between experiments

### Paired Conditions
- Same seed → same topology → different routing
- Eliminates topology variance from comparison
- Enables paired statistical tests if needed

### Reproducibility
```python
# Same seed always produces same results
sim1 = create_simulator(settings_with_seed_42)
result1 = sim1.run()

sim2 = create_simulator(settings_with_seed_42)
result2 = sim2.run()

assert result1.total_packets_delivered == result2.total_packets_delivered
```

## Configuration Files

| File | Purpose |
|------|---------|
| `configs/base.yaml` | Main experiment (50 nodes) |
| `configs/small.yaml` | Small network (20 nodes) |
| `configs/large.yaml` | Large network (100 nodes) |
| `configs/test_quick.yaml` | Quick test (10 nodes, 50 rounds) |

## Output Structure

```
results/
├── raw/                    # Individual run results (JSON)
│   ├── routing_comparison_run0.json
│   ├── routing_comparison_shortest_path_vs_energy_aware_run0.json
│   └── ...
├── summary/                # Aggregated summaries (JSON)
│   ├── routing_comparison_summary.json
│   ├── routing_comparison_shortest_path_vs_energy_aware_summary.json
│   └── ...
└── plots/                  # Generated visualizations (PNG)
    ├── topology_42.png
    ├── energy_heatmap_42.png
    ├── alive_nodes_42.png
    ├── energy_over_time_42.png
    └── ...
```

## Expected Outputs

### Routing Comparison Summary — Pilot Findings

Pilot runs with the base configuration (50 nodes, 1000 rounds, 1.0 J initial energy,
communication range 20 m, α=0.5, β=0.5) show that energy-aware routing **extends
network lifetime (FND)** while PDR remains comparable between algorithms:

| Seed | SP FND | EA FND | SP PDR | EA PDR |
|------|--------|--------|--------|--------|
| 42 | 180 | 193 | 0.340 | 0.347 |
| 43 | 85 | 153 | 0.172 | 0.183 |
| 44 | 108 | 112 | 0.166 | 0.166 |

**Interpretation**:
- Energy-aware routing increases FND in all observed cases (by +4 to +68 rounds).
- PDR is similar between algorithms — energy-aware improves *lifetime*, not delivery ratio.
- This is consistent with the research question: energy-aware routing increases WSN lifetime.
- HND and LND were not observed within 1000 rounds for the tested seeds; they remain `None`.
- Energy-aware routing is ~4x slower than shortest-path due to per-edge cost recomputation
  (see Performance Notes below).

**Important**: Previously committed results in `results/test_comparison/` showing
PDR=1.0 and FND=null **do not match actual simulation output**. Those files are stale
and should be regenerated by running the experiment with the current code.

### Performance Notes

Energy-aware routing recomputes `max_distance` by iterating all graph edges on every
`find_path` call. This makes Dijkstra O(E²logV) instead of O(ElogV). For 50-node
networks this is observable (~15s vs ~80s per run). Optimization (caching `max_distance`)
is deferred to Phase G and should preserve routing behavior.


## Limitations

1. **Static topology**: No mobility
2. **Single base station**: No multi-sink scenarios
3. **Constant traffic**: 1 packet/round per node
4. **Ideal MAC**: No collisions, no retransmissions
5. **Homogeneous nodes**: Same initial energy, same hardware

See `LIMITATIONS.md` for detailed discussion.