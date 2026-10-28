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

### Windows startup guide

For Python setup, the first dashboard launch, running simulations, comparisons, and troubleshooting, see [docs/STARTUP_GUIDE_WINDOWS.md](docs/STARTUP_GUIDE_WINDOWS.md). Once dependencies are installed, Windows users can double-click `start_dashboard.bat` to launch the dashboard.

### Interactive Web GUI (Streamlit)

A clean, interactive interface is provided to configure, run, compare, and visualize simulations without editing configuration files or operating the terminal:

```bash
# Launch directly with Streamlit (Recommended)
streamlit run src/energy_routing/dashboard.py

# Or via Python module
python -m streamlit run src/energy_routing/dashboard.py

# Or via the CLI launcher
python -m energy_routing.main gui

# Or using the run.sh wrapper (Linux / Mac / WSL)
./run.sh gui
```

The GUI consists of three main sections:
- **Section A — Run Simulation**: Configure node count, range, energy, rounds, seed, and routing algorithm (Shortest-Path or Energy-Aware with $\alpha$/$\beta$ weights). View key metrics (FND, HND, LND, PDR, packets, alive nodes) and operational curves.
- **Section B — Compare Algorithms**: Run paired comparisons across multiple seeds under identical topology and traffic conditions. View summary tables, per-seed win/tie/loss outcomes, and side-by-side charts.
- **Section C — View Previous Results**: Browse saved results from the `results/` directory or upload a result file to inspect configurations, metrics, and reconstructed charts.

New results from the GUI are saved automatically to `results/dashboard/single_runs/` and `results/dashboard/comparisons/` with unique timestamped filenames to prevent overwriting existing data.

### Quick Start (Recommended)

Use the `run.sh` convenience wrapper:

```bash
# Make it executable (one-time)
chmod +x run.sh

# Launch the interactive GUI
./run.sh gui

# Run a single simulation with default config
./run.sh run

# Run with a different config
./run.sh run configs/small.yaml

# Run the routing comparison experiment
./run.sh experiment

# List all available experiments
./run.sh list

# Run the full test suite
./run.sh test

# Show help
./run.sh help
```

### Manual Commands

If you prefer to run commands directly:

```bash
# Run single simulation
python -m energy_routing.main run --config configs/base.yaml

# Run routing comparison experiment
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml

# List available experiments
python -m energy_routing.main list-experiments

# Launch GUI
python -m energy_routing.main gui

# Run all tests
pytest tests/ -v
```

## Project Structure

```
energy-aware-routing/
├── configs/              # Configuration files
├── docs/                # Documentation
├── results/             # Simulation results
├── scripts/             # Utility scripts
│   └── sensitivity_study.py  # Robustness sensitivity study
├── src/energy_routing/  # Source code
│   ├── models/          # Domain models
│   ├── network/         # Network topology
│   ├── routing/         # Routing algorithms
│   ├── simulation/      # Simulation engine
│   ├── metrics/         # Metric collection
│   └── experiments/     # Experiment execution
├── tests/               # Automated tests
├── run.sh               # Convenience wrapper script
└── ...
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
