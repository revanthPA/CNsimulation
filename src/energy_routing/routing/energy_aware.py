"""
Energy-aware routing for Wireless Sensor Network simulation.

Implements routing based on weighted cost: α·distance + β·(1 - residual_energy).
Higher residual energy = lower energy cost = more preferred path.
"""

import math
import networkx as nx
from typing import Tuple, Dict

from energy_routing.routing.base import RoutingStrategy
from energy_routing.models.node import Node


class EnergyAwareRouting(RoutingStrategy):
    """
    Energy-aware routing using weighted cost function.
    
    Cost = α * (distance / max_distance) + β * (1 - normalized_residual_energy)
    
    Where:
    - α (alpha): weight for distance component (0 <= α <= 1)
    - β (beta): weight for energy component (0 <= β <= 1), α + β = 1
    - distance: Euclidean distance between nodes
    - normalized_residual_energy: remaining_energy / initial_energy (0 to 1)
      For base station (infinite energy): normalized_residual_energy = 1.0
    
    Both components are normalized to [0, 1] range for fair weighting.
    Lower residual energy increases the energy penalty, discouraging
    routes through depleted nodes.
    """
    
    def __init__(self, alpha: float = 0.5, beta: float = 0.5):
        """
        Initialize energy-aware routing.
        
        Args:
            alpha: Distance weight (0 <= alpha <= 1)
            beta: Weight for energy component (0 <= beta <= 1), alpha + beta = 1
            
        Raises:
            ValueError: If alpha or beta are out of range or don't sum to 1
        """
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be in [0, 1]")
        if not 0 <= beta <= 1:
            raise ValueError("beta must be in [0, 1]")
        if not math.isclose(alpha + beta, 1.0, abs_tol=1e-9):
            raise ValueError("alpha + beta must equal 1.0")
        
        self.alpha = alpha
        self.beta = beta
        # Cache for max edge distance, keyed by graph object.
        # Graph edge distances are static during simulation, so the cached
        # value remains valid as long as the same graph object is passed.
        # A single-entry cache is sufficient because the simulator reuses the
        # same alive subgraph for all packets within a round.
        self._cached_graph = None
        self._cached_max_distance = 0.0
    
    def _get_normalized_residual_energy(self, node: Node) -> float:
        """
        Get normalized residual energy for a node.
        
        For regular nodes: remaining_energy / initial_energy (clamped to [0, 1])
        For base station (infinite energy): returns 1.0 (always preferred)
        
        Args:
            node: Node to get energy for
            
        Returns:
            Normalized residual energy in [0, 1]
        """
        # Base station has infinite energy
        if node.initial_energy == float('inf') or node.remaining_energy == float('inf'):
            return 1.0
        
        if node.initial_energy <= 0:
            return 0.0
        
        # Normalize: remaining / initial, clamped to [0, 1]
        normalized = node.remaining_energy / node.initial_energy
        return max(0.0, min(1.0, normalized))
    
    def _get_max_distance(self, graph: nx.Graph) -> float:
        """
        Get the maximum edge distance in the graph, with caching.

        The maximum distance depends only on edge attributes, which are
        static during simulation. The cached value remains valid as long
        as the same graph object is passed, which is the case within a
        simulation round where the same alive subgraph is reused.

        Args:
            graph: NetworkX graph with distance edge attributes

        Returns:
            Maximum edge distance, or 0.0 if the graph has no edges
        """
        if graph is self._cached_graph:
            return self._cached_max_distance

        max_distance = 0.0
        for u, v, data in graph.edges(data=True):
            dist = data.get("distance", 0.0)
            if dist > max_distance:
                max_distance = dist

        self._cached_graph = graph
        self._cached_max_distance = max_distance
        return max_distance

    def _calculate_edge_cost(
        self,
        graph: nx.Graph,
        nodes: Dict[int, Node],
        u: int,
        v: int,
        max_distance: float
    ) -> float:
        """
        Calculate weighted cost for an edge.
        
        Cost = α * (distance / max_distance) + β * (1 - normalized_residual_energy)
        
        Args:
            graph: NetworkX graph
            nodes: Dictionary of all nodes
            u: Source node ID
            v: Target node ID
            max_distance: Maximum communication range (for distance normalization)
            
        Returns:
            Weighted cost for the edge. Both components are in [0, 1],
            so the total cost is in [0, 1] when α + β = 1.
        """
        # Get distance from graph edge attribute
        distance = graph[u][v].get("distance", 0.0)
        
        # Normalize distance to [0, 1]
        if max_distance > 0:
            normalized_distance = distance / max_distance
        else:
            normalized_distance = 0.0
        
        # Get normalized residual energy of the TARGET node (receiver)
        # We care about the energy of the node we're transmitting TO
        target_node = nodes[v]
        normalized_energy = self._get_normalized_residual_energy(target_node)
        
        # Energy penalty: linear in [0, 1]. Lower residual energy = higher penalty.
        # A fully depleted node (energy = 0) has penalty 1.0 (maximum).
        # A fully charged node (energy = 1.0) has penalty 0.0 (minimum).
        # Base station has normalized_energy = 1.0 → penalty 0.0 (always preferred).
        energy_cost = 1.0 - normalized_energy
        
        # Weighted combination
        cost = self.alpha * normalized_distance + self.beta * energy_cost
        
        return cost
    
    def find_path(
        self,
        graph: nx.Graph,
        nodes: Dict[int, Node],
        source: int,
        destination: int
    ) -> Tuple[int, ...]:
        """
        Find the minimum-cost path from source to destination.
        
        Uses Dijkstra's algorithm with custom edge weights based on
        distance and residual energy.
        
        Args:
            graph: NetworkX graph containing only alive nodes
            nodes: Dictionary of all nodes
            source: Source node ID
            destination: Destination node ID (typically base station)
            
        Returns:
            Tuple of node IDs representing the minimum-cost path.
            Returns empty tuple if no path exists.
        """
        # Check if both nodes exist in the graph
        if source not in graph or destination not in graph:
            return ()
        
        # Get max distance for normalization (communication range)
        # Cached per graph object; edge distances are static during simulation
        max_distance = self._get_max_distance(graph)
        
        # If no edges, can't route
        if max_distance == 0.0:
            return ()
        
        try:
            # Use Dijkstra with custom weight function
            path = nx.dijkstra_path(
                graph,
                source=source,
                target=destination,
                weight=lambda u, v, d: self._calculate_edge_cost(graph, nodes, u, v, max_distance)
            )
            return tuple(path)
        except nx.NetworkXNoPath:
            return ()
        except nx.NodeNotFound:
            return ()
    
    def get_next_hop(
        self,
        graph: nx.Graph,
        nodes: Dict[int, Node],
        current: int,
        destination: int
    ) -> int | None:
        """
        Get the next hop towards destination using energy-aware cost.
        
        Args:
            graph: NetworkX graph containing only alive nodes
            nodes: Dictionary of all nodes
            current: Current node ID
            destination: Destination node ID
            
        Returns:
            Next hop node ID, or None if no path exists
        """
        path = self.find_path(graph, nodes, current, destination)
        if len(path) >= 2:
            return path[1]
        return None