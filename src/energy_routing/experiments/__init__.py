"""
Experiments module for Wireless Sensor Network simulation.

Contains:
- Experiment and ExperimentRunner classes
- Experiment definitions and registry
"""

from energy_routing.experiments.runner import Experiment, ExperimentRunner
from energy_routing.experiments.definitions import (
    get_base_settings,
    create_routing_comparison_experiment,
    create_network_size_experiment,
    create_energy_aware_params_experiment,
    create_communication_range_experiment,
    create_initial_energy_experiment,
    create_all_experiments,
    get_experiment,
    list_experiments,
    EXPERIMENT_REGISTRY
)

__all__ = [
    "Experiment",
    "ExperimentRunner",
    "get_base_settings",
    "create_routing_comparison_experiment",
    "create_network_size_experiment",
    "create_energy_aware_params_experiment",
    "create_communication_range_experiment",
    "create_initial_energy_experiment",
    "create_all_experiments",
    "get_experiment",
    "list_experiments",
    "EXPERIMENT_REGISTRY",
]