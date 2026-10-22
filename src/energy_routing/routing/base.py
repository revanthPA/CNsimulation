"""
Routing abstraction for Wireless Sensor Network simulation.

Defines the base interface for routing strategies.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import networkx as nx

from energy_routing.models.node import Node


class RoutingStrategy(ABC):
    """
    Abstract base class for routing strategies.
    
    All routing strategies must implement the find_path method.
    The strategy receives the alive subgraph and node information,
    and returns the next hop towards the destination.
    """
    
    @abstractmethod
    def find_path(
        self,
        graph: nx.Graph,
        nodes: dict,
        source: int,
        destination: int
    ) -> Tuple[int, ...]:
        """
        Find the complete path from source to destination.
        
        Args:
            graph: NetworkX graph containing only alive nodes
            nodes: Dictionary of all nodes (including dead ones)
            source: Source node ID
            destination: Destination node ID (typically base station)
            
        Returns:
            Tuple of node IDs representing the path from source to destination.
            Returns empty tuple if no path exists.
        """
        pass
    
    def get_next_hop(
        self,
        graph: nx.Graph,
        nodes: dict,
        current: int,
        destination: int
    ) -> Optional[int]:
        """
        Get the next hop from current node towards destination.
        
        Default implementation finds full path and returns second node.
        Can be overridden for more efficient single-hop decisions.
        
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


def create_routing_strategy(algorithm: str, **kwargs) -> RoutingStrategy:
    """
    Factory function to create routing strategy instances.
    
    Args:
        algorithm: Algorithm name ("shortest_path" or "energy_aware")
        **kwargs: Additional arguments for the strategy
        
    Returns:
        RoutingStrategy instance
        
    Raises:
        ValueError: If algorithm is unknown
    """
    if algorithm == "shortest_path":
        from energy_routing.routing.shortest_path import ShortestPathRouting
        return ShortestPathRouting()
    elif algorithm == "energy_aware":
        from energy_routing.routing.energy_aware import EnergyAwareRouting
        alpha = kwargs.get("alpha", 0.5)
        beta = kwargs.get("beta", 0.5)
        return EnergyAwareRouting(alpha=alpha, beta=beta)
    else:
        raise ValueError(f"Unknown routing algorithm: {algorithm}")