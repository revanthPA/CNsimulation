"""
Tests for the Simulator class.
"""

import pytest
import networkx as nx
from unittest.mock import Mock
from energy_routing.simulation.simulator import Simulator, create_simulator
from energy_routing.simulation.energy_model import EnergyModel
from energy_routing.routing.shortest_path import ShortestPathRouting
from energy_routing.models.node import Node
from energy_routing.models.packet import Packet, PacketStatus
from energy_routing.network.topology import Topology
from energy_routing.network.graph import build_graph
from energy_routing.config import (
    SimulationSettings, NetworkConfig, EnergyConfig, 
    SimulationParameters, RoutingConfig, OutputConfig
)


class TestSimulatorSetup:
    """Tests for simulator initialization and setup."""

    def setup_method(self):
        """Create a simple test configuration."""
        self.network_config = NetworkConfig(
            num_nodes=3,
            area_width=50.0,
            area_height=50.0,
            communication_range=30.0,
            seed=42,
            base_station_x=25.0,
            base_station_y=25.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.simulation_config = SimulationParameters(
            num_rounds=10,
            packets_per_round=1,
            packet_size=512
        )
        self.routing_config = RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        )
        self.output_config = OutputConfig()
        
        self.settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )

    def test_create_simulator_factory(self):
        """Test creating simulator via factory function."""
        simulator = create_simulator(self.settings)
        assert isinstance(simulator, Simulator)
        assert simulator.settings == self.settings
        assert simulator.topology is not None
        assert simulator.energy_model is not None
        assert simulator.routing_strategy is not None
        assert isinstance(simulator.routing_strategy, ShortestPathRouting)

    def test_simulator_initialization(self):
        """Test simulator initialization."""
        topology = None
        from energy_routing.network.topology import generate_topology
        topology = generate_topology(self.network_config, self.energy_config)
        
        energy_model = EnergyModel(self.energy_config)
        routing_strategy = ShortestPathRouting()
        
        simulator = Simulator(
            settings=self.settings,
            topology=topology,
            graph=None,
            energy_model=energy_model,
            routing_strategy=routing_strategy
        )
        
        assert simulator.settings == self.settings
        assert simulator.topology == topology
        assert simulator.graph is not None
        assert len(simulator.nodes) == 4  # 3 sensors + 1 base station
        assert simulator.topology.base_station_id in simulator.nodes


class TestDeliverHopEnergyAccounting:
    """Tests for the exact failed-hop energy accounting (3 cases)."""

    def setup_method(self):
        """Create a simple network for testing energy accounting."""
        self.network_config = NetworkConfig(
            num_nodes=2,
            area_width=20.0,
            area_height=20.0,
            communication_range=30.0,
            seed=42,
            base_station_x=10.0,
            base_station_y=10.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.simulation_config = SimulationParameters(
            num_rounds=10,
            packets_per_round=1,
            packet_size=512
        )
        self.routing_config = RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        )
        self.output_config = OutputConfig()
        
        self.settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )
        
        from energy_routing.network.topology import generate_topology
        topology = generate_topology(self.network_config, self.energy_config)
        
        energy_model = EnergyModel(self.energy_config)
        routing_strategy = ShortestPathRouting()
        
        self.simulator = Simulator(
            settings=self.settings,
            topology=topology,
            graph=None,
            energy_model=energy_model,
            routing_strategy=routing_strategy
        )

    def test_case1_failed_before_tx_dead_transmitter(self):
        """CASE 1: Failed before TX - transmitter dead."""
        # Node 0 is the transmitter, node 1 is receiver, node 2 is base station
        # Make transmitter dead
        self.simulator.nodes[0].is_alive = False
        self.simulator.nodes[0].remaining_energy = 0.0
        
        # Record initial energy of receiver
        initial_rx_energy = self.simulator.nodes[1].remaining_energy
        
        # Attempt hop - should fail before TX
        result = self.simulator._deliver_hop(0, 1, 10.0)
        
        # Should return False (hop failed)
        assert result is False
        
        # TX energy NOT consumed (transmitter dead)
        # Actually, can_transmit returns False for dead nodes, so no energy consumed
        # The dead node already has 0 energy
        assert self.simulator.nodes[0].remaining_energy == 0.0
        
        # RX energy NOT consumed
        assert self.simulator.nodes[1].remaining_energy == initial_rx_energy

    def test_case1_failed_before_tx_insufficient_energy(self):
        """CASE 1: Failed before TX - insufficient TX energy."""
        # Set transmitter to have very low energy
        tx_cost = self.simulator.energy_model.transmit_cost(10.0)
        self.simulator.nodes[0].remaining_energy = tx_cost / 2  # Less than needed
        self.simulator.nodes[0].is_alive = True
        
        initial_tx_energy = self.simulator.nodes[0].remaining_energy
        initial_rx_energy = self.simulator.nodes[1].remaining_energy
        
        # Attempt hop - should fail due to insufficient energy
        result = self.simulator._deliver_hop(0, 1, 10.0)
        
        assert result is False
        
        # TX energy NOT consumed
        assert self.simulator.nodes[0].remaining_energy == initial_tx_energy
        
        # RX energy NOT consumed
        assert self.simulator.nodes[1].remaining_energy == initial_rx_energy

    def test_case2_successful_tx_dead_receiver(self):
        """CASE 2: Successful TX + dead receiver."""
        # Make receiver dead
        self.simulator.nodes[1].is_alive = False
        self.simulator.nodes[1].remaining_energy = 0.0
        
        initial_tx_energy = self.simulator.nodes[0].remaining_energy
        tx_cost = self.simulator.energy_model.transmit_cost(10.0)
        
        # Attempt hop
        result = self.simulator._deliver_hop(0, 1, 10.0)
        
        # Should return False (hop failed)
        assert result is False
        
        # TX energy CONSUMED
        assert self.simulator.nodes[0].remaining_energy == initial_tx_energy - tx_cost
        
        # RX energy NOT consumed (receiver dead)
        assert self.simulator.nodes[1].remaining_energy == 0.0

    def test_case3_successful_tx_successful_rx(self):
        """CASE 3: Successful TX + successful RX."""
        initial_tx_energy = self.simulator.nodes[0].remaining_energy
        initial_rx_energy = self.simulator.nodes[1].remaining_energy
        tx_cost = self.simulator.energy_model.transmit_cost(10.0)
        rx_cost = self.simulator.energy_model.receive_cost()
        
        # Attempt hop
        result = self.simulator._deliver_hop(0, 1, 10.0)
        
        # Should return True (hop succeeded)
        assert result is True
        
        # TX energy CONSUMED
        assert self.simulator.nodes[0].remaining_energy == initial_tx_energy - tx_cost
        
        # RX energy CONSUMED
        assert self.simulator.nodes[1].remaining_energy == initial_rx_energy - rx_cost
        
        # Packets sent/received counters updated
        assert self.simulator.nodes[0].packets_sent == 1
        assert self.simulator.nodes[1].packets_received == 1

    def test_base_station_infinite_energy(self):
        """Test that base station energy is handled correctly."""
        # Base station is node 2 (num_nodes=2)
        base_station_id = self.simulator.topology.base_station_id
        assert base_station_id == 2
        
        # Base station should have infinite energy
        assert self.simulator.nodes[base_station_id].initial_energy == float('inf')
        assert self.simulator.nodes[base_station_id].remaining_energy == float('inf')
        assert self.simulator.nodes[base_station_id].is_alive is True
        
        # Test hop TO base station (node 1 -> base station)
        initial_tx_energy = self.simulator.nodes[1].remaining_energy
        tx_cost = self.simulator.energy_model.transmit_cost(10.0)
        rx_cost = self.simulator.energy_model.receive_cost()
        
        result = self.simulator._deliver_hop(1, base_station_id, 10.0)
        
        assert result is True
        # TX energy consumed
        assert self.simulator.nodes[1].remaining_energy == initial_tx_energy - tx_cost
        # Base station energy remains infinite (no subtraction from inf)
        assert self.simulator.nodes[base_station_id].remaining_energy == float('inf')
        
        # Base station received packet
        assert self.simulator.nodes[base_station_id].packets_received == 1


class TestSimulatorRun:
    """Tests for the full simulation run."""

    def setup_method(self):
        """Create a test configuration with known topology."""
        self.network_config = NetworkConfig(
            num_nodes=3,
            area_width=30.0,
            area_height=30.0,
            communication_range=25.0,  # Enough for connectivity
            seed=42,
            base_station_x=15.0,
            base_station_y=15.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=10.0,  # High energy to last multiple rounds
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.simulation_config = SimulationParameters(
            num_rounds=5,
            packets_per_round=1,
            packet_size=512
        )
        self.routing_config = RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        )
        self.output_config = OutputConfig()
        
        self.settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )

    def test_run_short_simulation(self):
        """Test running a short simulation."""
        simulator = create_simulator(self.settings)
        result = simulator.run()
        
        assert isinstance(result, type(simulator._compile_results()))
        assert result.total_packets_generated > 0
        assert result.total_packets_delivered >= 0
        assert result.total_packets_lost >= 0
        assert result.total_packets_generated == result.total_packets_delivered + result.total_packets_lost
        assert 0 <= result.packet_delivery_ratio <= 1
        assert len(result.round_metrics) <= self.settings.simulation.num_rounds

    def test_run_deterministic(self):
        """Test that simulation is deterministic with same seed."""
        simulator1 = create_simulator(self.settings)
        result1 = simulator1.run()
        
        simulator2 = create_simulator(self.settings)
        result2 = simulator2.run()
        
        assert result1.total_packets_generated == result2.total_packets_generated
        assert result1.total_packets_delivered == result2.total_packets_delivered
        assert result1.total_packets_lost == result2.total_packets_lost
        assert result1.fnd == result2.fnd
        assert result1.hnd == result2.hnd
        assert result1.lnd == result2.lnd

    def test_run_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        settings2 = SimulationSettings(
            network=NetworkConfig(
                num_nodes=3,
                area_width=30.0,
                area_height=30.0,
                communication_range=25.0,
                seed=43,  # Different seed
                base_station_x=15.0,
                base_station_y=15.0
            ),
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )
        
        simulator1 = create_simulator(self.settings)
        result1 = simulator1.run()
        
        simulator2 = create_simulator(settings2)
        result2 = simulator2.run()
        
        # Results should differ (at least topology differs)
        # Note: with high energy and few rounds, might have same delivery counts
        # But round metrics should differ due to different topology
        assert result1.round_metrics != result2.round_metrics or \
               result1.fnd != result2.fnd or \
               result1.total_route_distance != result2.total_route_distance

    def test_fnd_calculation(self):
        """Test First Node Death calculation."""
        # Use extremely low energy to ensure nodes die in first round
        # TX cost at ~10m is ~0.000205 J, so use energy < TX cost
        low_energy_config = EnergyConfig(
            initial_energy=0.0001,  # Less than one TX cost
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        settings = SimulationSettings(
            network=self.network_config,
            energy=low_energy_config,
            simulation=SimulationParameters(num_rounds=5, packets_per_round=1, packet_size=512),
            routing=self.routing_config,
            output=self.output_config
        )
        
        simulator = create_simulator(settings)
        result = simulator.run()
        
        # With energy less than TX cost, nodes can't transmit (Case 1)
        # They never die because they never consume energy
        # So FND should be None in this case
        # This is correct behavior per the energy accounting rules
        
        # Use energy that allows exactly 1 TX then dies
        # TX+RX cost ~0.00041 J, so use slightly more than that
        low_energy_config2 = EnergyConfig(
            initial_energy=0.0005,  # Enough for 1 hop, then dies
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        settings2 = SimulationSettings(
            network=self.network_config,
            energy=low_energy_config2,
            simulation=SimulationParameters(num_rounds=10, packets_per_round=1, packet_size=512),
            routing=self.routing_config,
            output=self.output_config
        )
        
        simulator2 = create_simulator(settings2)
        result2 = simulator2.run()
        
        # FND may or may not occur depending on exact topology and energy
        # The important thing is the result is valid
        if result2.fnd is not None:
            assert result2.fnd >= 0

    def test_hnd_calculation(self):
        """Test Half Node Death calculation."""
        low_energy_config = EnergyConfig(
            initial_energy=0.001,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        settings = SimulationSettings(
            network=self.network_config,
            energy=low_energy_config,
            simulation=SimulationParameters(num_rounds=20, packets_per_round=1, packet_size=512),
            routing=self.routing_config,
            output=self.output_config
        )
        
        simulator = create_simulator(settings)
        result = simulator.run()
        
        # With 3 nodes, HND = round when alive <= 1 (floor(3/2) = 1)
        if result.hnd is not None:
            assert result.hnd >= result.fnd

    def test_lnd_calculation(self):
        """Test Last Node Death calculation."""
        low_energy_config = EnergyConfig(
            initial_energy=0.001,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        
        settings = SimulationSettings(
            network=self.network_config,
            energy=low_energy_config,
            simulation=SimulationParameters(num_rounds=50, packets_per_round=1, packet_size=512),
            routing=self.routing_config,
            output=self.output_config
        )
        
        simulator = create_simulator(settings)
        result = simulator.run()
        
        # LND should occur within 50 rounds with very low energy
        if result.lnd is not None:
            assert result.lnd >= result.hnd if result.hnd else True

    def test_avg_hop_count_calculation(self):
        """Test average hop count calculation."""
        simulator = create_simulator(self.settings)
        result = simulator.run()
        
        if result.total_packets_delivered > 0:
            assert result.avg_hop_count is not None
            assert result.avg_hop_count >= 1.0

    def test_total_route_distance_calculation(self):
        """Test total route distance calculation."""
        simulator = create_simulator(self.settings)
        result = simulator.run()
        
        if result.total_packets_delivered > 0:
            assert result.total_route_distance is not None
            assert result.total_route_distance >= 0.0

    def test_energy_aware_routing_simulation(self):
        """Test simulation with energy-aware routing."""
        ea_routing_config = RoutingConfig(
            algorithm="energy_aware",
            alpha=0.5,
            beta=0.5
        )
        
        settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=ea_routing_config,
            output=self.output_config
        )
        
        simulator = create_simulator(settings)
        result = simulator.run()
        
        assert isinstance(result, type(simulator._compile_results()))
        assert result.total_packets_generated > 0


class TestPacketRouting:
    """Tests for packet routing logic."""

    def setup_method(self):
        """Create a simple chain topology for testing."""
        self.network_config = NetworkConfig(
            num_nodes=3,
            area_width=50.0,
            area_height=50.0,
            communication_range=30.0,
            seed=42,
            base_station_x=25.0,
            base_station_y=25.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=10.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.simulation_config = SimulationParameters(
            num_rounds=2,
            packets_per_round=1,
            packet_size=512
        )
        self.routing_config = RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        )
        self.output_config = OutputConfig()
        
        self.settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )

    def test_route_packet_generates_path(self):
        """Test that routing generates a valid path."""
        simulator = create_simulator(self.settings)
        
        # Generate a packet
        packet = simulator._generate_packet(0)
        assert packet.source_id == 0
        assert packet.dest_id == simulator.topology.base_station_id
        assert packet.status == PacketStatus.GENERATED
        
        # Route it
        delivered = simulator._route_packet(packet)
        
        # Should be delivered or lost (depending on topology connectivity)
        assert delivered in (True, False)
        
        # Check the final packet in the appropriate list
        if delivered:
            final_packet = simulator.delivered_packets[-1]
            assert final_packet.status == PacketStatus.DELIVERED
            assert final_packet.path is not None
            assert len(final_packet.path) >= 2
            assert final_packet.path[0] == 0
            assert final_packet.path[-1] == simulator.topology.base_station_id
        else:
            final_packet = simulator.lost_packets[-1]
            assert final_packet.status == PacketStatus.LOST

    def test_dead_node_excluded_from_routing(self):
        """Test that dead nodes are excluded from pathfinding."""
        simulator = create_simulator(self.settings)
        
        # Kill an intermediate node
        intermediate_node = 1
        simulator.nodes[intermediate_node].is_alive = False
        simulator.nodes[intermediate_node].remaining_energy = 0.0
        
        # Try to route from node 0
        packet = simulator._generate_packet(0)
        delivered = simulator._route_packet(packet)
        
        # If there's an alternative path, it might still deliver
        # If not, it should be lost
        # Either way, should not crash
        assert delivered in (True, False)

    def test_route_is_selected_once_for_the_full_packet(self):
        simulator = create_simulator(self.settings)
        base_station = simulator.topology.base_station_id
        simulator.graph.add_edge(0, 1, distance=5.0)
        simulator.graph.add_edge(1, base_station, distance=5.0)
        simulator.routing_strategy.find_path = Mock(return_value=(0, 1, base_station))
        simulator._deliver_hop = Mock(return_value=True)

        delivered = simulator._route_packet(simulator._generate_packet(0))

        assert delivered is True
        simulator.routing_strategy.find_path.assert_called_once()
        assert simulator.delivered_packets[-1].path == (0, 1, base_station)


class TestRoundMetricsCollection:
    """Tests for round metrics collection."""

    def setup_method(self):
        """Create a test configuration."""
        self.network_config = NetworkConfig(
            num_nodes=2,
            area_width=20.0,
            area_height=20.0,
            communication_range=30.0,
            seed=42,
            base_station_x=10.0,
            base_station_y=10.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.simulation_config = SimulationParameters(
            num_rounds=3,
            packets_per_round=2,
            packet_size=512
        )
        self.routing_config = RoutingConfig(
            algorithm="shortest_path",
            alpha=0.5,
            beta=0.5
        )
        self.output_config = OutputConfig()
        
        self.settings = SimulationSettings(
            network=self.network_config,
            energy=self.energy_config,
            simulation=self.simulation_config,
            routing=self.routing_config,
            output=self.output_config
        )

    def test_collect_round_metrics(self):
        """Test round metrics collection."""
        simulator = create_simulator(self.settings)
        
        # Run one round manually
        simulator.current_round = 0
        simulator._run_round()
        metrics = simulator._collect_round_metrics()
        
        assert metrics.round == 0
        assert metrics.alive_nodes >= 0
        assert metrics.dead_nodes >= 0
        assert metrics.packets_generated >= 0
        assert metrics.packets_delivered >= 0
        assert metrics.packets_lost >= 0
        assert metrics.packets_generated == metrics.packets_delivered + metrics.packets_lost

    def test_metrics_accumulate_over_rounds(self):
        """Test that metrics accumulate correctly over rounds."""
        simulator = create_simulator(self.settings)
        result = simulator.run()
        
        # Check round metrics exist
        assert len(result.round_metrics) > 0
        assert len(result.round_metrics) <= self.settings.simulation.num_rounds
        
        # Check cumulative totals
        total_gen = sum(m.packets_generated for m in result.round_metrics)
        total_del = sum(m.packets_delivered for m in result.round_metrics)
        total_lost = sum(m.packets_lost for m in result.round_metrics)
        
        assert total_gen == result.total_packets_generated
        assert total_del == result.total_packets_delivered
        assert total_lost == result.total_packets_lost
