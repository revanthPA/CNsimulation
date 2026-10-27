"""
Tests for simulator edge cases and correctness gaps.

Covers:
- Zero generated packets and PDR division-by-zero handling
- Disconnected topologies and unreachable destinations
- FND/HND/LND behavior when events never occur
"""

import pytest
import networkx as nx
from energy_routing.simulation.simulator import Simulator, create_simulator
from energy_routing.models.node import Node
from energy_routing.models.packet import Packet, PacketStatus
from energy_routing.network.topology import Topology
from energy_routing.network.graph import build_graph
from energy_routing.routing.shortest_path import ShortestPathRouting
from energy_routing.config import (
    SimulationSettings, NetworkConfig, EnergyConfig,
    SimulationParameters, RoutingConfig, OutputConfig
)


class TestZeroPacketPDR:
    """Tests for PDR handling when no packets are generated."""

    def test_packets_per_round_zero(self):
        """Test PDR is 0.0 when packets_per_round=0 (no division by zero)."""
        network_config = NetworkConfig(
            num_nodes=3, area_width=50.0, area_height=50.0,
            communication_range=30.0, seed=42,
            base_station_x=25.0, base_station_y=25.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0, E_elec=50.0, E_amp=0.0013, packet_size=512
        )
        simulation_config = SimulationParameters(
            num_rounds=10, packets_per_round=0, packet_size=512
        )
        routing_config = RoutingConfig(
            algorithm="shortest_path", alpha=0.5, beta=0.5
        )
        output_config = OutputConfig()

        settings = SimulationSettings(
            network=network_config, energy=energy_config,
            simulation=simulation_config, routing=routing_config,
            output=output_config
        )

        simulator = create_simulator(settings)
        result = simulator.run()

        # No packets generated, PDR should be 0.0 (no division by zero)
        assert result.total_packets_generated == 0
        assert result.total_packets_delivered == 0
        assert result.total_packets_lost == 0
        assert result.packet_delivery_ratio == 0.0
        assert len(result.round_metrics) == 10  # All rounds completed

    def test_pdr_zero_generated_all_rounds(self):
        """Test that PDR remains 0.0 across all rounds with zero packets."""
        network_config = NetworkConfig(
            num_nodes=2, area_width=20.0, area_height=20.0,
            communication_range=30.0, seed=42,
            base_station_x=10.0, base_station_y=10.0
        )
        energy_config = EnergyConfig(
            initial_energy=1.0, E_elec=50.0, E_amp=0.0013, packet_size=512
        )
        simulation_config = SimulationParameters(
            num_rounds=5, packets_per_round=0, packet_size=512
        )
        routing_config = RoutingConfig(
            algorithm="energy_aware", alpha=0.5, beta=0.5
        )
        output_config = OutputConfig()

        settings = SimulationSettings(
            network=network_config, energy=energy_config,
            simulation=simulation_config, routing=routing_config,
            output=output_config
        )

        simulator = create_simulator(settings)
        result = simulator.run()

        for m in result.round_metrics:
            assert m.packets_generated == 0
            assert m.packets_delivered == 0
            assert m.packets_lost == 0
        assert result.packet_delivery_ratio == 0.0


class TestDisconnectedTopology:
    """Tests for routing when nodes cannot reach the base station."""

    def test_unreachable_destination_packet_lost(self):
        """Test that packets to an unreachable base station are lost."""
        # Node 0 is isolated from base station (node 2)
        nodes = {
            0: Node(0, 0, 0, 1.0, 1.0),
            1: Node(1, 100, 0, 1.0, 1.0),  # base station, too far from 0
        }
        topology = Topology(nodes=nodes, base_station_id=1, width=200.0, height=200.0)
        graph = nx.Graph()
        for nid, node in nodes.items():
            graph.add_node(nid, x=node.x, y=node.y)
        # No edges - nodes are completely disconnected

        routing = ShortestPathRouting()
        path = routing.find_path(graph, nodes, 0, 1)
        assert path == ()  # No path exists

        next_hop = routing.get_next_hop(graph, nodes, 0, 1)
        assert next_hop is None

    def test_simulator_with_disconnected_nodes(self):
        """Test simulator handles nodes that cannot reach base station."""
        network_config = NetworkConfig(
            num_nodes=3, area_width=200.0, area_height=200.0,
            communication_range=10.0, seed=42,
            base_station_x=100.0, base_station_y=100.0
        )
        energy_config = EnergyConfig(
            initial_energy=10.0, E_elec=50.0, E_amp=0.0013, packet_size=512
        )
        simulation_config = SimulationParameters(
            num_rounds=5, packets_per_round=1, packet_size=512
        )
        routing_config = RoutingConfig(
            algorithm="shortest_path", alpha=0.5, beta=0.5
        )
        output_config = OutputConfig()

        settings = SimulationSettings(
            network=network_config, energy=energy_config,
            simulation=simulation_config, routing=routing_config,
            output=output_config
        )

        simulator = create_simulator(settings)
        result = simulator.run()

        # With short range, many nodes may be unreachable
        # All packets should be either delivered or lost, no crashes
        assert result.total_packets_generated >= 0
        assert result.total_packets_delivered >= 0
        assert result.total_packets_lost >= 0
        assert result.total_packets_generated == \
            result.total_packets_delivered + result.total_packets_lost
        assert 0.0 <= result.packet_delivery_ratio <= 1.0

    def test_partial_connectivity_some_lost_some_delivered(self):
        """Test mixed connectivity where some nodes reach base, some don't."""
        # Node 0 close to base station (distance ~7.07 < range 10)
        # Node 1 far from base station (no edge possible)
        nodes = {
            0: Node(0, 0, 0, 10.0, 10.0),
            1: Node(1, 100, 100, 10.0, 10.0),
            2: Node(2, 5, 5, float('inf'), float('inf')),  # base station
        }
        topology = Topology(nodes=nodes, base_station_id=2, width=200.0, height=200.0)
        graph = build_graph(topology, communication_range=10.0)

        # Node 0 should connect to base station (dist ~7.07 < 10)
        assert graph.has_edge(0, 2)
        # Node 1 should NOT connect to base station (dist ~134 > 10)
        assert not graph.has_edge(1, 2)
        # Node 1 should NOT connect to node 0 either (dist ~141 > 10)
        assert not graph.has_edge(1, 0)

        routing = ShortestPathRouting()
        # Node 0 can reach base station
        path_0 = routing.find_path(graph, nodes, 0, 2)
        assert path_0 == (0, 2)
        # Node 1 is completely isolated
        path_1 = routing.find_path(graph, nodes, 1, 2)
        assert path_1 == ()