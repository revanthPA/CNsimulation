# Energy-Aware Routing Protocol for Wireless Sensor Networks

A Python-based simulator for comparing shortest-path and residual-energy-aware routing protocols in Wireless Sensor Networks (WSNs).

## Overview

This project implements a **software simulation** (no hardware required) to evaluate whether incorporating residual node energy into routing decisions increases network lifetime compared to conventional shortest-path routing.

## Core Features

- Random WSN topology generation with fixed base station
- First-order radio energy model
- Two routing strategies:
  - Shortest-path (Dijkstra)
  - Energy-aware (weighted cost: α·distance + β·energy)
- Packet generation and delivery simulation
- Node energy depletion and death tracking
- Comprehensive metric collection (FND, HND, LND, PDR, etc.)
- Experiment runner for controlled comparisons
- CSV/JSON result export
- Matplotlib visualizations
- CLI interface

## Research Question

> Does incorporating residual node energy into routing decisions increase wireless sensor network lifetime compared with shortest-path routing under identical simulation conditions?

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd energy-aware-routing

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### Run a Simulation

```bash
# Run single simulation
python -m energy_routing.main run --config configs/base.yaml

# Run routing comparison experiment
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml

# List available experiments
python -m energy_routing.main list-experiments
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests for specific module
pytest tests/test_models/ -v
```

## Project Structure

```
energy-aware-routing/
├── configs/              # Configuration files
├── docs/                # Documentation
├── results/             # Simulation results
├── src/energy_routing/  # Source code
│   ├── models/          # Domain models
│   ├── network/         # Network topology
│   ├── routing/         # Routing algorithms
│   ├── simulation/      # Simulation engine
│   ├── metrics/         # Metric collection
│   ├── experiments/     # Experiment execution
│   └── visualization/    # Plotting
└── tests/               # Automated tests
```

## Configuration

Configuration files are in YAML format. See `configs/base.yaml` for an example.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and module responsibilities
- [Algorithm](docs/ALGORITHM.md) - Routing algorithms and energy model
- [Experiments](docs/EXPERIMENTS.md) - Experiment design and hypotheses
- [Energy Model](docs/ENERGY_MODEL.md) - Energy consumption calculations
- [Limitations](docs/LIMITATIONS.md) - Model assumptions and limitations
- [Development](docs/DEVELOPMENT.md) - Development setup and guidelines

## Implementation Plan

See `IMPLEMENTATION_PLAN.md` for the complete engineering plan and `PLAN_REFERENCE.md` for mandatory rules on using the plan.

## License

MIT License

## Contributing

1. Read `IMPLEMENTATION_PLAN.md` and `PLAN_REFERENCE.md`
2. Follow the staged implementation approach
3. Run tests after every change
4. Ensure reproducibility (use fixed seeds)
5. Never fabricate results

## Key Principles

- **Reproducibility:** Fixed seeds, deterministic execution
- **Modularity:** Interchangeable routing, replaceable energy model
- **Fair Comparisons:** Identical conditions for algorithm comparisons
- **No Fabrication:** All results from actual simulation runs
