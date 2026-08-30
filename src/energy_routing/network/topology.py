"""
Topology generation for Wireless Sensor Network simulation.

Generates node positions and manages the network layout.
"""

import random
from dataclasses import dataclass
from typing import Dict

from energy_routing.models.node import Node
from energy_routing.config import NetworkConfig, EnergyConfig


@dataclass
class Topology:
    """
    Represents the physical layout of nodes in the Wireless Sensor Network.
    
    Attributes:
        nodes: Dictionary mapping node_id to Node
        base_station_id: ID of the base station node
        width: Width of the network area in meters
        height: Height of the network area in meters
    """
    nodes: Dict[int, Node]
    base_station_id: int
    width: float
    height: float


def generate_topology(
    network_config: NetworkConfig,
    energy_config: EnergyConfig
) -> Topology:
    """
    Generate a random WSN topology.
    
    The topology is STATIC - it does not change during simulation.
    Dead nodes are represented by is_alive=False, not by removal from the topology.
    
    Args:
        network_config: Network configuration
        energy_config: Energy configuration
        
    Returns:
        Topology with nodes and base station
    """
    random.seed(network_config.seed)
    nodes = {}

    # Generate sensor nodes
    for node_id in range(network_config.num_nodes):
        x = random.uniform(0, network_config.area_width)
        y = random.uniform(0, network_config.area_height)
        nodes[node_id] = Node(
            node_id=node_id,
            x=x,
            y=y,
            initial_energy=energy_config.initial_energy,
            remaining_energy=energy_config.initial_energy
        )

    # Base station (infinite energy, never dies, fixed position)
    base_station_id = network_config.num_nodes
    nodes[base_station_id] = Node(
        node_id=base_station_id,
        x=network_config.base_station_x,
        y=network_config.base_station_y,
        initial_energy=float('inf'),
        remaining_energy=float('inf'),
        is_alive=True
    )

    return Topology(
        nodes=nodes,
        base_station_id=base_station_id,
        width=network_config.area_width,
        height=network_config.area_height
    )
