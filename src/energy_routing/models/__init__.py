"""
Domain models for the Energy-Aware Routing Protocol simulator.

Contains:
- Node: Sensor node representation
- Packet: Data packet representation
- Result: Simulation result containers
"""

from .node import Node
from .packet import Packet, PacketStatus
from .result import RoundMetrics, SimulationResult

__all__ = ["Node", "Packet", "PacketStatus", "RoundMetrics", "SimulationResult"]
