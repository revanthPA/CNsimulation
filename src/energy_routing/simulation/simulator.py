"""
Simulation engine for Wireless Sensor Network.

Implements the core simulation loop with exact failed-hop energy accounting.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable

import networkx as nx

from energy_routing.models.node import Node
from energy_routing.models.packet import Packet, PacketStatus
from energy_routing.models.result import RoundMetrics, SimulationResult
from energy_routing.network.topology import Topology
from energy_routing.network.graph import build_graph, get_alive_subgraph
from energy_routing.routing.base import RoutingStrategy
from energy_routing.simulation.energy_model import EnergyModel
from energy_routing.config import SimulationSettings, SimulationParameters


@dataclass
class Simulator:
    """
    Core simulation engine for WSN.
    
    Implements the exact failed-hop energy accounting (3 cases):
    1. Failed before TX: transmitter dead or insufficient energy → NO TX, NO RX, LOST
    2. Successful TX + dead receiver → TX consumed, RX NOT consumed, LOST
    3. Successful TX + successful RX → TX consumed, RX consumed, DELIVERED/continues
    
    Attributes:
        settings: Complete simulation settings
        topology: Network topology (static)
        graph: Full network graph (static)
        energy_model: Energy model for TX/RX cost calculation
        routing_strategy: Routing algorithm to use
        nodes: Mutable node states (updated during simulation)
        packet_id_counter: Counter for generating unique packet IDs
    """
    settings: SimulationSettings
    topology: Topology
    graph: nx.Graph
    energy_model: EnergyModel
    routing_strategy: RoutingStrategy
    nodes: Dict[int, Node] = field(default_factory=dict)
    packet_id_counter: int = 0
    
    # Simulation state
    current_round: int = 0
    round_metrics: List[RoundMetrics] = field(default_factory=list)
    delivered_packets: List[Packet] = field(default_factory=list)
    lost_packets: List[Packet] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize simulator state."""
        # Copy nodes from topology (mutable during simulation)
        self.nodes = {nid: node for nid, node in self.topology.nodes.items()}
        
        # Build static graph once
        self.graph = build_graph(self.topology, self.settings.network.communication_range)
        
        # Initialize random seed for reproducibility
        random.seed(self.settings.network.seed)
    
    def run(self) -> SimulationResult:
        """
        Run the complete simulation.
        
        Returns:
            SimulationResult with all metrics and outcomes
        """
        # Reset state
        self.current_round = 0
        self.round_metrics = []
        self.delivered_packets = []
        self.lost_packets = []
        self.packet_id_counter = 0
        
        # Reset node energies to initial
        for node in self.nodes.values():
            if node.initial_energy != float('inf'):
                node.remaining_energy = node.initial_energy
                node.is_alive = True
                node.packets_sent = 0
                node.packets_received = 0
                node.packets_forwarded = 0
                node.packets_dropped = 0
        
        # Run simulation rounds
        for round_num in range(self.settings.simulation.num_rounds):
            self.current_round = round_num
            self._run_round()
            
            # Collect round metrics
            metrics = self._collect_round_metrics()
            self.round_metrics.append(metrics)
            
            # Check for early termination (all sensor nodes dead)
            alive_sensors = sum(1 for nid, node in self.nodes.items() 
                               if nid != self.topology.base_station_id and node.is_alive)
            if alive_sensors == 0:
                break
        
        # Compile final results
        return self._compile_results()
    
    def _run_round(self):
        """Execute a single simulation round."""
        packets_generated = 0
        packets_delivered = 0
        packets_lost = 0
        
        # Generate packets for each alive sensor node
        for node_id, node in self.nodes.items():
            # Skip base station
            if node_id == self.topology.base_station_id:
                continue
            
            # Skip dead nodes
            if not node.is_alive:
                continue
            
            # Generate packets_per_round packets
            for _ in range(self.settings.simulation.packets_per_round):
                packet = self._generate_packet(node_id)
                packets_generated += 1
                
                # Route and deliver packet
                delivered = self._route_packet(packet)
                if delivered:
                    packets_delivered += 1
                else:
                    packets_lost += 1
        
        # Store round totals for metrics collection
        self._round_packets_generated = packets_generated
        self._round_packets_delivered = packets_delivered
        self._round_packets_lost = packets_lost
    
    def _generate_packet(self, source_id: int) -> Packet:
        """Generate a new packet from source node."""
        packet = Packet(
            packet_id=self.packet_id_counter,
            source_id=source_id,
            dest_id=self.topology.base_station_id,
            generation_round=self.current_round,
            size=self.settings.simulation.packet_size
        )
        self.packet_id_counter += 1
        return packet
    
    def _route_packet(self, packet: Packet) -> bool:
        """
        Route a packet from source to destination.
        
        Returns:
            True if delivered, False if lost
        """
        current = packet.source_id
        
        # Get alive subgraph for routing (excludes dead nodes)
        alive_graph = get_alive_subgraph(self.graph, self.nodes)
        
        # Check if source is still alive and in graph
        if current not in alive_graph:
            packet = packet.with_status(PacketStatus.LOST)
            self.lost_packets.append(packet)
            self.nodes[current].packets_dropped += 1
            return False
        
        route = self.routing_strategy.find_path(
            alive_graph, self.nodes, current, self.topology.base_station_id
        )
        if len(route) < 2 or route[0] != current or route[-1] != self.topology.base_station_id:
            packet = packet.with_status(PacketStatus.LOST)
            self.lost_packets.append(packet)
            self.nodes[current].packets_dropped += 1
            return False

        traversed_path = [current]
        for current, next_hop in zip(route, route[1:]):
            # Get distance between current and next_hop
            distance = self.graph[current][next_hop].get("distance", 0.0)
            
            # Attempt hop delivery with exact energy accounting
            success = self._deliver_hop(current, next_hop, distance)
            
            # Add to path
            traversed_path.append(next_hop)
            
            if not success:
                # Hop failed - packet lost
                packet = packet.with_path(tuple(traversed_path)).with_status(PacketStatus.LOST)
                self.lost_packets.append(packet)
                return False
            
        
        # Packet delivered successfully
        packet = packet.with_path(tuple(traversed_path)).with_status(PacketStatus.DELIVERED).with_delivery_round(self.current_round)
        self.delivered_packets.append(packet)
        return True
    
    def _deliver_hop(self, current: int, next_hop: int, distance: float) -> bool:
        """
        Execute a single hop delivery with EXACT failed-hop energy accounting.
        
        Case 1: Failed before TX (transmitter dead or insufficient energy)
        → TX energy: NONE, RX energy: NONE, Status: LOST
        
        Case 2: Successful TX + dead receiver
        → TX energy: CONSUMED, RX energy: NOT consumed, Status: LOST
        
        Case 3: Successful TX + successful RX
        → TX energy: CONSUMED, RX energy: CONSUMED, Status: DELIVERED/continues
        
        Args:
            current: Current node ID (transmitter)
            next_hop: Next hop node ID (receiver)
            distance: Distance between nodes
            
        Returns:
            True if hop succeeded (packet continues), False if lost
        """
        # Get nodes
        tx_node = self.nodes[current]
        rx_node = self.nodes[next_hop]
        
        # Calculate TX energy cost
        tx_cost = self.energy_model.transmit_cost(distance)
        
        # CASE 1: Failed before TX
        # Transmitter dead OR insufficient energy for TX
        if not tx_node.can_transmit(tx_cost):
            return False  # NO TX energy, NO RX energy
        
        # CASE 2 & 3: TX energy CONSUMED
        tx_node.consume_energy(tx_cost)
        tx_node.packets_sent += 1
        
        # Check if receiver is alive
        if not rx_node.is_alive:
            # CASE 2: Dead receiver
            # TX consumed, RX NOT consumed
            return False
        
        # CASE 3: Successful RX
        rx_cost = self.energy_model.receive_cost()
        rx_node.consume_energy(rx_cost)
        rx_node.packets_received += 1
        
        # If receiver is not base station, it's forwarding
        if next_hop != self.topology.base_station_id:
            rx_node.packets_forwarded += 1
        
        return True
    
    def _collect_round_metrics(self) -> RoundMetrics:
        """Collect metrics for the current round."""
        # Count alive/dead sensor nodes (exclude base station)
        alive_sensors = 0
        dead_sensors = 0
        total_remaining_energy = 0.0
        total_energy_consumed = 0.0
        
        for node_id, node in self.nodes.items():
            if node_id == self.topology.base_station_id:
                continue  # Skip base station
            
            if node.is_alive:
                alive_sensors += 1
            else:
                dead_sensors += 1
            
            if node.initial_energy != float('inf'):
                total_remaining_energy += node.remaining_energy
                total_energy_consumed += (node.initial_energy - node.remaining_energy)
        
        return RoundMetrics(
            round=self.current_round,
            alive_nodes=alive_sensors,
            dead_nodes=dead_sensors,
            total_remaining_energy=total_remaining_energy,
            total_energy_consumed=total_energy_consumed,
            packets_generated=self._round_packets_generated,
            packets_delivered=self._round_packets_delivered,
            packets_lost=self._round_packets_lost
        )
    
    def _compile_results(self) -> SimulationResult:
        """Compile final simulation results."""
        # Calculate FND, HND, LND
        fnd = None
        hnd = None
        lnd = None
        
        total_nodes = self.settings.network.num_nodes
        half_nodes = total_nodes // 2
        
        for metrics in self.round_metrics:
            dead_count = metrics.dead_nodes
            
            # FND: first round with at least 1 dead sensor node
            if fnd is None and dead_count >= 1:
                fnd = metrics.round
            
            # HND: first round with alive sensor nodes <= half
            if hnd is None and metrics.alive_nodes <= half_nodes:
                hnd = metrics.round
            
            # LND: first round with all sensor nodes dead
            if lnd is None and dead_count == total_nodes:
                lnd = metrics.round
        
        # Calculate totals
        total_generated = sum(m.packets_generated for m in self.round_metrics)
        total_delivered = sum(m.packets_delivered for m in self.round_metrics)
        total_lost = sum(m.packets_lost for m in self.round_metrics)
        
        pdr = total_delivered / total_generated if total_generated > 0 else 0.0
        
        # Final node counts
        final_alive = sum(1 for nid, node in self.nodes.items() 
                         if nid != self.topology.base_station_id and node.is_alive)
        final_dead = self.settings.network.num_nodes - final_alive
        
        # Final energy
        final_remaining = sum(node.remaining_energy for nid, node in self.nodes.items() 
                             if nid != self.topology.base_station_id and node.initial_energy != float('inf'))
        final_consumed = sum(node.initial_energy - node.remaining_energy for nid, node in self.nodes.items() 
                            if nid != self.topology.base_station_id and node.initial_energy != float('inf'))
        
        # Calculate average hop count for delivered packets
        avg_hop_count = None
        if self.delivered_packets:
            total_hops = sum(len(p.path) - 1 for p in self.delivered_packets)
            avg_hop_count = total_hops / len(self.delivered_packets)
        
        # Calculate total route distance
        total_route_distance = None
        if self.delivered_packets:
            total_dist = 0.0
            for packet in self.delivered_packets:
                for i in range(len(packet.path) - 1):
                    u = packet.path[i]
                    v = packet.path[i + 1]
                    if self.graph.has_edge(u, v):
                        total_dist += self.graph[u][v].get("distance", 0.0)
            total_route_distance = total_dist
        
        # Prepare config dict for serialization
        config_dict = {
            "network": {k: v for k, v in self.settings.network.__dict__.items()},
            "energy": {k: v for k, v in self.settings.energy.__dict__.items()},
            "simulation": {k: v for k, v in self.settings.simulation.__dict__.items()},
            "routing": {k: v for k, v in self.settings.routing.__dict__.items()},
            "output": {k: v for k, v in self.settings.output.__dict__.items()}
        }
        
        return SimulationResult(
            config=config_dict,
            round_metrics=self.round_metrics,
            fnd=fnd,
            hnd=hnd,
            lnd=lnd,
            total_packets_generated=total_generated,
            total_packets_delivered=total_delivered,
            total_packets_lost=total_lost,
            packet_delivery_ratio=pdr,
            final_alive_nodes=final_alive,
            final_dead_nodes=final_dead,
            final_total_remaining_energy=final_remaining,
            final_total_energy_consumed=final_consumed,
            avg_hop_count=avg_hop_count,
            total_route_distance=total_route_distance
        )


def create_simulator(settings: SimulationSettings) -> Simulator:
    """
    Factory function to create a Simulator instance.
    
    Args:
        settings: Complete simulation settings
        
    Returns:
        Configured Simulator instance
    """
    # Generate topology
    topology = None
    # We need to import generate_topology here to avoid circular imports
    from energy_routing.network.topology import generate_topology
    topology = generate_topology(settings.network, settings.energy)
    
    # Create energy model
    energy_model = EnergyModel(settings.energy)
    
    # Create routing strategy
    from energy_routing.routing import create_routing_strategy
    routing_strategy = create_routing_strategy(
        settings.routing.algorithm,
        alpha=settings.routing.alpha,
        beta=settings.routing.beta
    )
    
    return Simulator(
        settings=settings,
        topology=topology,
        graph=None,  # Will be built in __post_init__
        energy_model=energy_model,
        routing_strategy=routing_strategy
    )
