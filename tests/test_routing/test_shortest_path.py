"""
Tests for ShortestPathRouting.
"""

import pytest
import networkx as nx
from energy_routing.routing.shortest_path import ShortestPathRouting
from energy_routing.routing.base import create_routing_strategy
from energy_routing.models.node import Node
from energy_routing.network.topology import Topology, generate_topology
from energy_routing.network.graph import build_graph, get_alive_subgraph
from energy_routing.config import NetworkConfig, EnergyConfig


class TestShortestPathRouting:
    """Tests for ShortestPathRouting implementation."""

    def setup_method(self):
        """Set up a simple topology for testing."""
        self.network_config = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=50.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.topology = generate_topology(self.network_config, self.energy_config)
        self.graph = build_graph(self.topology, self.network_config.communication_range)
        self.routing = ShortestPathRouting()

    def test_find_path_direct_connection(self):
        """Test finding path when source and destination are directly connected."""
        # Use base station as destination
        source = 0
        destination = self.topology.base_station_id
        
        # Get alive subgraph (all nodes alive initially)
        alive_graph = get_alive_subgraph(self.graph, self.topology.nodes)
        
        path = self.routing.find_path(alive_graph, self.topology.nodes, source, destination)
        
        # Path should exist and start with source, end with destination
        assert len(path) >= 2
        assert path[0] == source
        assert path[-1] == destination

    def test_find_path_multi_hop(self):
        """Test finding path requiring multiple hops."""
        # Create a topology where nodes form a chain
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 0, 1.0, 1.0),
            2: Node(2, 20, 0, 1.0, 1.0),
            3: Node(3, 30, 0, 1.0, 1.0),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=100.0, height=100.0)
        
        # Build graph with range 15 (connects adjacent nodes only)
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        # Add edges: 0-1, 1-2, 2-3 (distance 10 each)
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        graph.add_edge(2, 3, distance=10.0)
        
        path = self.routing.find_path(graph, nodes, 0, 3)
        
        assert path == (0, 1, 2, 3)

    def test_find_path_no_path_exists(self):
        """Test when no path exists between source and destination."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 0, 1.0, 1.0),  # Too far from 0
            2: Node(2, 0, 100, 1.0, 1.0),  # base station, too far from 0
        }
        topology = Topology(nodes=nodes, base_station_id=2, width=200.0, height=200.0)
        
        # Build graph with range 50 (no connections possible)
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        # No edges added - nodes are isolated
        
        path = self.routing.find_path(graph, nodes, 0, 2)
        
        assert path == ()

    def test_find_path_source_not_in_graph(self):
        """Test when source node is not in graph."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 0, 1.0, 1.0),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=100.0, height=100.0)
        
        graph = nx.Graph()
        graph.add_node(1, x=10.0, y=0.0)  # Only base station in graph
        
        path = self.routing.find_path(graph, nodes, 0, 1)
        
        assert path == ()

    def test_find_path_destination_not_in_graph(self):
        """Test when destination node is not in graph."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 0, 1.0, 1.0),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=100.0, height=100.0)
        
        graph = nx.Graph()
        graph.add_node(0, x=0.0, y=0.0)  # Only source in graph
        
        path = self.routing.find_path(graph, nodes, 0, 1)
        
        assert path == ()

    def test_get_next_hop(self):
        """Test getting next hop from current position."""
        # Create chain: 0 -> 1 -> 2 -> 3 (base station)
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 0, 1.0, 1.0),
            2: Node(2, 20, 0, 1.0, 1.0),
            3: Node(3, 30, 0, 1.0, 1.0),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        graph.add_edge(2, 3, distance=10.0)
        
        # From node 0, next hop should be 1
        next_hop = self.routing.get_next_hop(graph, nodes, 0, 3)
        assert next_hop == 1
        
        # From node 1, next hop should be 2
        next_hop = self.routing.get_next_hop(graph, nodes, 1, 3)
        assert next_hop == 2
        
        # From node 2, next hop should be 3 (base station)
        next_hop = self.routing.get_next_hop(graph, nodes, 2, 3)
        assert next_hop == 3
        
        # From base station, no next hop
        next_hop = self.routing.get_next_hop(graph, nodes, 3, 3)
        assert next_hop is None

    def test_get_next_hop_no_path(self):
        """Test next hop when no path exists."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 0, 1.0, 1.0),  # base station, too far
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=200.0, height=200.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        # No edges
        
        next_hop = self.routing.get_next_hop(graph, nodes, 0, 1)
        assert next_hop is None

    def test_path_uses_shortest_distance(self):
        """Test that Dijkstra finds the path with minimum total distance."""
        # Create a diamond topology:
        #    0
        #   / \
        #  1   2
        #   \ /
        #    3 (base station)
        # Path 0-1-3: distance 10+10=20
        # Path 0-2-3: distance 10+10=20
        # Both equal, but let's make one shorter
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 5, 5, 1.0, 1.0),    # distance ~7.07 from 0
            2: Node(2, 15, 0, 1.0, 1.0),   # distance 15 from 0
            3: Node(3, 10, 10, 1.0, 1.0),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        # Distances:
        # 0-1: ~7.07
        # 1-3: ~7.07
        # 0-2: 15
        # 2-3: ~11.18
        # Path 0-1-3: ~14.14
        # Path 0-2-3: ~26.18
        graph.add_edge(0, 1, distance=7.07)
        graph.add_edge(1, 3, distance=7.07)
        graph.add_edge(0, 2, distance=15.0)
        graph.add_edge(2, 3, distance=11.18)
        
        path = self.routing.find_path(graph, nodes, 0, 3)
        
        # Should take shorter path 0-1-3
        assert path == (0, 1, 3)


class TestRoutingFactory:
    """Tests for the routing factory function."""

    def test_create_shortest_path_routing(self):
        """Test creating shortest path routing via factory."""
        routing = create_routing_strategy("shortest_path")
        assert isinstance(routing, ShortestPathRouting)

    def test_create_unknown_routing_raises(self):
        """Test that unknown algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Unknown routing algorithm: unknown"):
            create_routing_strategy("unknown")