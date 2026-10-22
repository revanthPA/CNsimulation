"""
Tests for EnergyAwareRouting.
"""

import pytest
import networkx as nx
import math
from energy_routing.routing.energy_aware import EnergyAwareRouting
from energy_routing.routing.base import create_routing_strategy
from energy_routing.models.node import Node
from energy_routing.network.topology import Topology
from energy_routing.config import NetworkConfig, EnergyConfig


class TestEnergyAwareRouting:
    """Tests for EnergyAwareRouting implementation."""

    def setup_method(self):
        """Set up a simple topology for testing."""
        self.routing = EnergyAwareRouting(alpha=0.5, beta=0.5)

    def test_initialization_valid_params(self):
        """Test initialization with valid alpha and beta."""
        routing = EnergyAwareRouting(alpha=0.3, beta=0.7)
        assert routing.alpha == 0.3
        assert routing.beta == 0.7
        
        routing = EnergyAwareRouting(alpha=1.0, beta=0.0)
        assert routing.alpha == 1.0
        assert routing.beta == 0.0
        
        routing = EnergyAwareRouting(alpha=0.0, beta=1.0)
        assert routing.alpha == 0.0
        assert routing.beta == 1.0

    def test_initialization_invalid_alpha(self):
        """Test that invalid alpha raises ValueError."""
        with pytest.raises(ValueError, match="alpha must be in \[0, 1\]"):
            EnergyAwareRouting(alpha=-0.1, beta=1.1)
        with pytest.raises(ValueError, match="alpha must be in \[0, 1\]"):
            EnergyAwareRouting(alpha=1.1, beta=-0.1)

    def test_initialization_invalid_beta(self):
        """Test that invalid beta raises ValueError."""
        with pytest.raises(ValueError, match="beta must be in \[0, 1\]"):
            EnergyAwareRouting(alpha=0.5, beta=-0.1)
        with pytest.raises(ValueError, match="beta must be in \[0, 1\]"):
            EnergyAwareRouting(alpha=0.5, beta=1.1)

    def test_initialization_sum_not_one(self):
        """Test that alpha + beta != 1 raises ValueError."""
        with pytest.raises(ValueError, match="alpha \\+ beta must equal 1.0"):
            EnergyAwareRouting(alpha=0.3, beta=0.3)
        with pytest.raises(ValueError, match="alpha \\+ beta must equal 1.0"):
            EnergyAwareRouting(alpha=0.6, beta=0.6)

    def test_normalized_residual_energy_regular_node(self):
        """Test normalized energy for regular node."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=0.5)
        energy = self.routing._get_normalized_residual_energy(node)
        assert energy == 0.5

    def test_normalized_residual_energy_full(self):
        """Test normalized energy for full energy node."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        energy = self.routing._get_normalized_residual_energy(node)
        assert energy == 1.0

    def test_normalized_residual_energy_empty(self):
        """Test normalized energy for depleted node."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=0.0)
        energy = self.routing._get_normalized_residual_energy(node)
        assert energy == 0.0

    def test_normalized_residual_energy_base_station(self):
        """Test normalized energy for base station (infinite energy)."""
        node = Node(1, 0, 0, initial_energy=float('inf'), remaining_energy=float('inf'))
        energy = self.routing._get_normalized_residual_energy(node)
        assert energy == 1.0

    def test_normalized_residual_energy_clamped(self):
        """Test that normalized energy is clamped to [0, 1]."""
        # Remaining > initial (shouldn't happen but test clamping)
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=2.0)
        energy = self.routing._get_normalized_residual_energy(node)
        assert energy == 1.0

    def test_find_path_prefers_higher_energy(self):
        """Test that routing prefers nodes with higher residual energy."""
        # Create topology:
        # Source (0) connects to two relays (1 and 2), both connect to base station (3)
        # Node 1: high energy (0.9), Node 2: low energy (0.1)
        # Distance is same for both paths
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),       # source
            1: Node(1, 10, 0, 1.0, 0.9),       # high energy relay
            2: Node(2, 10, 10, 1.0, 0.1),      # low energy relay
            3: Node(3, 20, 5, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        # All distances = 10 (simplified)
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(0, 2, distance=10.0)
        graph.add_edge(1, 3, distance=10.0)
        graph.add_edge(2, 3, distance=10.0)
        
        # With beta=0.5, should prefer node 1 (higher energy)
        path = self.routing.find_path(graph, nodes, 0, 3)
        
        # Path should go through node 1 (high energy)
        assert path == (0, 1, 3)

    def test_find_path_alpha_only(self):
        """Test routing with alpha=1.0 (distance only, same as shortest path)."""
        routing = EnergyAwareRouting(alpha=1.0, beta=0.0)
        
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 5, 0, 1.0, 0.1),    # close but low energy
            2: Node(2, 15, 0, 1.0, 0.9),   # far but high energy
            3: Node(3, 20, 0, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        graph.add_edge(0, 1, distance=5.0)
        graph.add_edge(1, 3, distance=15.0)  # total 20
        graph.add_edge(0, 2, distance=15.0)
        graph.add_edge(2, 3, distance=5.0)   # total 20
        
        # Both paths have same total distance, so either is valid
        path = routing.find_path(graph, nodes, 0, 3)
        assert len(path) >= 2
        assert path[0] == 0
        assert path[-1] == 3

    def test_find_path_beta_only(self):
        """Test routing with beta=1.0 (energy only)."""
        routing = EnergyAwareRouting(alpha=0.0, beta=1.0)
        
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 0, 1.0, 0.9),  # far but high energy
            2: Node(2, 5, 0, 1.0, 0.1),    # close but low energy
            3: Node(3, 105, 0, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=3, width=200.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        graph.add_edge(0, 1, distance=100.0)
        graph.add_edge(1, 3, distance=5.0)
        graph.add_edge(0, 2, distance=5.0)
        graph.add_edge(2, 3, distance=100.0)
        
        # Should prefer node 1 (high energy) despite longer distance
        path = routing.find_path(graph, nodes, 0, 3)
        assert path == (0, 1, 3)

    def test_find_path_no_path_exists(self):
        """Test when no path exists."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 100, 1.0, 1.0),  # base station, isolated
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=200.0, height=200.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        # No edges
        
        path = self.routing.find_path(graph, nodes, 0, 1)
        assert path == ()

    def test_find_path_handles_base_station_infinite_energy(self):
        """Test that base station infinite energy doesn't cause inf/inf issues."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 0.5),
            1: Node(1, 10, 0, 1.0, 0.5),
            2: Node(2, 20, 0, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=2, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        # Should find path without math errors
        path = self.routing.find_path(graph, nodes, 0, 2)
        assert path == (0, 1, 2)

    def test_get_next_hop(self):
        """Test getting next hop."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 0, 1.0, 0.9),
            2: Node(2, 20, 0, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=2, width=100.0, height=100.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        next_hop = self.routing.get_next_hop(graph, nodes, 0, 2)
        assert next_hop == 1
        
        next_hop = self.routing.get_next_hop(graph, nodes, 1, 2)
        assert next_hop == 2

    def test_get_next_hop_no_path(self):
        """Test next hop when no path exists."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 100, float('inf'), float('inf')),
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=200.0, height=200.0)
        
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        # No edges
        
        next_hop = self.routing.get_next_hop(graph, nodes, 0, 1)
        assert next_hop is None


class TestRoutingFactoryEnergyAware:
    """Tests for the routing factory with energy-aware routing."""

    def test_create_energy_aware_routing(self):
        """Test creating energy aware routing via factory."""
        routing = create_routing_strategy("energy_aware", alpha=0.3, beta=0.7)
        assert isinstance(routing, EnergyAwareRouting)
        assert routing.alpha == 0.3
        assert routing.beta == 0.7

    def test_create_energy_aware_routing_defaults(self):
        """Test creating energy aware routing with defaults."""
        routing = create_routing_strategy("energy_aware")
        assert isinstance(routing, EnergyAwareRouting)
        assert routing.alpha == 0.5
        assert routing.beta == 0.5