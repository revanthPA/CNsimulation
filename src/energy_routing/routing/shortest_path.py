"""
Shortest-path routing for Wireless Sensor Network simulation.

Implements Dijkstra's algorithm for finding shortest paths based on Euclidean distance.
"""

import networkx as nx
from typing import Tuple, Dict

from energy_routing.routing.base import RoutingStrategy
from energy_routing.models.node import Node


class ShortestPathRouting(RoutingStrategy):
    """
    Shortest-path routing using Dijkstra's algorithm.
    
    Finds the path with minimum total Euclidean distance from source to destination.
    Uses NetworkX's built-in Dijkstra implementation.
    """
    
    def find_path(
        self,
        graph: nx.Graph,
        nodes: Dict[int, Node],
        source: int,
        destination: int
    ) -> Tuple[int, ...]:
        """
        Find the shortest path from source to destination using Dijkstra's algorithm.
        
        Args:
            graph: NetworkX graph containing only alive nodes
            nodes: Dictionary of all nodes (for position lookup)
            source: Source node ID
            destination: Destination node ID (typically base station)
            
        Returns:
            Tuple of node IDs representing the shortest path.
            Returns empty tuple if no path exists.
        """
        # Check if both nodes exist in the graph
        if source not in graph or destination not in graph:
            return ()
        
        try:
            # Use NetworkX's Dijkstra path finding with distance as weight
            path = nx.dijkstra_path(
                graph,
                source=source,
                target=destination,
                weight="distance"
            )
            return tuple(path)
        except nx.NetworkXNoPath:
            # No path exists between source and destination
            return ()
        except nx.NodeNotFound:
            # One of the nodes doesn't exist in the graph
            return ()
    
    def get_next_hop(
        self,
        graph: nx.Graph,
        nodes: Dict[int, Node],
        current: int,
        destination: int
    ) -> int | None:
        """
        Get the next hop towards destination using shortest path.
        
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