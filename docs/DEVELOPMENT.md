# Development Guide

## Project Setup

### Prerequisites
- Python 3.12+
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd energy-aware-routing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .
```

### Project Structure

```
energy-aware-routing/
├── configs/              # YAML configuration files
├── docs/                 # Documentation
├── results/              # Simulation outputs (gitignored)
│   ├── raw/              # Individual run JSON
│   ├── summary/          # Aggregated summaries
│   └── plots/            # Visualization PNGs
├── src/energy_routing/   # Source code
│   ├── config.py         # Configuration dataclasses
│   ├── models/           # Domain models (Node, Packet, Result)
│   ├── network/          # Topology and graph
│   ├── routing/          # Routing algorithms
│   ├── simulation/       # Energy model and simulator
│   ├── metrics/          # Metrics collection
│   ├── experiments/      # Experiment runner and definitions
│   ├── visualization/    # Plotting
│   └── main.py           # CLI entry point
└── tests/                # Test suite
    ├── test_models/
    ├── test_network/
    ├── test_routing/
    ├── test_simulation/
    ├── test_metrics/
    ├── test_experiments/
    └── test_visualization/
```

## Development Workflow

### 1. Before Starting Work
```bash
# Check current status
git status

# Run full test suite
pytest tests/ -v

# Review implementation plan
cat IMPLEMENTATION_PLAN.md
```

### 2. Implementing a New Feature

#### Step 1: Read the Plan
Check `IMPLEMENTATION_PLAN.md` for the current stage requirements.

#### Step 2: Write Tests First (TDD)
```bash
# Create test file
touch tests/test_<module>/test_<feature>.py

# Write failing tests
# Run to confirm they fail
pytest tests/test_<module>/test_<feature>.py -v
```

#### Step 3: Implement Feature
```bash
# Create/modify source files in src/energy_routing/
# Run focused tests
pytest tests/test_<module>/test_<feature>.py -v
```

#### Step 4: Run Full Suite
```bash
pytest tests/ -v
```

#### Step 5: Verify Acceptance Criteria
Check stage requirements in `IMPLEMENTATION_PLAN.md`.

#### Step 6: Commit
```bash
git add .
git commit -m "Stage N: Description of changes"
```

### 3. Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_models/ -v
pytest tests/test_network/ -v
pytest tests/test_routing/ -v
pytest tests/test_simulation/ -v
pytest tests/test_metrics/ -v
pytest tests/test_experiments/ -v
pytest tests/test_visualization/ -v

# Specific test file
pytest tests/test_models/test_node.py -v

# Specific test
pytest tests/test_models/test_node.py::TestNodeCreation::test_node_creation_with_defaults -v

# With coverage
pytest tests/ --cov=energy_routing --cov-report=term-missing
```

### 4. Running Simulations

```bash
# Single simulation
python -m energy_routing.main run --config configs/base.yaml

# Experiment
python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml

# List experiments
python -m energy_routing.main list-experiments
```

### 5. Code Quality

#### Type Hints
All code should have type hints:
```python
def function(param: Type) -> ReturnType:
    ...
```

#### Docstrings
All public classes and functions need docstrings:
```python
def function(param: Type) -> ReturnType:
    """
    Brief description.
    
    Args:
        param: Description
        
    Returns:
        Description
        
    Raises:
        ExceptionType: When...
    """
```

#### Imports
Use absolute imports:
```python
from energy_routing.models.node import Node
from energy_routing.config import NetworkConfig
```

## Architecture Rules (Must Preserve)

1. **Routing strategies interchangeable** - Use `RoutingStrategy` ABC
2. **Energy model replaceable** - Use `EnergyModel` class
3. **Simulator no hard-coded routing** - Dependency injection
4. **Visualization separate** - No simulation control in visualization
5. **Experiments don't modify internals** - Clean API boundaries
6. **Domain models independent** - Pure dataclasses, no simulation logic
7. **No circular imports** - Strict layering
8. **Configuration centralized** - `SimulationSettings` root object
9. **Topology structurally static** - Dead nodes marked, not removed
10. **Dead nodes by state** - `is_alive` flag, excluded from routing
11. **Packet paths immutable** - `Tuple[int, ...]`, use `dataclasses.replace()`
12. **Deterministic** - Same seed → same results

## Critical Implementation Rules

### Energy Accounting (3 Cases - MUST IMPLEMENT EXACTLY)
```python
# Case 1: Failed before TX
if not node.can_transmit(tx_cost):
    return False  # NO TX, NO RX

# Case 2 & 3: TX consumed
node.consume_energy(tx_cost)

# Case 2: Dead receiver
if not receiver.is_alive:
    return False  # TX consumed, RX NOT

# Case 3: Successful RX
receiver.consume_energy(rx_cost)
return True  # Both consumed
```

### Base Station Handling
```python
# Never do: inf / inf
# Always handle explicitly:
if node.initial_energy == float('inf'):
    return 1.0  # Normalized energy = 1.0
```

### Packet Immutability
```python
# CORRECT - use dataclasses.replace
new_packet = packet.with_status(PacketStatus.DELIVERED)
new_packet = packet.with_path((0, 1, 2))

# WRONG - mutating frozen dataclass
packet.status = PacketStatus.DELIVERED  # AttributeError!
packet.path = [0, 1, 2]  # TypeError!
```

### Metrics
- Simulator explicitly provides: packets_generated, packets_delivered, packets_lost
- MetricsCollector must NOT infer counts indirectly
- FND/HND/LND definitions:
  - FND: First round with >=1 dead sensor node
  - HND: First round with alive <= floor(N/2)
  - LND: First round with all sensor nodes dead
  - None if never occurs

## Adding a New Routing Algorithm

1. Create new file in `routing/` (e.g., `my_routing.py`)
2. Implement `RoutingStrategy` ABC:
```python
from energy_routing.routing.base import RoutingStrategy

class MyRouting(RoutingStrategy):
    def find_path(self, graph, nodes, source, destination) -> Tuple[int, ...]:
        # Your algorithm
        return path_tuple
```
3. Add to factory in `routing/__init__.py`:
```python
def create_routing_strategy(algorithm: str, **kwargs):
    if algorithm == "my_routing":
        from energy_routing.routing.my_routing import MyRouting
        return MyRouting(**kwargs)
    ...
```
4. Add to `RoutingConfig.algorithm` Literal type in `config.py`
5. Write tests in `tests/test_routing/`

## Adding a New Experiment

1. Add function in `experiments/definitions.py`:
```python
def create_my_experiment() -> Experiment:
    return Experiment(
        name="my_experiment",
        description="Description",
        base_settings=get_base_settings(),
        parameter_variations={...},
        fixed_parameters={...},
        num_seeds=5
    )
```
2. Register in `create_all_experiments()` and `EXPERIMENT_REGISTRY`
3. Write tests in `tests/test_experiments/`

## Debugging Tips

### Common Issues

1. **Import errors**: Check PYTHONPATH or install with `pip install -e .`
2. **Circular imports**: Check import graph; use TYPE_CHECKING for type-only imports
3. **Energy not depleting**: Verify `can_transmit` and `consume_energy` logic
4. **Packets not delivered**: Check graph connectivity, routing algorithm
5. **FND/HND/LND None**: May be correct if nodes don't die in simulation time
6. **Visualization not showing**: Use `matplotlib.use('Agg')` for headless

### Debug Commands

```bash
# Run single test with output
pytest tests/test_simulation/test_simulator.py::TestDeliverHopEnergyAccounting::test_case3_successful_tx_successful_rx -v -s

# Print all test names
pytest tests/ --collect-only

# Run with Python debugger
pytest tests/ --pdb

# Profile simulation
python -m cProfile -o profile.stats -m energy_routing.main run --config configs/base.yaml
```

## Git Workflow

### Branch Naming
- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `docs/<description>` - Documentation updates

### Commit Messages
```
Stage N: Brief description

- Detail 1
- Detail 2
```

### Before Committing
```bash
# Run tests
pytest tests/ -v

# Check diff
git diff

# Verify no unintended changes
git status
```

## Continuous Integration

The project uses pytest for testing. Ensure:
- All tests pass locally before pushing
- No hardcoded paths or environment-specific code
- Requirements files up to date

## Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Changelog updated
- [ ] Config files validated
- [ ] Example runs successful

## Useful Resources

- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [pytest Documentation](https://docs.pytest.org/en/stable/)