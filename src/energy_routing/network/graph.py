"""
Graph representation for Wireless Sensor Network simulation.

Builds and maintains the NetworkX graph representation of the network.
"""

import math
from typing import Dict
import networkx as nx

from energy_routing.models.node import Node
from energy_routing.network.topology import Topology


def build_graph(
    topology: Topology,
    communication_range: float
) -> nx.Graph:
    """
    Build a NetworkX graph from the topology.
    
    The graph is STATIC - its structure does not change during simulation.
    Dead nodes are handled by excluding them from pathfinding via get_alive_subgraph().
    
    Args:
        topology: Node positions and base station
        communication_range: Maximum transmission distance in meters
        
    Returns:
        NetworkX Graph with edges where distance <= communication_range
    """
    graph = nx.Graph()
    nodes = topology.nodes

    # Add all nodes with positions
    for node_id, node in nodes.items():
        graph.add_node(node_id, x=node.x, y=node.y)

    # Add edges between nodes within communication range
    node_ids = list(nodes.keys())
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            u = node_ids[i]
            v = node_ids[j]
            distance = math.dist(
                (nodes[u].x, nodes[u].y),
                (nodes[v].x, nodes[v].y)
            )
            if distance <= communication_range:
                graph.add_edge(u, v, distance=distance)

    return graph


def get_alive_subgraph(
    graph: nx.Graph,
    nodes: Dict[int, Node]
) -> nx.Graph:
    """
    Get subgraph containing only alive nodes.
    
    Used for routing to exclude dead nodes from pathfinding.
    The original graph remains unchanged (topology is static).
    
    Args:
        graph: Full network graph
        nodes: Dictionary of all nodes
        
    Returns:
        Subgraph with only alive nodes
    """
    alive_nodes = [nid for nid, node in nodes.items() if node.is_alive]
    return graph.subgraph(alive_nodes)
