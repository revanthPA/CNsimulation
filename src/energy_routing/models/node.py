"""
Node model for Wireless Sensor Network simulation.

Represents a sensor node with position, energy, and packet statistics.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """
    Represents a sensor node in the Wireless Sensor Network.
    
    Attributes:
        node_id: Unique identifier for the node
        x: X-coordinate in meters
        y: Y-coordinate in meters
        initial_energy: Initial energy in Joules
        remaining_energy: Current remaining energy in Joules
        is_alive: Whether the node is operational
        packets_sent: Count of packets transmitted
        packets_received: Count of packets received
        packets_forwarded: Count of packets forwarded
        packets_dropped: Count of packets dropped
    """
    node_id: int
    x: float  # meters
    y: float  # meters
    initial_energy: float  # Joules
    remaining_energy: float  # Joules
    is_alive: bool = True
    packets_sent: int = 0
    packets_received: int = 0
    packets_forwarded: int = 0
    packets_dropped: int = 0

    def __post_init__(self):
        """Validate node initialization."""
        if self.initial_energy < 0:
            raise ValueError("initial_energy must be >= 0")
        if self.remaining_energy < 0:
            raise ValueError("remaining_energy must be >= 0")
        if self.initial_energy > 0 and self.remaining_energy > self.initial_energy:
            # Clamp remaining energy to initial if it exceeds
            self.remaining_energy = self.initial_energy

    def consume_energy(self, amount: float) -> bool:
        """
        Consume energy from the node.
        
        Args:
            amount: Energy to consume in Joules
            
        Returns:
            True if node died as a result, False otherwise
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Energy consumption amount must be >= 0")

        # Dead nodes cannot consume energy
        if not self.is_alive:
            return False

        self.remaining_energy -= amount

        # Node dies if energy drops to or below zero
        if self.remaining_energy <= 0:
            self.is_alive = False
            self.remaining_energy = 0.0  # Clamp to zero
            return True
        
        return False

    def can_transmit(self, energy_cost: float) -> bool:
        """
        Check if node can transmit a packet.
        
        Args:
            energy_cost: Energy required for transmission in Joules
            
        Returns:
            True if node is alive and has sufficient energy
        """
        return self.is_alive and self.remaining_energy >= energy_cost
