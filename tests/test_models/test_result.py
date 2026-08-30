"""
Tests for the Result models.
"""

import pytest
from energy_routing.models.result import RoundMetrics, SimulationResult


class TestRoundMetrics:
    """Tests for RoundMetrics dataclass."""

    def test_round_metrics_creation(self):
        """Test creating RoundMetrics with valid values."""
        rm = RoundMetrics(
            round=0,
            alive_nodes=50,
            dead_nodes=0,
            total_remaining_energy=50.0,
            total_energy_consumed=0.0,
            packets_generated=50,
            packets_delivered=48,
            packets_lost=2
        )
        assert rm.round == 0
        assert rm.alive_nodes == 50
        assert rm.dead_nodes == 0
        assert rm.total_remaining_energy == 50.0
        assert rm.total_energy_consumed == 0.0
        assert rm.packets_generated == 50
        assert rm.packets_delivered == 48
        assert rm.packets_lost == 2

    def test_round_metrics_negative_round_raises(self):
        """Test that negative round raises ValueError."""
        with pytest.raises(ValueError, match="round must be >= 0"):
            RoundMetrics(
                round=-1,
                alive_nodes=50,
                dead_nodes=0,
                total_remaining_energy=50.0,
                total_energy_consumed=0.0,
                packets_generated=50,
                packets_delivered=48,
                packets_lost=2
            )

    def test_round_metrics_negative_nodes_raises(self):
        """Test that negative node counts raise ValueError."""
        with pytest.raises(ValueError, match="Node counts must be >= 0"):
            RoundMetrics(
                round=0,
                alive_nodes=-1,
                dead_nodes=0,
                total_remaining_energy=50.0,
                total_energy_consumed=0.0,
                packets_generated=50,
                packets_delivered=48,
                packets_lost=2
            )

    def test_round_metrics_negative_energy_raises(self):
        """Test that negative energy raises ValueError."""
        with pytest.raises(ValueError, match="total_remaining_energy must be >= 0"):
            RoundMetrics(
                round=0,
                alive_nodes=50,
                dead_nodes=0,
                total_remaining_energy=-1.0,
                total_energy_consumed=0.0,
                packets_generated=50,
                packets_delivered=48,
                packets_lost=2
            )

    def test_round_metrics_negative_packets_raises(self):
        """Test that negative packet counts raise ValueError."""
        with pytest.raises(ValueError, match="Packet counts must be >= 0"):
            RoundMetrics(
                round=0,
                alive_nodes=50,
                dead_nodes=0,
                total_remaining_energy=50.0,
                total_energy_consumed=0.0,
                packets_generated=-1,
                packets_delivered=48,
                packets_lost=2
            )


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_simulation_result_creation(self):
        """Test creating SimulationResult with valid values."""
        result = SimulationResult(
            config={"test": "config"},
            round_metrics=[],
            fnd=100,
            hnd=200,
            lnd=300,
            total_packets_generated=1000,
            total_packets_delivered=950,
            total_packets_lost=50,
            packet_delivery_ratio=0.95,
            final_alive_nodes=10,
            final_dead_nodes=40,
            final_total_remaining_energy=5.0,
            final_total_energy_consumed=45.0,
            avg_hop_count=2.5,
            total_route_distance=1000.0
        )
        assert result.fnd == 100
        assert result.hnd == 200
        assert result.lnd == 300
        assert result.packet_delivery_ratio == 0.95
        assert result.avg_hop_count == 2.5

    def test_simulation_result_fnd_hnd_lnd_validation(self):
        """Test that FND <= HND <= LND is enforced."""
        with pytest.raises(ValueError, match="FND, HND, LND must satisfy FND <= HND <= LND"):
            SimulationResult(
                config={},
                fnd=200,
                hnd=100,
                lnd=300
            )

    def test_simulation_result_pdr_validation(self):
        """Test that PDR must be in [0, 1]."""
        with pytest.raises(ValueError, match=r"packet_delivery_ratio must be in \[0, 1\]"):
            SimulationResult(
                config={},
                packet_delivery_ratio=1.5
            )

        with pytest.raises(ValueError, match=r"packet_delivery_ratio must be in \[0, 1\]"):
            SimulationResult(
                config={},
                packet_delivery_ratio=-0.1
            )

    def test_simulation_result_none_values(self):
        """Test that None values for FND/HND/LND are allowed."""
        result = SimulationResult(
            config={},
            fnd=None,
            hnd=None,
            lnd=None
        )
        assert result.fnd is None
        assert result.hnd is None
        assert result.lnd is None

    def test_simulation_result_partial_none_values(self):
        """Test partial None values for FND/HND/LND."""
        # Only FND set
        result = SimulationResult(config={}, fnd=100)
        assert result.fnd == 100
        assert result.hnd is None
        assert result.lnd is None

        # FND and HND set
        result = SimulationResult(config={}, fnd=100, hnd=200)
        assert result.fnd == 100
        assert result.hnd == 200
        assert result.lnd is None

    def test_simulation_result_to_dict(self):
        """Test converting SimulationResult to dictionary."""
        result = SimulationResult(
            config={"test": "config"},
            round_metrics=[
                RoundMetrics(
                    round=0,
                    alive_nodes=50,
                    dead_nodes=0,
                    total_remaining_energy=50.0,
                    total_energy_consumed=0.0,
                    packets_generated=50,
                    packets_delivered=48,
                    packets_lost=2
                )
            ],
            fnd=100,
            hnd=200,
            lnd=300,
            total_packets_generated=1000,
            total_packets_delivered=950,
            total_packets_lost=50,
            packet_delivery_ratio=0.95
        )
        result_dict = result.to_dict()
        assert result_dict["fnd"] == 100
        assert result_dict["hnd"] == 200
        assert result_dict["lnd"] == 300
        assert result_dict["packet_delivery_ratio"] == 0.95
        assert len(result_dict["round_metrics"]) == 1

    def test_simulation_result_from_dict(self):
        """Test creating SimulationResult from dictionary."""
        data = {
            "config": {"test": "config"},
            "round_metrics": [
                {
                    "round": 0,
                    "alive_nodes": 50,
                    "dead_nodes": 0,
                    "total_remaining_energy": 50.0,
                    "total_energy_consumed": 0.0,
                    "packets_generated": 50,
                    "packets_delivered": 48,
                    "packets_lost": 2
                }
            ],
            "fnd": 100,
            "hnd": 200,
            "lnd": 300,
            "total_packets_generated": 1000,
            "total_packets_delivered": 950,
            "total_packets_lost": 50,
            "packet_delivery_ratio": 0.95,
            "final_alive_nodes": 10,
            "final_dead_nodes": 40,
            "final_total_remaining_energy": 5.0,
            "final_total_energy_consumed": 45.0,
            "avg_hop_count": 2.5
        }
        result = SimulationResult.from_dict(data)
        assert result.fnd == 100
        assert result.hnd == 200
        assert result.lnd == 300
        assert result.packet_delivery_ratio == 0.95
        assert result.avg_hop_count == 2.5
        assert len(result.round_metrics) == 1
