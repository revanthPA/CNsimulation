"""
Packet model for Wireless Sensor Network simulation.

Represents a data packet with routing information.
"""

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Optional, Tuple


class PacketStatus(Enum):
    """Delivery status of a packet."""
    GENERATED = auto()
    DELIVERED = auto()
    LOST = auto()


@dataclass(frozen=True)
class Packet:
    """
    Immutable representation of a data packet in the WSN.
    
    Attributes:
        packet_id: Unique identifier for the packet
        source_id: ID of the source node
        dest_id: ID of the destination node (typically base station)
        generation_round: Simulation round when packet was generated
        size: Packet size in bytes
        status: Current delivery status
        path: Immutable tuple of node IDs representing the route taken
        delivery_round: Simulation round when packet was delivered (None if lost)
    """
    packet_id: int
    source_id: int
    dest_id: int
    generation_round: int
    size: int  # bytes
    status: PacketStatus = PacketStatus.GENERATED
    path: Tuple[int, ...] = ()  # Immutable tuple of node IDs
    delivery_round: Optional[int] = None

    def __post_init__(self):
        """Validate packet initialization."""
        if self.packet_id < 0:
            raise ValueError("packet_id must be >= 0")
        if self.source_id < 0 or self.dest_id < 0:
            raise ValueError("Node IDs must be >= 0")
        if self.generation_round < 0:
            raise ValueError("generation_round must be >= 0")
        if self.size <= 0:
            raise ValueError("size must be > 0")

    def with_status(self, status: PacketStatus) -> "Packet":
        """Return a new Packet with updated status."""
        return replace(self, status=status)

    def with_path(self, path: Tuple[int, ...]) -> "Packet":
        """Return a new Packet with updated path."""
        return replace(self, path=path)

    def with_delivery_round(self, round: int) -> "Packet":
        """Return a new Packet with updated delivery round."""
        return replace(self, delivery_round=round)
