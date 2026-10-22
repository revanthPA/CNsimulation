"""
Energy model for Wireless Sensor Network simulation.

Implements the first-order radio energy model for transmission and reception.
"""

from dataclasses import dataclass
from energy_routing.config import EnergyConfig


@dataclass
class EnergyModel:
    """
    First-order radio energy model for WSN.
    
    Implements the following formulas:
    - E_tx(k, d) = k_bits * E_elec + k_bits * E_amp * d^2
    - E_rx(k) = k_bits * E_elec
    
    Where:
    - k_bits = packet_size * 8 (bits)
    - d = Euclidean distance (meters)
    - E_elec = Energy for transmitter/receiver electronics (nJ/bit)
    - E_amp = Energy for transmit amplifier (nJ/bit/m^2)
    
    All calculations return energy in Joules.
    
    Attributes:
        config: Energy configuration
    """
    config: EnergyConfig

    def _bits(self) -> int:
        """Get packet size in bits."""
        return self.config.packet_size * 8

    def transmit_cost(self, distance: float) -> float:
        """
        Calculate energy cost for transmitting a packet.
        
        E_tx = k_bits * E_elec + k_bits * E_amp * d^2
        
        Args:
            distance: Transmission distance in meters
            
        Returns:
            Energy cost in Joules
        """
        k_bits = self._bits()
        # Convert nJ to J: divide by 1e9
        e_tx_nj = k_bits * (self.config.E_elec + self.config.E_amp * distance ** 2)
        return e_tx_nj / 1e9  # nJ → J

    def receive_cost(self) -> float:
        """
        Calculate energy cost for receiving a packet.
        
        E_rx = k_bits * E_elec
        
        Returns:
            Energy cost in Joules
        """
        k_bits = self._bits()
        e_rx_nj = k_bits * self.config.E_elec
        return e_rx_nj / 1e9  # nJ → J
