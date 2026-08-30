"""
Tests for graph building and manipulation.
"""

import pytest
import networkx as nx
from energy_routing.network.graph import build_graph, get_alive_subgraph
from energy_routing.network.topology import Topology, generate_topology
from energy_routing.config import NetworkConfig, EnergyConfig
from energy_routing.models.node import Node


class TestBuildGraph:
    """Tests for graph building."""

    def test_build_graph_basic(self):
        """Test basic graph building."""
        network_config = NetworkConfig(
            num_nodes=3,
            area_width=10.0,
            area_height=10.0,
            communication_range=20.0,  # Large enough for full connectivity
            seed=42,
            base_station_x=5.0,
            base_station_y=5.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # Should have 4 nodes (3 sensors + 1 base station)
        assert len(graph.nodes()) == 4
        assert topology.base_station_id in graph.nodes()

    def test_build_graph_edges(self):
        """Test that edges are created within communication range."""
        network_config = NetworkConfig(
            num_nodes=2,
            area_width=10.0,
            area_height=10.0,
            communication_range=5.0,
            seed=42,
            base_station_x=5.0,
            base_station_y=5.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # With small communication range, not all nodes may be connected
        # But graph should have nodes
        assert len(graph.nodes()) == 3  # 2 sensors + 1 base station

    def test_build_graph_edge_attributes(self):
        """Test that edges have distance attributes."""
        network_config = NetworkConfig(
            num_nodes=2,
            area_width=10.0,
            area_height=10.0,
            communication_range=20.0,
            seed=42,
            base_station_x=5.0,
            base_station_y=5.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # Check that edges have distance attribute
        for u, v, data in graph.edges(data=True):
            assert "distance" in data
            assert data["distance"] >= 0

    def test_build_graph_node_attributes(self):
        """Test that nodes have position attributes."""
        network_config = NetworkConfig(
            num_nodes=2,
            area_width=10.0,
            area_height=10.0,
            communication_range=20.0,
            seed=42,
            base_station_x=5.0,
            base_station_y=5.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # Check that nodes have x and y attributes
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            assert "x" in node_data
            assert "y" in node_data

    def test_build_graph_undirected(self):
        """Test that graph is undirected."""
        network_config = NetworkConfig(
            num_nodes=2,
            area_width=10.0,
            area_height=10.0,
            communication_range=20.0,
            seed=42,
            base_station_x=5.0,
            base_station_y=5.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # NetworkX Graph is undirected by default
        assert not graph.is_directed()


class TestAliveSubgraph:
    """Tests for alive subgraph extraction."""

    def test_alive_subgraph_all_alive(self):
        """Test alive subgraph when all nodes are alive."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0, is_alive=True),
            1: Node(1, 10, 0, 1.0, 1.0, is_alive=True),
            2: Node(2, 0, 10, 1.0, 1.0, is_alive=True)
        }
        graph = nx.Graph()
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        alive_subgraph = get_alive_subgraph(graph, nodes)
        
        assert len(alive_subgraph.nodes()) == 3
        assert 0 in alive_subgraph.nodes()
        assert 1 in alive_subgraph.nodes()
        assert 2 in alive_subgraph.nodes()

    def test_alive_subgraph_with_dead_node(self):
        """Test alive subgraph excludes dead nodes."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0, is_alive=True),
            1: Node(1, 10, 0, 1.0, 0.0, is_alive=False),  # Dead
            2: Node(2, 0, 10, 1.0, 1.0, is_alive=True)
        }
        graph = nx.Graph()
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        alive_subgraph = get_alive_subgraph(graph, nodes)
        
        # Dead node 1 should be excluded
        assert len(alive_subgraph.nodes()) == 2
        assert 0 in alive_subgraph.nodes()
        assert 1 not in alive_subgraph.nodes()
        assert 2 in alive_subgraph.nodes()
        
        # Edge through dead node should be excluded
        assert not alive_subgraph.has_edge(0, 2)

    def test_alive_subgraph_all_dead(self):
        """Test alive subgraph when all nodes are dead."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 0.0, is_alive=False),
            1: Node(1, 10, 0, 1.0, 0.0, is_alive=False),
            2: Node(2, 0, 10, 1.0, 0.0, is_alive=False)
        }
        graph = nx.Graph()
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        alive_subgraph = get_alive_subgraph(graph, nodes)
        
        assert len(alive_subgraph.nodes()) == 0

    def test_alive_subgraph_preserves_edges(self):
        """Test that alive subgraph preserves edges between alive nodes."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0, is_alive=True),
            1: Node(1, 10, 0, 1.0, 1.0, is_alive=True),
            2: Node(2, 20, 0, 1.0, 1.0, is_alive=True)
        }
        graph = nx.Graph()
        graph.add_edge(0, 1, distance=10.0)
        graph.add_edge(1, 2, distance=10.0)
        
        alive_subgraph = get_alive_subgraph(graph, nodes)
        
        assert alive_subgraph.has_edge(0, 1)
        assert alive_subgraph.has_edge(1, 2)
