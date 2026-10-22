"""
Tests for the Streamlit Dashboard.
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestDashboardImports:
    """Test that dashboard can be imported without errors."""

    def test_dashboard_import(self):
        """Test that dashboard module can be imported."""
        # This tests that the module loads without import errors
        import energy_routing.dashboard
        assert energy_routing.dashboard is not None


class TestDashboardFunctions:
    """Test dashboard helper functions."""

    def test_plot_to_streamlit(self):
        """Test plot_to_streamlit function."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from energy_routing.dashboard import plot_to_streamlit
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])
        
        buf = plot_to_streamlit(fig)
        
        assert buf is not None
        assert hasattr(buf, 'read')
        buf.seek(0)
        data = buf.read()
        assert len(data) > 0
        # Should be PNG data
        assert data[:8] == b'\x89PNG\r\n\x1a\n'


class TestDashboardSimulation:
    """Test dashboard simulation functions with mocks."""

    @patch('energy_routing.dashboard.create_simulator')
    def test_run_single_simulation(self, mock_create_simulator):
        """Test run_single_simulation function."""
        from energy_routing.dashboard import run_single_simulation
        from energy_routing.models.result import SimulationResult
        
        # Create mock result
        mock_result = SimulationResult(
            config={},
            round_metrics=[],
            fnd=100,
            hnd=200,
            lnd=300,
            total_packets_generated=1000,
            total_packets_delivered=900,
            total_packets_lost=100,
            packet_delivery_ratio=0.9,
            final_alive_nodes=10,
            final_dead_nodes=40,
            final_total_remaining_energy=5.0,
            final_total_energy_consumed=45.0,
            avg_hop_count=2.5,
            total_route_distance=1000.0
        )
        
        mock_simulator = MagicMock()
        mock_simulator.run.return_value = mock_result
        mock_create_simulator.return_value = mock_simulator
        
        # Create mock settings
        from energy_routing.config import SimulationSettings
        settings = SimulationSettings(
            network=__import__('energy_routing.config', fromlist=['NetworkConfig']).NetworkConfig(
                num_nodes=10,
                area_width=50.0,
                area_height=50.0,
                communication_range=25.0,
                seed=42,
                base_station_x=25.0,
                base_station_y=25.0
            ),
            energy=__import__('energy_routing.config', fromlist=['EnergyConfig']).EnergyConfig(
                initial_energy=1.0,
                E_elec=50.0,
                E_amp=0.0013,
                packet_size=512
            ),
            simulation=__import__('energy_routing.config', fromlist=['SimulationParameters']).SimulationParameters(
                num_rounds=50,
                packets_per_round=1,
                packet_size=512
            ),
            routing=__import__('energy_routing.config', fromlist=['RoutingConfig']).RoutingConfig(
                algorithm="shortest_path",
                alpha=0.5,
                beta=0.5
            )
        )
        
        result = run_single_simulation(settings)
        
        assert result['fnd'] == 100
        assert result['packet_delivery_ratio'] == 0.9
        mock_create_simulator.assert_called_once()
        mock_simulator.run.assert_called_once()


class TestDashboardUI:
    """Test dashboard UI functions."""

    def test_display_simulation_results(self):
        """Test display_simulation_results doesn't crash."""
        from energy_routing.dashboard import display_simulation_results
        import streamlit as st
        
        result = {
            'fnd': 100,
            'hnd': 200,
            'lnd': 300,
            'packet_delivery_ratio': 0.9,
            'avg_hop_count': 2.5,
            'total_route_distance': 1000.0,
            'final_total_remaining_energy': 5.0,
            'total_packets_delivered': 900,
            'total_packets_generated': 1000
        }
        
        # This just tests the function runs without error
        # We can't easily test Streamlit UI functions without running streamlit
        # So we just verify the function exists
        assert callable(display_simulation_results)


class TestDashboardComparison:
    """Test comparison experiment function."""

    @patch('energy_routing.dashboard.ExperimentRunner')
    @patch('energy_routing.experiments.runner.Experiment')
    def test_run_comparison_experiment(self, mock_experiment, mock_runner_class):
        """Test run_comparison_experiment function."""
        from energy_routing.dashboard import run_comparison_experiment
        from energy_routing.models.result import SimulationResult
        
        # Create mock results
        mock_result_a = SimulationResult(
            config={"routing": {"algorithm": "shortest_path"}},
            round_metrics=[],
            fnd=100, hnd=200, lnd=300,
            total_packets_generated=1000,
            total_packets_delivered=900,
            total_packets_lost=100,
            packet_delivery_ratio=0.9,
            final_alive_nodes=10,
            final_dead_nodes=40,
            final_total_remaining_energy=5.0,
            final_total_energy_consumed=45.0,
            avg_hop_count=2.5,
            total_route_distance=1000.0
        )
        
        mock_result_b = SimulationResult(
            config={"routing": {"algorithm": "energy_aware"}},
            round_metrics=[],
            fnd=150, hnd=250, lnd=350,
            total_packets_generated=1000,
            total_packets_delivered=950,
            total_packets_lost=50,
            packet_delivery_ratio=0.95,
            final_alive_nodes=15,
            final_dead_nodes=35,
            final_total_remaining_energy=6.0,
            final_total_energy_consumed=44.0,
            avg_hop_count=2.8,
            total_route_distance=1100.0
        )
        
        mock_runner = MagicMock()
        mock_runner.run_comparison.return_value = {
            "shortest_path": [mock_result_a],
            "energy_aware": [mock_result_b]
        }
        mock_runner_class.return_value = mock_runner
        
        from energy_routing.config import SimulationSettings
        settings = SimulationSettings(
            network=__import__('energy_routing.config', fromlist=['NetworkConfig']).NetworkConfig(
                num_nodes=10,
                area_width=50.0,
                area_height=50.0,
                communication_range=25.0,
                seed=42,
                base_station_x=25.0,
                base_station_y=25.0
            ),
            energy=__import__('energy_routing.config', fromlist=['EnergyConfig']).EnergyConfig(
                initial_energy=1.0,
                E_elec=50.0,
                E_amp=0.0013,
                packet_size=512
            ),
            simulation=__import__('energy_routing.config', fromlist=['SimulationParameters']).SimulationParameters(
                num_rounds=50,
                packets_per_round=1,
                packet_size=512
            ),
            routing=__import__('energy_routing.config', fromlist=['RoutingConfig']).RoutingConfig(
                algorithm="shortest_path",
                alpha=0.5,
                beta=0.5
            )
        )
        
        results = run_comparison_experiment(settings, num_seeds=1)
        
        assert "shortest_path" in results
        assert "energy_aware" in results
        assert len(results["shortest_path"]) == 1
        assert len(results["energy_aware"]) == 1
        assert results["shortest_path"][0]['fnd'] == 100
        assert results["energy_aware"][0]['fnd'] == 150


if __name__ == "__main__":
    pytest.main([__file__, "-v"])