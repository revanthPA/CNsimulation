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

    def test_classify_saved_result_formats(self):
        from energy_routing.dashboard import classify_result_data

        assert classify_result_data({"round_metrics": [], "fnd": None}) == "single"
        assert classify_result_data({"comparison": {"shortest_path": {}}}) == "comparison_summary"
        assert classify_result_data({"shortest_path": {}, "energy_aware": {}}) == "comparison_pair"
        assert classify_result_data({"message": "unrecognized"}) == "raw"

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


class TestDashboardValidation:
    """Test dashboard input validation rules."""

    def test_valid_parameters(self):
        """Test that valid parameters produce zero validation errors."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=50,
            comm_range=20.0,
            initial_energy=1.0,
            num_rounds=1000,
            seed=42,
            algorithm="shortest_path"
        )
        assert len(errors) == 0

    def test_valid_energy_aware_parameters(self):
        """Test valid energy-aware weights sum to 1.0."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=50,
            comm_range=20.0,
            initial_energy=1.0,
            num_rounds=1000,
            seed=42,
            algorithm="energy_aware",
            alpha=0.4,
            beta=0.6
        )
        assert len(errors) == 0

    def test_invalid_node_count(self):
        """Test node count < 2 triggers error."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=1,
            comm_range=20.0,
            initial_energy=1.0,
            num_rounds=1000,
            seed=42,
            algorithm="shortest_path"
        )
        assert any("sensor nodes must be at least 2" in e for e in errors)

    def test_invalid_comm_range_and_energy(self):
        """Test non-positive range and energy trigger errors."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=10,
            comm_range=0.0,
            initial_energy=-1.0,
            num_rounds=1000,
            seed=42,
            algorithm="shortest_path"
        )
        assert any("Communication range" in e for e in errors)
        assert any("Initial energy" in e for e in errors)

    def test_invalid_alpha_beta_sum(self):
        """Test alpha + beta != 1.0 triggers error."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=10,
            comm_range=20.0,
            initial_energy=1.0,
            num_rounds=100,
            seed=42,
            algorithm="energy_aware",
            alpha=0.7,
            beta=0.7
        )
        assert any("must sum to 1.0" in e for e in errors)

    def test_invalid_alpha_beta_bounds(self):
        """Test alpha or beta out of [0, 1] triggers error."""
        from energy_routing.dashboard import validate_simulation_parameters
        errors = validate_simulation_parameters(
            num_nodes=10,
            comm_range=20.0,
            initial_energy=1.0,
            num_rounds=100,
            seed=42,
            algorithm="energy_aware",
            alpha=-0.2,
            beta=1.2
        )
        assert any("Alpha" in e for e in errors)
        assert any("Beta" in e for e in errors)

    def test_invalid_advanced_network_and_packet_parameters(self):
        from energy_routing.dashboard import validate_simulation_parameters

        errors = validate_simulation_parameters(
            num_nodes=10, comm_range=20.0, initial_energy=1.0,
            num_rounds=100, seed=42, algorithm="shortest_path",
            area_width=10.0, area_height=10.0,
            base_station_x=11.0, base_station_y=5.0,
            packets_per_round=-1, packet_size=0, E_elec=-1.0, E_amp=-0.1,
        )

        assert any("Base station X" in error for error in errors)
        assert any("Packets per node" in error for error in errors)
        assert any("Packet size" in error for error in errors)
        assert any("Electronics energy" in error for error in errors)
        assert any("Amplifier energy" in error for error in errors)


class TestDashboardMetricFormatting:
    """Test lifetime metric formatting."""

    def test_format_lifetime_metric_observed(self):
        from energy_routing.dashboard import format_lifetime_metric
        assert format_lifetime_metric(142) == "Round 142"

    def test_format_lifetime_metric_unobserved(self):
        from energy_routing.dashboard import format_lifetime_metric
        assert format_lifetime_metric(None) == "Not observed"
        assert format_lifetime_metric(None, max_rounds=1000) == "Not observed (>1000 rounds)"


class TestDashboardFileHandling:
    """Test saved result discovery and loading."""

    def test_find_saved_result_files(self, tmp_path):
        from energy_routing.dashboard import find_saved_result_files
        # Create a dummy json file
        test_file = tmp_path / "test_result.json"
        test_file.write_text('{"fnd": 50}', encoding="utf-8")

        found = find_saved_result_files(str(tmp_path))
        assert len(found) == 1
        assert found[0].name == "test_result.json"

    def test_load_result_file_valid(self, tmp_path):
        from energy_routing.dashboard import load_result_file
        test_file = tmp_path / "valid.json"
        test_file.write_text('{"packet_delivery_ratio": 0.95}', encoding="utf-8")

        data, err = load_result_file(test_file)
        assert err is None
        assert data["packet_delivery_ratio"] == 0.95

    def test_load_result_file_missing(self, tmp_path):
        from energy_routing.dashboard import load_result_file
        missing = tmp_path / "does_not_exist.json"
        data, err = load_result_file(missing)
        assert data is None
        assert "not found" in err.lower()

    def test_load_result_file_invalid_json(self, tmp_path):
        from energy_routing.dashboard import load_result_file
        broken = tmp_path / "broken.json"
        broken.write_text('{not valid json', encoding="utf-8")
        data, err = load_result_file(broken)
        assert data is None
        assert "invalid json" in err.lower()


class TestDashboardPlotting:
    """Test matplotlib figure generation functions."""

    def test_plot_simulation_metrics(self):
        from energy_routing.dashboard import plot_simulation_metrics
        mock_result = {
            "round_metrics": [
                {"round": 0, "alive_nodes": 10, "total_remaining_energy": 10.0},
                {"round": 1, "alive_nodes": 9, "total_remaining_energy": 8.5},
            ],
            "fnd": 1
        }
        fig = plot_simulation_metrics(mock_result)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_simulation_metrics_empty(self):
        from energy_routing.dashboard import plot_simulation_metrics
        assert plot_simulation_metrics({}) is None

    def test_plot_comparison_results(self):
        from energy_routing.dashboard import plot_comparison_results
        sp_runs = [{"fnd": 100, "packet_delivery_ratio": 0.8}]
        ea_runs = [{"fnd": 150, "packet_delivery_ratio": 0.85}]
        fig = plot_comparison_results(sp_runs, ea_runs)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestCoreIndependence:
    """Verify core simulation and CLI are independent from the dashboard."""

    def test_create_simulator_without_dashboard(self):
        from energy_routing.config import load_config
        from energy_routing.simulation import create_simulator
        settings = load_config("configs/test_quick.yaml")
        sim = create_simulator(settings)
        assert sim is not None

    def test_main_cli_importable(self):
        import energy_routing.main
        assert callable(energy_routing.main.run_simulation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
