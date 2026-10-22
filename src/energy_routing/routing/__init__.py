"""
Routing module for Wireless Sensor Network simulation.

Provides routing strategy implementations and factory.
"""

from energy_routing.routing.base import RoutingStrategy, create_routing_strategy
from energy_routing.routing.shortest_path import ShortestPathRouting
from energy_routing.routing.energy_aware import EnergyAwareRouting

__all__ = [
    "RoutingStrategy",
    "create_routing_strategy",
    "ShortestPathRouting",
    "EnergyAwareRouting",
]