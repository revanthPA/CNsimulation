"""
Experiment definitions for Wireless Sensor Network simulation.

Defines standard experiments for the project.
"""

from typing import Dict, List, Any
from energy_routing.experiments.runner import Experiment
from energy_routing.config import (
    SimulationSettings, NetworkConfig, EnergyConfig,
    SimulationParameters, RoutingConfig, OutputConfig
)


def get_base_settings() -> SimulationSettings:
    """Get the base simulation settings from the plan."""
    return SimulationSettings(
        network=NetworkConfig(
            num_nodes=50,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0,
            topology="random"
        ),
        energy=EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        ),
        simulation=SimulationParameters(
            num_rounds=1000,
            packets_per_round=1,
            packet_size=512
        ),
        routing=RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        ),
        output=OutputConfig(
            results_dir="results",
            save_results=True,
            generate_plots=True,
            plot_format="png"
        )
    )


def create_routing_comparison_experiment() -> Experiment:
    """
    Create the main routing comparison experiment.
    
    Compares shortest_path vs energy_aware (alpha=0.5, beta=0.5)
    using 5 seeds for statistical significance.
    Uses SAME topology for each seed pair (fair comparison).
    """
    base = get_base_settings()
    
    return Experiment(
        name="routing_comparison",
        description="Compare shortest-path vs energy-aware routing (5 seeds, alpha=0.5, beta=0.5)",
        base_settings=base,
        num_seeds=5,
        seed_offset=0,
        fixed_parameters={
            "routing.alpha": 0.5,
            "routing.beta": 0.5
        }
    )


def create_network_size_experiment() -> Experiment:
    """
    Create network size scaling experiment.
    
    Tests different network sizes with same base seed.
    Each size generates a DIFFERENT topology (as per plan).
    """
    base = get_base_settings()
    
    return Experiment(
        name="network_size",
        description="Network size scaling: 20, 50, 100, 200 nodes (same seed, different topologies)",
        base_settings=base,
        parameter_variations={
            "network.num_nodes": [20, 50, 100, 200]
        },
        num_seeds=1,
        seed_offset=0,
        fixed_parameters={
            "routing.algorithm": "shortest_path",
            "routing.alpha": 0.5,
            "routing.beta": 0.5
        }
    )


def create_energy_aware_params_experiment() -> Experiment:
    """
    Create energy-aware parameter sweep experiment.
    
    Tests different alpha/beta combinations for energy-aware routing.
    Uses paired (alpha, beta) values that sum to 1.0.
    """
    base = get_base_settings()
    
    # Use paired parameter variations - each entry is a tuple of (alpha, beta)
    alpha_beta_pairs = [
        (0.0, 1.0),   # Pure energy-aware (beta=1)
        (0.25, 0.75),
        (0.5, 0.5),   # Balanced
        (0.75, 0.25),
        (1.0, 0.0),   # Pure shortest-path (alpha=1)
    ]
    
    return Experiment(
        name="energy_aware_params",
        description="Energy-aware parameter sweep: alpha=0.0, 0.25, 0.5, 0.75, 1.0 (paired with beta)",
        base_settings=base,
        parameter_variations={
            "routing.alpha_beta_pair": alpha_beta_pairs
        },
        num_seeds=3,
        seed_offset=100,
        fixed_parameters={
            "routing.algorithm": "energy_aware"
        }
    )


def create_communication_range_experiment() -> Experiment:
    """
    Create communication range experiment.
    
    Tests different communication ranges.
    """
    base = get_base_settings()
    
    return Experiment(
        name="communication_range",
        description="Communication range scaling: 15, 20, 25, 30 meters",
        base_settings=base,
        parameter_variations={
            "network.communication_range": [15.0, 20.0, 25.0, 30.0]
        },
        num_seeds=3,
        seed_offset=200,
        fixed_parameters={
            "routing.algorithm": "shortest_path"
        }
    )


def create_initial_energy_experiment() -> Experiment:
    """
    Create initial energy scaling experiment.
    
    Tests different initial energy levels.
    """
    base = get_base_settings()
    
    return Experiment(
        name="initial_energy",
        description="Initial energy scaling: 0.5, 1.0, 2.0, 5.0 Joules",
        base_settings=base,
        parameter_variations={
            "energy.initial_energy": [0.5, 1.0, 2.0, 5.0]
        },
        num_seeds=3,
        seed_offset=300,
        fixed_parameters={
            "routing.algorithm": "shortest_path"
        }
    )


def create_all_experiments() -> Dict[str, Experiment]:
    """
    Create all standard experiments.
    
    Returns:
        Dictionary mapping experiment names to Experiment objects
    """
    return {
        "routing_comparison": create_routing_comparison_experiment(),
        "network_size": create_network_size_experiment(),
        "energy_aware_params": create_energy_aware_params_experiment(),
        "communication_range": create_communication_range_experiment(),
        "initial_energy": create_initial_energy_experiment(),
    }


EXPERIMENT_REGISTRY = create_all_experiments()


def get_experiment(name: str) -> Experiment:
    """
    Get an experiment by name.
    
    Args:
        name: Experiment name
        
    Returns:
        Experiment object
        
    Raises:
        KeyError: If experiment not found
    """
    if name not in EXPERIMENT_REGISTRY:
        available = list(EXPERIMENT_REGISTRY.keys())
        raise KeyError(f"Unknown experiment: {name}. Available: {available}")
    return EXPERIMENT_REGISTRY[name]


def list_experiments() -> List[str]:
    """List all available experiment names."""
    return list(EXPERIMENT_REGISTRY.keys())