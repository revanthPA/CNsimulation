"""
Network module for Wireless Sensor Network simulation.

Contains:
- Topology generation
- Graph representation
"""

from .topology import Topology, generate_topology
from .graph import build_graph, get_alive_subgraph

__all__ = ["Topology", "generate_topology", "build_graph", "get_alive_subgraph"]
