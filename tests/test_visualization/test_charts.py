"""
Tests for visualization module.
"""

import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path

from energy_routing.visualization.network_plot import (
    plot_network_topology,
    plot_energy_heatmap
)
from energy_routing.visualization.charts import ResultVisualizer
from energy_routing.models.result import SimulationResult, RoundMetrics
from energy_routing.metrics.collector import AggregatedMetrics
from energy_routing.network.topology import Topology, generate_topology
from energy_routing.network.graph import build_graph
from energy_routing.config import NetworkConfig, EnergyConfig
from energy_routing.models.node import Node


class TestNetworkPlot:
    """Tests for network topology plotting."""

    def setup_method(self):
        """Create a simple topology for testing."""
        self.network_config = NetworkConfig(
            num_nodes=5,
            area_width=100.0,
            area_height=100.0,
            communication_range=50.0,
            seed=42,
            base_station_x=50.0,
            base_station_y=50.0
        )
        self.energy_config = EnergyConfig(
            initial_energy=1.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        self.topology = generate_topology(self.network_config, self.energy_config)
        self.graph = build_graph(self.topology, self.network_config.communication_range)

    def test_plot_network_topology_basic(self):
        """Test basic network topology plot."""
        fig = plot_network_topology(self.topology, self.graph, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_network_topology_with_highlight(self):
        """Test plot with highlighted nodes and path."""
        fig = plot_network_topology(
            self.topology,
            self.graph,
            highlight_nodes=[0, 1],
            highlight_path=[0, 1, 2, self.topology.base_station_id],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_network_topology_save(self):
        """Test saving plot to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "topology.png"
            fig = plot_network_topology(
                self.topology,
                self.graph,
                save_path=str(save_path),
                show=False
            )
            assert save_path.exists()
            plt.close(fig)

    def test_plot_network_topology_custom_sizes(self):
        """Test plot with custom node sizes."""
        fig = plot_network_topology(
            self.topology,
            self.graph,
            node_size=200,
            base_station_size=500,
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_energy_heatmap(self):
        """Test energy heatmap plot."""
        fig = plot_energy_heatmap(self.topology, self.graph, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_energy_heatmap_save(self):
        """Test saving energy heatmap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "heatmap.png"
            fig = plot_energy_heatmap(
                self.topology,
                self.graph,
                save_path=str(save_path),
                show=False
            )
            assert save_path.exists()
            plt.close(fig)


class TestResultVisualizer:
    """Tests for ResultVisualizer class."""

    def setup_method(self):
        """Create sample simulation results."""
        self.visualizer = ResultVisualizer(figsize=(8, 5))
        
        # Create sample results
        self.result1 = SimulationResult(
            config={},
            round_metrics=[
                RoundMetrics(0, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(1, 9, 1, 9.0, 1.0, 10, 9, 1),
                RoundMetrics(2, 7, 3, 7.0, 3.0, 10, 7, 3),
                RoundMetrics(3, 4, 6, 4.0, 6.0, 10, 4, 6),
                RoundMetrics(4, 1, 9, 1.0, 9.0, 10, 1, 9),
            ],
            fnd=1, hnd=3, lnd=4,
            total_packets_generated=50,
            total_packets_delivered=40,
            total_packets_lost=10,
            packet_delivery_ratio=0.8,
            final_alive_nodes=1,
            final_dead_nodes=9,
            final_total_remaining_energy=1.0,
            final_total_energy_consumed=9.0,
            avg_hop_count=2.5,
            total_route_distance=100.0
        )
        
        self.result2 = SimulationResult(
            config={},
            round_metrics=[
                RoundMetrics(0, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(1, 10, 0, 10.0, 0.0, 10, 10, 0),
                RoundMetrics(2, 9, 1, 9.0, 1.0, 10, 9, 1),
                RoundMetrics(3, 8, 2, 8.0, 2.0, 10, 8, 2),
                RoundMetrics(4, 6, 4, 6.0, 4.0, 10, 6, 4),
                RoundMetrics(5, 3, 7, 3.0, 7.0, 10, 3, 7),
            ],
            fnd=2, hnd=4, lnd=5,
            total_packets_generated=60,
            total_packets_delivered=50,
            total_packets_lost=10,
            packet_delivery_ratio=0.83,
            final_alive_nodes=3,
            final_dead_nodes=7,
            final_total_remaining_energy=3.0,
            final_total_energy_consumed=7.0,
            avg_hop_count=3.0,
            total_route_distance=120.0
        )

    def test_plot_alive_nodes_over_time(self):
        """Test alive nodes over time plot."""
        fig = self.visualizer.plot_alive_nodes_over_time(
            [self.result1, self.result2],
            labels=["Run 1", "Run 2"],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_alive_nodes_over_time_save(self):
        """Test saving alive nodes plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "alive.png"
            fig = self.visualizer.plot_alive_nodes_over_time(
                [self.result1],
                save_path=str(save_path),
                show=False
            )
            assert save_path.exists()
            plt.close(fig)

    def test_plot_energy_over_time(self):
        """Test energy over time plot."""
        fig = self.visualizer.plot_energy_over_time(
            [self.result1, self.result2],
            labels=["Run 1", "Run 2"],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_packets_over_time(self):
        """Test packets over time plot."""
        fig = self.visualizer.plot_packets_over_time(
            [self.result1, self.result2],
            labels=["Run 1", "Run 2"],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_pdr_comparison(self):
        """Test PDR comparison plot."""
        fig = self.visualizer.plot_pdr_comparison(
            [self.result1],
            [self.result2],
            label_a="SP",
            label_b="EA",
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_lifetime_comparison(self):
        """Test lifetime comparison plot."""
        fig = self.visualizer.plot_lifetime_comparison(
            [self.result1, self.result2],
            [self.result2, self.result1],  # Different order
            label_a="SP",
            label_b="EA",
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_hop_count_distribution(self):
        """Test hop count distribution plot."""
        fig = self.visualizer.plot_hop_count_distribution(
            [self.result1, self.result2],
            labels=["Run 1", "Run 2"],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_hop_count_with_none(self):
        """Test hop count plot with None values."""
        result_no_hops = SimulationResult(
            config={}, round_metrics=[],
            avg_hop_count=None,
            packet_delivery_ratio=0.5,
            final_total_remaining_energy=5.0
        )
        fig = self.visualizer.plot_hop_count_distribution(
            [result_no_hops, self.result1],
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_aggregated_metrics(self):
        """Test aggregated metrics plot."""
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
        fig = self.visualizer.plot_aggregated_metrics(metrics, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_aggregated_metrics_with_none(self):
        """Test aggregated metrics with None values."""
        metrics = AggregatedMetrics(
            num_runs=3,
            mean_fnd=None, std_fnd=None,
            mean_hnd=None, std_hnd=None,
            mean_lnd=None, std_lnd=None,
            mean_pdr=0.8, std_pdr=0.1,
            mean_avg_hop_count=None, std_avg_hop_count=None,
            mean_total_route_distance=None, std_total_route_distance=None,
            mean_final_energy=5.0, std_final_energy=1.0
        )
        fig = self.visualizer.plot_aggregated_metrics(metrics, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_network_size_scaling(self):
        """Test network size scaling plot."""
        results_by_size = {
            20: [self.result1],
            50: [self.result2],
            100: [self.result1, self.result2],
        }
        fig = self.visualizer.plot_network_size_scaling(
            results_by_size,
            metric='fnd',
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_network_size_scaling_different_metrics(self):
        """Test network size scaling with different metrics."""
        results_by_size = {
            20: [self.result1],
            50: [self.result2],
        }
        
        for metric in ['fnd', 'hnd', 'lnd', 'pdr', 'avg_hop_count', 'final_energy']:
            fig = self.visualizer.plot_network_size_scaling(
                results_by_size,
                metric=metric,
                show=False
            )
            assert isinstance(fig, plt.Figure)
            plt.close(fig)


class TestVisualizationIntegration:
    """Integration tests for visualization with actual simulation data."""

    def test_visualize_simulation_result(self):
        """Test visualizing actual simulation result."""
        # Create a simple topology
        network_config = NetworkConfig(
            num_nodes=3,
            area_width=30.0,
            area_height=30.0,
            communication_range=25.0,
            seed=42,
            base_station_x=15.0,
            base_station_y=15.0
        )
        energy_config = EnergyConfig(
            initial_energy=10.0,
            E_elec=50.0,
            E_amp=0.0013,
            packet_size=512
        )
        topology = generate_topology(network_config, energy_config)
        graph = build_graph(topology, network_config.communication_range)
        
        # Plot topology
        fig = plot_network_topology(topology, graph, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
        
        # Plot energy heatmap
        fig = plot_energy_heatmap(topology, graph, show=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)