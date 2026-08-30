"""
Result models for Wireless Sensor Network simulation.

Contains data structures for storing simulation metrics and results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RoundMetrics:
    """
    Metrics collected per simulation round.
    
    Attributes:
        round: Simulation round number
        alive_nodes: Number of alive sensor nodes
        dead_nodes: Number of dead sensor nodes
        total_remaining_energy: Total remaining energy for all sensor nodes in Joules
        total_energy_consumed: Total energy consumed by all sensor nodes in Joules
        packets_generated: Number of packets generated this round
        packets_delivered: Number of packets delivered this round
        packets_lost: Number of packets lost this round
    """
    round: int
    alive_nodes: int
    dead_nodes: int
    total_remaining_energy: float  # Joules
    total_energy_consumed: float  # Joules
    packets_generated: int
    packets_delivered: int
    packets_lost: int

    def __post_init__(self):
        """Validate round metrics."""
        if self.round < 0:
            raise ValueError("round must be >= 0")
        if self.alive_nodes < 0 or self.dead_nodes < 0:
            raise ValueError("Node counts must be >= 0")
        if self.total_remaining_energy < 0:
            raise ValueError("total_remaining_energy must be >= 0")
        if self.total_energy_consumed < 0:
            raise ValueError("total_energy_consumed must be >= 0")
        if self.packets_generated < 0 or self.packets_delivered < 0 or self.packets_lost < 0:
            raise ValueError("Packet counts must be >= 0")


@dataclass
class SimulationResult:
    """
    Complete results from a single simulation run.
    
    Attributes:
        config: Full configuration used for the simulation
        round_metrics: List of per-round metrics
        fnd: First Node Death round (None if no nodes died)
        hnd: Half Node Death round (None if never reached)
        lnd: Last Node Death round (None if not all nodes died)
        total_packets_generated: Total packets generated
        total_packets_delivered: Total packets delivered
        total_packets_lost: Total packets lost
        packet_delivery_ratio: Ratio of delivered to generated packets
        final_alive_nodes: Alive sensor nodes at simulation end
        final_dead_nodes: Dead sensor nodes at simulation end
        final_total_remaining_energy: Total remaining energy at end in Joules
        final_total_energy_consumed: Total energy consumed at end in Joules
        avg_hop_count: Average number of hops per delivered packet
        total_route_distance: Total Euclidean distance of all delivered packets in meters
    """
    config: Dict[str, Any]
    round_metrics: List[RoundMetrics] = field(default_factory=list)
    fnd: Optional[int] = None
    hnd: Optional[int] = None
    lnd: Optional[int] = None
    total_packets_generated: int = 0
    total_packets_delivered: int = 0
    total_packets_lost: int = 0
    packet_delivery_ratio: float = 0.0
    final_alive_nodes: int = 0
    final_dead_nodes: int = 0
    final_total_remaining_energy: float = 0.0
    final_total_energy_consumed: float = 0.0
    avg_hop_count: Optional[float] = None
    total_route_distance: Optional[float] = None

    def __post_init__(self):
        """Validate simulation result."""
        # Validate FND <= HND <= LND when all are defined
        defined = [x for x in [self.fnd, self.hnd, self.lnd] if x is not None]
        if len(defined) >= 2:
            if sorted(defined) != defined:
                raise ValueError("FND, HND, LND must satisfy FND <= HND <= LND")
        
        if not 0 <= self.packet_delivery_ratio <= 1:
            raise ValueError("packet_delivery_ratio must be in [0, 1]")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "config": self.config,
            "round_metrics": [rm.__dict__ for rm in self.round_metrics],
            "fnd": self.fnd,
            "hnd": self.hnd,
            "lnd": self.lnd,
            "total_packets_generated": self.total_packets_generated,
            "total_packets_delivered": self.total_packets_delivered,
            "total_packets_lost": self.total_packets_lost,
            "packet_delivery_ratio": self.packet_delivery_ratio,
            "final_alive_nodes": self.final_alive_nodes,
            "final_dead_nodes": self.final_dead_nodes,
            "final_total_remaining_energy": self.final_total_remaining_energy,
            "final_total_energy_consumed": self.final_total_energy_consumed,
            "avg_hop_count": self.avg_hop_count,
            "total_route_distance": self.total_route_distance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        """Create SimulationResult from dictionary."""
        round_metrics = [RoundMetrics(**rm) for rm in data["round_metrics"]]
        return cls(
            config=data["config"],
            round_metrics=round_metrics,
            fnd=data.get("fnd"),
            hnd=data.get("hnd"),
            lnd=data.get("lnd"),
            total_packets_generated=data["total_packets_generated"],
            total_packets_delivered=data["total_packets_delivered"],
            total_packets_lost=data["total_packets_lost"],
            packet_delivery_ratio=data["packet_delivery_ratio"],
            final_alive_nodes=data["final_alive_nodes"],
            final_dead_nodes=data["final_dead_nodes"],
            final_total_remaining_energy=data["final_total_remaining_energy"],
            final_total_energy_consumed=data["final_total_energy_consumed"],
            avg_hop_count=data.get("avg_hop_count"),
            total_route_distance=data.get("total_route_distance")
        )
