"""
Tests for the MetricsCollector class.
"""

import pytest
from energy_routing.metrics.collector import (
    MetricsCollector,
    AggregatedMetrics,
    calculate_avg_hop_count,
    calculate_total_route_distance
)
from energy_routing.models.result import SimulationResult, RoundMetrics
from energy_routing.models.packet import Packet, PacketStatus
import networkx as nx


class TestCalculateAvgHopCount:
    """Tests for calculate_avg_hop_count function."""

    def test_empty_list(self):
        """Test with empty packet list."""
        result = calculate_avg_hop_count([])
        assert result is None

    def test_single_packet_one_hop(self):
        """Test with single packet, one hop."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=2,
            generation_round=0,
            size=512,
            status=PacketStatus.DELIVERED,
            path=(0, 2)  # Direct: 1 hop
        )
        result = calculate_avg_hop_count([packet])
        assert result == 1.0

    def test_single_packet_multi_hop(self):
        """Test with single packet, multiple hops."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=3,
            generation_round=0,
            size=512,
            status=PacketStatus.DELIVERED,
            path=(0, 1, 2, 3)  # 3 hops
        )
        result = calculate_avg_hop_count([packet])
        assert result == 3.0

    def test_multiple_packets(self):
        """Test with multiple packets."""
        packets = [
            Packet(1, 0, 2, 0, 512, PacketStatus.DELIVERED, path=(0, 2)),
            Packet(2, 1, 2, 0, 512, PacketStatus.DELIVERED, path=(1, 2)),
            Packet(3, 0, 3, 0, 512, PacketStatus.DELIVERED, path=(0, 1, 2, 3)),
        ]
        # Hops: 1, 1, 3 = avg 1.666...
        result = calculate_avg_hop_count(packets)
        assert result == pytest.approx(5/3, rel=1e-9)


class TestCalculateTotalRouteDistance:
    """Tests for calculate_total_route_distance function."""

    def setup_method(self):
        """Create a simple graph for testing."""
        self.graph = nx.Graph()
        self.graph.add_edge(0, 1, distance=10.0)
        self.graph.add_edge(1, 2, distance=15.0)
        self.graph.add_edge(2, 3, distance=20.0)

    def test_empty_list(self):
        """Test with empty packet list."""
        result = calculate_total_route_distance([], self.graph)
        assert result is None

    def test_single_packet(self):
        """Test with single packet."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=3,
            generation_round=0,
            size=512,
            status=PacketStatus.DELIVERED,
            path=(0, 1, 2, 3)
        )
        # Distance: 10 + 15 + 20 = 45
        result = calculate_total_route_distance([packet], self.graph)
        assert result == 45.0

    def test_multiple_packets(self):
        """Test with multiple packets."""
        packets = [
            Packet(1, 0, 2, 0, 512, PacketStatus.DELIVERED, path=(0, 1, 2)),
            Packet(2, 1, 3, 0, 512, PacketStatus.DELIVERED, path=(1, 2, 3)),
        ]
        # First: 10 + 15 = 25
        # Second: 15 + 20 = 35
        # Total: 60
        result = calculate_total_route_distance(packets, self.graph)
        assert result == 60.0

    def test_missing_edge(self):
        """Test with missing edge in graph."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=3,
            generation_round=0,
            size=512,
            status=PacketStatus.DELIVERED,
            path=(0, 1, 5, 3)  # Edge 1-5 doesn't exist
        )
        # Should skip missing edge
        result = calculate_total_route_distance([packet], self.graph)
        # Only 0-1 exists (10.0), 1-5 and 5-3 don't exist
        assert result == 10.0


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def setup_method(self):
        """Create sample simulation results for testing."""
        self.collector = MetricsCollector()
        
        # Create sample results
        self.result1 = SimulationResult(
            config={},
            round_metrics=[
                RoundMetrics(0, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(1, 9, 1, 9.0, 1.0, 10, 9, 1),
                RoundMetrics(2, 5, 5, 5.0, 5.0, 10, 5, 5),
            ],
            fnd=1,
            hnd=2,
            lnd=3,
            total_packets_generated=30,
            total_packets_delivered=24,
            total_packets_lost=6,
            packet_delivery_ratio=0.8,
            final_alive_nodes=5,
            final_dead_nodes=5,
            final_total_remaining_energy=5.0,
            final_total_energy_consumed=5.0,
            avg_hop_count=2.5,
            total_route_distance=100.0
        )
        
        self.result2 = SimulationResult(
            config={},
            round_metrics=[
                RoundMetrics(0, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(1, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(2, 8, 2, 8.0, 2.0, 10, 8, 2),
                RoundMetrics(3, 4, 6, 4.0, 6.0, 10, 4, 6),
            ],
            fnd=2,
            hnd=3,
            lnd=4,
            total_packets_generated=40,
            total_packets_delivered=32,
            total_packets_lost=8,
            packet_delivery_ratio=0.8,
            final_alive_nodes=4,
            final_dead_nodes=6,
            final_total_remaining_energy=4.0,
            final_total_energy_consumed=6.0,
            avg_hop_count=3.0,
            total_route_distance=120.0
        )
        
        self.result3 = SimulationResult(
            config={},
            round_metrics=[
                RoundMetrics(0, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(1, 9, 1, 9.0, 1.0, 10, 9, 1),
            ],
            fnd=None,  # No nodes died
            hnd=None,
            lnd=None,
            total_packets_generated=20,
            total_packets_delivered=18,
            total_packets_lost=2,
            packet_delivery_ratio=0.9,
            final_alive_nodes=10,
            final_dead_nodes=0,
            final_total_remaining_energy=10.0,
            final_total_energy_consumed=0.0,
            avg_hop_count=None,
            total_route_distance=None
        )

    def test_add_result(self):
        """Test adding a single result."""
        self.collector.add_result(self.result1)
        assert len(self.collector.get_results()) == 1

    def test_add_results(self):
        """Test adding multiple results."""
        self.collector.add_results([self.result1, self.result2])
        assert len(self.collector.get_results()) == 2

    def test_clear(self):
        """Test clearing results."""
        self.collector.add_result(self.result1)
        self.collector.clear()
        assert len(self.collector.get_results()) == 0

    def test_get_results_returns_copy(self):
        """Test that get_results returns a copy."""
        self.collector.add_result(self.result1)
        results = self.collector.get_results()
        results.clear()
        assert len(self.collector.get_results()) == 1

    def test_compute_aggregated_metrics_empty(self):
        """Test aggregated metrics with no results."""
        metrics = self.collector.compute_aggregated_metrics()
        assert metrics.num_runs == 0
        assert metrics.mean_fnd is None
        assert metrics.mean_pdr == 0.0

    def test_compute_aggregated_metrics_with_results(self):
        """Test aggregated metrics with results."""
        self.collector.add_results([self.result1, self.result2, self.result3])
        metrics = self.collector.compute_aggregated_metrics()
        
        assert metrics.num_runs == 3
        
        # FND: 1, 2, None -> mean = 1.5
        assert metrics.mean_fnd == pytest.approx(1.5)
        
        # HND: 2, 3, None -> mean = 2.5
        assert metrics.mean_hnd == pytest.approx(2.5)
        
        # LND: 3, 4, None -> mean = 3.5
        assert metrics.mean_lnd == pytest.approx(3.5)
        
        # PDR: 0.8, 0.8, 0.9 -> mean = 0.833...
        assert metrics.mean_pdr == pytest.approx(0.8333333, rel=1e-6)
        
        # Avg hop count: 2.5, 3.0, None -> mean = 2.75
        assert metrics.mean_avg_hop_count == pytest.approx(2.75)
        
        # Total route distance: 100, 120, None -> mean = 110
        assert metrics.mean_total_route_distance == pytest.approx(110.0)
        
        # Final energy: 5.0, 4.0, 10.0 -> mean = 6.333...
        assert metrics.mean_final_energy == pytest.approx(6.333333, rel=1e-6)

    def test_compute_aggregated_metrics_std(self):
        """Test standard deviation in aggregated metrics."""
        self.collector.add_results([self.result1, self.result2])
        metrics = self.collector.compute_aggregated_metrics()
        
        # With 2 values, std should be > 0 for varying metrics
        assert metrics.std_pdr == 0.0  # Both 0.8
        assert metrics.std_final_energy > 0  # 5.0 vs 4.0

    def test_compute_round_aggregates(self):
        """Test round-wise aggregate computation."""
        self.collector.add_results([self.result1, self.result2])
        aggregates = self.collector.compute_round_aggregates()
        
        # Should have rounds 0, 1, 2, 3 (max across results)
        assert 0 in aggregates
        assert 1 in aggregates
        assert 2 in aggregates
        assert 3 in aggregates
        
        # Round 0: both have 10 alive, 0 dead
        assert aggregates[0]["mean_alive_nodes"] == 10.0
        assert aggregates[0]["mean_dead_nodes"] == 0.0
        assert aggregates[0]["std_alive_nodes"] == 0.0
        
        # Round 2: result1 has 5 alive, result2 has 8 alive
        assert aggregates[2]["mean_alive_nodes"] == 6.5

    def test_compare_algorithms(self):
        """Test algorithm comparison."""
        results_a = [self.result1, self.result2]
        results_b = [self.result3]
        
        comparison = self.collector.compare_algorithms(results_a, results_b, "SP", "EA")
        
        assert "SP" in comparison
        assert "EA" in comparison
        assert "improvement" in comparison
        
        # Check SP stats
        assert comparison["SP"]["num_runs"] == 2
        assert comparison["SP"]["pdr_mean"] == 0.8
        
        # Check EA stats
        assert comparison["EA"]["num_runs"] == 1
        assert comparison["EA"]["pdr_mean"] == 0.9
        
        # Check improvement (EA has higher PDR = better)
        # pdr: (0.9 - 0.8) / 0.8 * 100 = 12.5%
        assert comparison["improvement"]["pdr_mean"] == pytest.approx(12.5)

    def test_compare_algorithms_hop_count_improvement(self):
        """Test that lower hop count is considered improvement."""
        result_a = SimulationResult(
            config={}, round_metrics=[],
            avg_hop_count=3.0, packet_delivery_ratio=0.8,
            final_total_remaining_energy=5.0
        )
        result_b = SimulationResult(
            config={}, round_metrics=[],
            avg_hop_count=2.0, packet_delivery_ratio=0.8,
            final_total_remaining_energy=5.0
        )
        
        comparison = self.collector.compare_algorithms([result_a], [result_b], "A", "B")
        
        # B has lower hop count (2 vs 3), so improvement should be positive
        # (3 - 2) / 3 * 100 = 33.33%
        assert comparison["improvement"]["avg_hop_count_mean"] == pytest.approx(33.333, rel=1e-2)

    def test_export_to_dict(self):
        """Test exporting to dictionary."""
        self.collector.add_results([self.result1, self.result2])
        data = self.collector.export_to_dict()
        
        assert data["num_results"] == 2
        assert len(data["results"]) == 2
        assert "aggregated_metrics" in data
        assert "round_aggregates" in data


class TestAggregatedMetrics:
    """Tests for AggregatedMetrics dataclass."""

    def test_creation(self):
        """Test creating AggregatedMetrics."""
        metrics = AggregatedMetrics(
            num_runs=5,
            mean_fnd=10.0, std_fnd=2.0,
            mean_hnd=20.0, std_hnd=3.0,
            mean_lnd=30.0, std_lnd=4.0,
            mean_pdr=0.85, std_pdr=0.05,
            mean_avg_hop_count=2.5, std_avg_hop_count=0.5,
            mean_total_route_distance=100.0, std_total_route_distance=10.0,
            mean_final_energy=5.0, std_final_energy=1.0
        )
        assert metrics.num_runs == 5
        assert metrics.mean_fnd == 10.0
        assert metrics.std_pdr == 0.05