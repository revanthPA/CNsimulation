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

### Routing Comparison Summary — Hardened Results (20 seeds, base configuration)

The main comparison experiment was run with `configs/base.yaml` (50 nodes,
100×100 m area, communication range 20 m, 1.0 J initial energy, 1000 rounds,
1 packet/round, α=0.5, β=0.5) using 20 paired seeds (42–61):

Command:
```bash
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml --output results/routing_comparison_base
```

For a larger hardened run (20 seeds, seeds 42–61), results were saved to
`results/routing_comparison_hardened/` using the Python API directly.

| Seed | SP PDR | EA PDR | SP FND | EA FND | EA−SP FND | SP HND | EA HND |
|------|--------|--------|--------|--------|-----------|--------|--------|
| 42 | 0.3401 | 0.3465 | 180 | 193 | +13 | None | None |
| 43 | 0.1720 | 0.1826 | 85 | 153 | +68 | None | None |
| 44 | 0.1656 | 0.1656 | 108 | 112 | +4 | None | None |
| 45 | 0.4067 | 0.4060 | 180 | 225 | +45 | None | None |
| 46 | 0.0501 | 0.0501 | 50 | 50 | 0 | None | None |
| 47 | 0.4738 | 0.4594 | 256 | 290 | +34 | None | None |
| 48 | 0.2377 | 0.2377 | 180 | 171 | −9 | None | None |
| 49 | 0.4788 | 0.5002 | 157 | 209 | +52 | None | None |
| 50 | 0.4791 | 0.4600 | 168 | 194 | +26 | None | None |
| 51 | 0.2775 | 0.3031 | 131 | 131 | 0 | None | None |
| 52 | 0.2642 | 0.2609 | 99 | 99 | 0 | None | None |
| 53 | 0.3374 | 0.3432 | 147 | 257 | +110 | None | None |
| 54 | 0.3068 | 0.3281 | 147 | 183 | +36 | None | None |
| 55 | 0.6273 | 0.6312 | 131 | 277 | +146 | None | None |
| 56 | 0.2869 | 0.3150 | 92 | 112 | +20 | None | None |
| 57 | 0.4257 | 0.4142 | 131 | 229 | +98 | None | None |
| 58 | 0.3500 | 0.3389 | 168 | 255 | +87 | None | None |
| 59 | 0.3300 | 0.3501 | 118 | 130 | +12 | None | None |
| 60 | 0.5237 | 0.5586 | 255 | 353 | +98 | None | None |
| 61 | 0.2749 | 0.3028 | 231 | 248 | +17 | None | None |

**Aggregate (20 seeds):**
- Shortest Path: mean FND = 150.7 ± 54.4, mean PDR = 0.3404 ± 0.1368
- Energy-Aware: mean FND = 193.6 ± 75.4, mean PDR = 0.3477 ± 0.1367
- Mean paired FND improvement (EA−SP): 42.9 rounds
- Median paired FND improvement: 30.0 rounds
- 95% CI for paired FND diff: [22.2, 63.5]
- Mean paired PDR diff: +0.0073

**Interpretation:**
- Energy-aware routing extends FND in 16 of 20 seeds (3 ties, 1 regression).
- PDR is similar between algorithms — energy-aware improves *lifetime*, not delivery ratio.
- HND and LND were not observed within the 1000-round horizon for any seed; they remain `None`.
- Based on 20 seeds, the mean FND improvement is positive with a 95% CI
  that excludes zero ([22.2, 63.5]), suggesting a consistent lifetime benefit.
  However, 20 seeds is still a modest sample; larger studies may be warranted.

### Configuration Files

| File | Purpose |
|------|---------|
| `configs/base.yaml` | Main comparison experiment (50 nodes, 1000 rounds, 1.0 J) |
| `configs/small.yaml` | Small network (20 nodes) |
| `configs/large.yaml` | Large network (100 nodes) |
| `configs/test_quick.yaml` | Short smoke test (10 nodes, 50 rounds) — NOT the main comparison configuration |

**Important note on `results/test_comparison/`:**
The previously committed files in `results/test_comparison/` were generated using
`configs/test_quick.yaml` (10 nodes, 50 rounds), not `configs/base.yaml`. With only
10 nodes and 50 rounds at 1.0 J initial energy, no node depletes within the horizon,
so those outputs show PDR=1.0 and FND=null for both algorithms. They are correct for
the quick-test configuration but do not represent the main comparison experiment.
The hardened results above (`results/routing_comparison_hardened/`) use the correct
base configuration with 20 seeds.

### Performance Notes

Energy-aware routing caches the maximum edge distance (`max_distance`)
per graph object to avoid redundant O(E) edge iteration on every
`find_path` call. This reduced the EA/SP runtime ratio from ~4.85x to
~3.32x (measured on 100 rounds, 3 seeds). Routing decisions are
identical with or without the cache.

Optimization details:
- `max_distance` is cached keyed by graph object identity in
  `EnergyAwareRouting._get_max_distance()`
- The cache is valid because edge distances are static during simulation
- The same alive subgraph is reused for all packets within a round
- No stale-cache behavior is possible within the supported API


## Limitations

1. **Static topology**: No mobility
2. **Single base station**: No multi-sink scenarios
3. **Constant traffic**: 1 packet/round per node
4. **Ideal MAC**: No collisions, no retransmissions
5. **Homogeneous nodes**: Same initial energy, same hardware

See `LIMITATIONS.md` for detailed discussion.