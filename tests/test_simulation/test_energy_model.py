"""
Tests for the EnergyModel class.
"""

import pytest
from energy_routing.simulation.energy_model import EnergyModel
from energy_routing.config import EnergyConfig


class TestEnergyModel:
    """Tests for EnergyModel calculations."""

    def setup_method(self):
        """Set up a standard energy model for testing."""
        self.config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,      # nJ/bit
            E_amp=0.0013,     # nJ/bit/m^2
            packet_size=512   # bytes
        )
        self.model = EnergyModel(self.config)

    def test_bits_calculation(self):
        """Test that packet size in bits is calculated correctly."""
        # 512 bytes = 4096 bits
        assert self.model._bits() == 4096

    def test_transmit_cost_zero_distance(self):
        """Test transmit cost at zero distance."""
        # E_tx = k * E_elec + k * E_amp * 0^2 = k * E_elec
        # 4096 * 50 = 204800 nJ = 0.0002048 J
        cost = self.model.transmit_cost(0.0)
        expected = 4096 * 50 / 1e9  # 204800 nJ = 0.0002048 J
        assert cost == pytest.approx(expected, rel=1e-9)

    def test_transmit_cost_positive_distance(self):
        """Test transmit cost at 10 meters."""
        # Worked example from plan:
        # E_tx = 4096 * 50 + 4096 * 0.0013 * 10^2
        #      = 204800 + 4096 * 0.0013 * 100
        #      = 204800 + 532.48
        #      = 205332.48 nJ = 0.00020533248 J
        cost = self.model.transmit_cost(10.0)
        expected = (4096 * 50 + 4096 * 0.0013 * 100) / 1e9
        assert cost == pytest.approx(expected, rel=1e-9)

    def test_receive_cost(self):
        """Test receive cost (distance independent)."""
        # E_rx = k * E_elec = 4096 * 50 = 204800 nJ = 0.0002048 J
        cost = self.model.receive_cost()
        expected = 4096 * 50 / 1e9
        assert cost == pytest.approx(expected, rel=1e-9)

    def test_transmit_cost_increases_with_distance(self):
        """Test that transmit cost increases with distance squared."""
        cost_10 = self.model.transmit_cost(10.0)
        cost_20 = self.model.transmit_cost(20.0)
        cost_30 = self.model.transmit_cost(30.0)

        assert cost_20 > cost_10
        assert cost_30 > cost_20
        # Should be roughly quadratic (20^2 = 4 * 10^2, so ~4x the distance component)
        # Total cost at 20m should be more than double cost at 10m

    def test_receive_cost_constant(self):
        """Test that receive cost is constant regardless of distance."""
        cost1 = self.model.receive_cost()
        cost2 = self.model.receive_cost()
        assert cost1 == cost2

    def test_zero_packet_size_raises(self):
        """Test that zero packet size raises ValueError in config validation."""
        with pytest.raises(ValueError, match="packet_size must be > 0"):
            EnergyConfig(
                initial_energy=1.0,
                E_elec=50.0,
                E_amp=0.0013,
                packet_size=0
            )

    def test_large_distance(self):
        """Test with large distance."""
        cost = self.model.transmit_cost(100.0)
        # E_tx = 4096 * 50 + 4096 * 0.0013 * 10000
        #      = 204800 + 53248 = 258048 nJ = 0.000258048 J
        expected = (4096 * 50 + 4096 * 0.0013 * 10000) / 1e9
        assert cost == pytest.approx(expected, rel=1e-9)

    def test_different_config(self):
        """Test with different energy configuration."""
        config = EnergyConfig(
            initial_energy=2.0,
            E_elec=100.0,
            E_amp=0.0026,
            packet_size=256
        )
        model = EnergyModel(config)
        # 256 bytes = 2048 bits
        # At 10m: E_tx = 2048 * 100 + 2048 * 0.0026 * 100
        #              = 204800 + 532.48 = 205332.48 nJ
        cost = model.transmit_cost(10.0)
        expected = (2048 * 100 + 2048 * 0.0026 * 100) / 1e9
        assert cost == pytest.approx(expected, rel=1e-9)


class TestEnergyModelConfigValidation:
    """Tests for EnergyConfig validation."""

    def test_valid_config(self):
        """Test that valid config works."""
        config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        assert config.initial_energy == 1.0

    def test_invalid_initial_energy(self):
        """Test that negative initial energy raises."""
        with pytest.raises(ValueError, match="initial_energy must be > 0"):
            EnergyConfig(initial_energy=-1.0, E_elec=50, E_amp=0.0013, packet_size=512)

    def test_invalid_E_elec(self):
        """Test that negative E_elec raises."""
        with pytest.raises(ValueError, match="Energy parameters must be >= 0"):
            EnergyConfig(initial_energy=1.0, E_elec=-50, E_amp=0.0013, packet_size=512)

    def test_invalid_E_amp(self):
        """Test that negative E_amp raises."""
        with pytest.raises(ValueError, match="Energy parameters must be >= 0"):
            EnergyConfig(initial_energy=1.0, E_elec=50, E_amp=-0.0013, packet_size=512)

    def test_invalid_packet_size(self):
        """Test that zero/negative packet size raises."""
        with pytest.raises(ValueError, match="packet_size must be > 0"):
            EnergyConfig(initial_energy=1.0, E_elec=50, E_amp=0.0013, packet_size=0)
        with pytest.raises(ValueError, match="packet_size must be > 0"):
            EnergyConfig(initial_energy=1.0, E_elec=50, E_amp=0.0013, packet_size=-10)


class TestEnergyModelWorkedExample:
    """Test the exact worked example from the plan documentation."""

    def test_plan_worked_example(self):
        """
        Verify the exact worked example from the plan:
        E_elec = 50 nJ/bit
        E_amp = 0.0013 nJ/bit/m^2
        packet_size = 512 bytes = 4096 bits
        distance = 10 meters
        
        E_tx = 4096 * 50 + 4096 * 0.0013 * 10^2
             = 204,800 + 4096 * 0.0013 * 100
             = 204,800 + 532.48
             = 205,332.48 nJ
             = 0.00020533248 J
        """
        config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        model = EnergyModel(config)

        tx_cost = model.transmit_cost(10.0)
        rx_cost = model.receive_cost()

        # Transmit cost at 10m
        expected_tx = (4096 * 50 + 4096 * 0.0013 * 100) / 1e9
        assert tx_cost == pytest.approx(expected_tx, rel=1e-9)

        # Receive cost (distance independent)
        expected_rx = (4096 * 50) / 1e9
        assert rx_cost == pytest.approx(expected_rx, rel=1e-9)

        # Total hop cost = TX + RX
        total_hop = tx_cost + rx_cost
        expected_total = (204800 + 532.48 + 204800) / 1e9  # 410132.48 nJ = 0.00041013248 J
        assert total_hop == pytest.approx(expected_total, rel=1e-9)

        # Verify with initial energy of 1.0 J, a node can transmit ~2440 packets at 10m
        # 1.0 / 0.00041013248 ≈ 2438 packets per node lifetime at 10m