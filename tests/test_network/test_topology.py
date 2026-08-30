"""
Tests for topology generation.
"""

import pytest
from energy_routing.network.topology import Topology, generate_topology
from energy_routing.config import NetworkConfig, EnergyConfig
from energy_routing.models.node import Node


class TestTopologyGeneration:
    """Tests for topology generation."""

    def test_generate_topology_basic(self):
        """Test basic topology generation."""
        network_config = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        
        # Check number of nodes (5 sensors + 1 base station)
        assert len(topology.nodes) == 6
        assert topology.base_station_id == 5
        assert topology.width == 100.0
        assert topology.height == 100.0

    def test_generate_topology_base_station(self):
        """Test that base station has infinite energy."""
        network_config = NetworkConfig(
            num_nodes=3,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        base_station = topology.nodes[topology.base_station_id]
        
        assert base_station.initial_energy == float('inf')
        assert base_station.remaining_energy == float('inf')
        assert base_station.is_alive is True
        assert base_station.x == 50.0
        assert base_station.y == 50.0

    def test_generate_topology_sensor_nodes(self):
        """Test that sensor nodes have correct initial energy."""
        network_config = NetworkConfig(
            num_nodes=3,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        energy_config = EnergyConfig(
            initial_energy=2.5,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology = generate_topology(network_config, energy_config)
        
        # Check sensor nodes (0, 1, 2)
        for node_id in range(3):
            node = topology.nodes[node_id]
            assert node.initial_energy == 2.5
            assert node.remaining_energy == 2.5
            assert node.is_alive is True
            assert 0 <= node.x <= 100.0
            assert 0 <= node.y <= 100.0

    def test_generate_topology_deterministic(self):
        """Test that topology generation is deterministic with same seed."""
        network_config = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology1 = generate_topology(network_config, energy_config)
        topology2 = generate_topology(network_config, energy_config)
        
        # Node positions should be identical
        for node_id in range(5):  # Sensor nodes only
            node1 = topology1.nodes[node_id]
            node2 = topology2.nodes[node_id]
            assert node1.x == node2.x
            assert node1.y == node2.y

    def test_generate_topology_different_seeds(self):
        """Test that different seeds produce different topologies."""
        network_config1 = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        network_config2 = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=20.0,
            seed=43,
            base_station_x=50.0,
            base_station_y=50.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        topology1 = generate_topology(network_config1, energy_config)
        topology2 = generate_topology(network_config2, energy_config)
        
        # At least one node should have different position
        different = False
        for node_id in range(5):
            node1 = topology1.nodes[node_id]
            node2 = topology2.nodes[node_id]
            if node1.x != node2.x or node1.y != node2.y:
                different = True
                break
        assert different


class TestTopologyClass:
    """Tests for Topology dataclass."""

    def test_topology_creation(self):
        """Test creating a Topology instance."""
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 10, 10, 1.0, 1.0)
        }
        topology = Topology(
            nodes=nodes,
            base_station_id=1,
            width=100.0,
            height=100.0
        )
        
        assert len(topology.nodes) == 2
        assert topology.base_station_id == 1
        assert topology.width == 100.0
        assert topology.height == 100.0
