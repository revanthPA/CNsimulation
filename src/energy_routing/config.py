"""
Configuration management for the Energy-Aware Routing Protocol simulator.

Uses dataclasses for type-safe configuration with validation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
import math


@dataclass
class NetworkConfig:
    """
    Network topology configuration.
    
    Attributes:
        num_nodes: Number of sensor nodes
        area_width: Width of the network area in meters
        area_height: Height of the network area in meters
        communication_range: Maximum transmission distance in meters
        seed: Random seed for reproducibility
        base_station_x: X-coordinate of the base station in meters
        base_station_y: Y-coordinate of the base station in meters
        topology: Type of topology generation (currently only "random")
    """
    num_nodes: int
    area_width: float  # meters
    area_height: float  # meters
    communication_range: float  # meters
    seed: int
    base_station_x: float  # meters
    base_station_y: float  # meters
    topology: Literal["random"] = "random"

    def __post_init__(self):
        """Validate network configuration."""
        if self.num_nodes <= 0:
            raise ValueError("num_nodes must be > 0")
        if self.area_width <= 0 or self.area_height <= 0:
            raise ValueError("area dimensions must be > 0")
        if self.communication_range <= 0:
            raise ValueError("communication_range must be > 0")
        if self.seed < 0:
            raise ValueError("seed must be >= 0")
        if not 0 <= self.base_station_x <= self.area_width:
            raise ValueError("base_station_x must be within the network area")
        if not 0 <= self.base_station_y <= self.area_height:
            raise ValueError("base_station_y must be within the network area")


@dataclass
class EnergyConfig:
    """
    Energy model configuration.
    
    Attributes:
        initial_energy: Initial energy per node in Joules
        E_elec: Energy for transmitter/receiver electronics in nJ/bit
        E_amp: Energy for transmit amplifier in nJ/bit/m^2
        packet_size: Size of each packet in bytes
    """
    initial_energy: float  # Joules
    E_elec: float  # nJ/bit
    E_amp: float  # nJ/bit/m^2
    packet_size: int  # bytes

    def __post_init__(self):
        """Validate energy configuration."""
        if self.initial_energy <= 0:
            raise ValueError("initial_energy must be > 0")
        if self.E_elec < 0 or self.E_amp < 0:
            raise ValueError("Energy parameters must be >= 0")
        if self.packet_size <= 0:
            raise ValueError("packet_size must be > 0")


@dataclass
class SimulationParameters:
    """
    Simulation execution configuration.
    
    Attributes:
        num_rounds: Number of simulation rounds
        packets_per_round: Number of packets generated per node per round
        packet_size: Size of each packet in bytes
    """
    num_rounds: int
    packets_per_round: int  # packets per node per round
    packet_size: int  # bytes

    def __post_init__(self):
        """Validate simulation configuration."""
        if self.num_rounds <= 0:
            raise ValueError("num_rounds must be > 0")
        if self.packets_per_round < 0:
            raise ValueError("packets_per_round must be >= 0")
        if self.packet_size <= 0:
            raise ValueError("packet_size must be > 0")


@dataclass
class RoutingConfig:
    """
    Routing algorithm configuration.
    
    Attributes:
        algorithm: Routing algorithm to use ("shortest_path" or "energy_aware")
        alpha: Distance weight for energy-aware routing (0 <= alpha <= 1)
        beta: Energy weight for energy-aware routing (0 <= beta <= 1)
    """
    algorithm: Literal["shortest_path", "energy_aware"]
    alpha: float  # distance weight
    beta: float  # energy weight

    def __post_init__(self):
        """Validate routing configuration."""
        if self.algorithm not in ("shortest_path", "energy_aware"):
            raise ValueError("algorithm must be 'shortest_path' or 'energy_aware'")
        if self.alpha < 0 or self.alpha > 1:
            raise ValueError("alpha must be in [0, 1]")
        if self.beta < 0 or self.beta > 1:
            raise ValueError("beta must be in [0, 1]")
        if not math.isclose(self.alpha + self.beta, 1.0, abs_tol=1e-9):
            raise ValueError("alpha + beta must equal 1.0")


@dataclass
class OutputConfig:
    """
    Output configuration.
    
    Attributes:
        results_dir: Directory to store results
        save_results: Whether to save results to files
        generate_plots: Whether to generate visualizations
        plot_format: Format for plot files ("png", "svg", or "pdf")
    """
    results_dir: str = "results"
    save_results: bool = True
    generate_plots: bool = True
    plot_format: Literal["png", "svg", "pdf"] = "png"


@dataclass
class SimulationSettings:
    """
    ROOT CONFIG: Complete simulation settings.
    
    Contains all sub-configurations for a complete simulation setup.
    
    Attributes:
        network: Network topology configuration
        energy: Energy model configuration
        simulation: Simulation execution configuration
        routing: Routing algorithm configuration
        output: Output configuration
    """
    network: NetworkConfig
    energy: EnergyConfig
    simulation: SimulationParameters
    routing: RoutingConfig
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(config_path: str) -> SimulationSettings:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        SimulationSettings dataclass instance
        
    Raises:
        ValueError: If config is invalid
        FileNotFoundError: If file doesn't exist
    """
    import yaml
    from pathlib import Path
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    return settings_from_dict(config_data)


def settings_from_dict(config_data: Dict[str, Any]) -> SimulationSettings:
    """Validate and build settings from a parsed YAML/JSON mapping."""
    if not isinstance(config_data, dict):
        raise ValueError("Configuration must be a YAML mapping with network, energy, simulation, and routing sections.")
    required = ("network", "energy", "simulation", "routing")
    missing = [section for section in required if section not in config_data]
    if missing:
        raise ValueError(f"Configuration is missing required section(s): {', '.join(missing)}.")
    try:
        return SimulationSettings(
        network=NetworkConfig(**config_data["network"]),
        energy=EnergyConfig(**config_data["energy"]),
        simulation=SimulationParameters(**config_data["simulation"]),
        routing=RoutingConfig(**config_data["routing"]),
        output=OutputConfig(**config_data.get("output", {}))
        )
    except (TypeError, KeyError) as error:
        raise ValueError(f"Configuration fields are invalid: {error}") from error


def settings_to_dict(settings: SimulationSettings) -> Dict[str, Dict[str, Any]]:
    """Return a plain, serializable mapping of all effective settings."""
    return {
        "network": dict(settings.network.__dict__),
        "energy": dict(settings.energy.__dict__),
        "simulation": dict(settings.simulation.__dict__),
        "routing": dict(settings.routing.__dict__),
        "output": dict(settings.output.__dict__),
    }


def save_config(settings: SimulationSettings, output_path: str):
    """
    Save configuration to YAML file.
    
    Args:
        settings: SimulationSettings to save
        output_path: Path to output YAML file
    """
    import yaml
    
    with open(output_path, "w") as f:
        yaml.safe_dump(settings_to_dict(settings), f, default_flow_style=False, sort_keys=False)
