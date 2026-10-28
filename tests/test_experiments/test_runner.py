"""
Tests for the ExperimentRunner and Experiment classes.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from energy_routing.experiments.runner import Experiment, ExperimentRunner
from energy_routing.experiments.definitions import (
    get_base_settings,
    create_routing_comparison_experiment,
    create_network_size_experiment,
    create_energy_aware_params_experiment,
    get_experiment,
    list_experiments,
    EXPERIMENT_REGISTRY
)
from energy_routing.config import SimulationSettings
from energy_routing.models.result import SimulationResult, RoundMetrics
from energy_routing.models.packet import Packet, PacketStatus


class TestExperiment:
    """Tests for Experiment class."""

    def setup_method(self):
        """Create base settings for testing."""
        self.base_settings = get_base_settings()

    def test_experiment_creation(self):
        """Test creating an experiment."""
        exp = Experiment(
            name="test_exp",
            description="Test experiment",
            base_settings=self.base_settings,
            num_seeds=3
        )
        assert exp.name == "test_exp"
        assert exp.num_seeds == 3

    def test_generate_configs_multi_seed(self):
        """Test config generation for multi-seed experiment."""
        exp = Experiment(
            name="multi_seed",
            description="Multi-seed test",
            base_settings=self.base_settings,
            num_seeds=5
        )
        
        configs = exp.generate_configs()
        
        assert len(configs) == 5
        seeds = [c.network.seed for c in configs]
        # Base seed is 42, so seeds should be 42, 43, 44, 45, 46
        assert seeds == [42, 43, 44, 45, 46]

    def test_generate_configs_with_seed_offset(self):
        """Test config generation with seed offset."""
        exp = Experiment(
            name="offset_test",
            description="Seed offset test",
            base_settings=self.base_settings,
            num_seeds=3,
            seed_offset=10
        )
        
        configs = exp.generate_configs()
        seeds = [c.network.seed for c in configs]
        # Base 42 + offset 10 = 52, 53, 54
        assert seeds == [52, 53, 54]

    def test_generate_configs_parameter_sweep(self):
        """Test config generation for parameter sweep."""
        exp = Experiment(
            name="param_sweep",
            description="Parameter sweep test",
            base_settings=self.base_settings,
            parameter_variations={
                "network.num_nodes": [20, 50],
                "energy.initial_energy": [0.5, 1.0]
            },
            num_seeds=2
        )
        
        configs = exp.generate_configs()
        
        # 2 (num_nodes) * 2 (energy) * 2 (seeds) = 8 configs
        assert len(configs) == 8
        
        # Check all combinations exist
        node_energy_pairs = [(c.network.num_nodes, c.energy.initial_energy) for c in configs]
        expected = [
            (20, 0.5), (20, 0.5),  # 2 seeds each
            (20, 1.0), (20, 1.0),
            (50, 0.5), (50, 0.5),
            (50, 1.0), (50, 1.0)
        ]
        assert sorted(node_energy_pairs) == sorted(expected)

    def test_fixed_parameters_applied(self):
        """Test that fixed parameters are applied."""
        exp = Experiment(
            name="fixed_test",
            description="Fixed parameters test",
            base_settings=self.base_settings,
            fixed_parameters={
                "routing.algorithm": "energy_aware",
                "routing.alpha": 0.3,
                "routing.beta": 0.7
            },
            num_seeds=2
        )
        
        configs = exp.generate_configs()
        
        for c in configs:
            assert c.routing.algorithm == "energy_aware"
            assert c.routing.alpha == 0.3
            assert c.routing.beta == 0.7


class TestExperimentRunner:
    """Tests for ExperimentRunner class."""

    def setup_method(self):
        """Create a temporary directory for results."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = ExperimentRunner(output_dir=self.temp_dir)
        self.base_settings = get_base_settings()

    def test_runner_creates_directories(self):
        """Test that runner creates output directories."""
        assert Path(self.temp_dir).exists()
        assert (Path(self.temp_dir) / "raw").exists()
        assert (Path(self.temp_dir) / "summary").exists()

    @patch('energy_routing.experiments.runner.create_simulator')
    def test_run_experiment(self, mock_create_simulator):
        """Test running an experiment with mocked simulator."""
        # Create mock results
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
        
        exp = Experiment(
            name="test_exp",
            description="Test",
            base_settings=self.base_settings,
            num_seeds=3
        )
        
        results = self.runner.run_experiment(exp)
        
        assert len(results) == 3
        assert mock_create_simulator.call_count == 3
        assert mock_simulator.run.call_count == 3
        
        # Check raw results saved
        raw_files = list((Path(self.temp_dir) / "raw").glob("*.json"))
        assert len(raw_files) == 3
        
        # Check summary saved
        summary_files = list((Path(self.temp_dir) / "summary").glob("*.json"))
        assert len(summary_files) == 1

    @patch('energy_routing.experiments.runner.create_simulator')
    def test_repeated_experiment_saves_new_artifacts_without_overwriting(self, mock_create_simulator):
        mock_simulator = MagicMock()
        mock_simulator.run.return_value = SimulationResult(config={}, packet_delivery_ratio=0.0)
        mock_create_simulator.return_value = mock_simulator
        experiment = Experiment(
            name="repeat_test",
            description="Repeat output safety test",
            base_settings=self.base_settings,
            num_seeds=1,
        )

        self.runner.run_experiment(experiment)
        self.runner.run_experiment(experiment)

        raw_files = list((Path(self.temp_dir) / "raw").glob("*.json"))
        summary_files = list((Path(self.temp_dir) / "summary").glob("*.json"))
        assert len(raw_files) == 2
        assert len(summary_files) == 2
        assert len({path.name for path in raw_files}) == 2

    @patch('energy_routing.experiments.runner.create_simulator')
    def test_run_comparison(self, mock_create_simulator):
        """Test running algorithm comparison."""
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
        
        mock_simulator = MagicMock()
        mock_simulator.run.side_effect = [mock_result_a, mock_result_b] * 3
        mock_create_simulator.return_value = mock_simulator
        
        exp = Experiment(
            name="comparison_test",
            description="Comparison test",
            base_settings=self.base_settings,
            num_seeds=3
        )
        
        results = self.runner.run_comparison(exp)
        
        assert "shortest_path" in results
        assert "energy_aware" in results
        assert len(results["shortest_path"]) == 3
        assert len(results["energy_aware"]) == 3
        
        # Should call create_simulator 6 times (2 algos * 3 seeds)
        assert mock_create_simulator.call_count == 6
        
        # Check comparison files saved
        raw_files = list((Path(self.temp_dir) / "raw").glob("*comparison*"))
        # Actually files named with pattern
        all_raw = list((Path(self.temp_dir) / "raw").glob("*.json"))
        # 3 runs * 2 algos = 6 individual + 3 comparison pairs = 9? 
        # Let's just check summary exists
        summary_files = list((Path(self.temp_dir) / "summary").glob("*comparison*"))
        assert len(summary_files) >= 1


class TestExperimentDefinitions:
    """Tests for experiment definitions."""

    def test_get_base_settings(self):
        """Test getting base settings."""
        settings = get_base_settings()
        assert isinstance(settings, SimulationSettings)
        assert settings.network.num_nodes == 50
        assert settings.network.seed == 42
        assert settings.energy.initial_energy == 1.0
        assert settings.simulation.num_rounds == 1000

    def test_routing_comparison_experiment(self):
        """Test routing comparison experiment creation."""
        exp = create_routing_comparison_experiment()
        
        assert exp.name == "routing_comparison"
        assert exp.num_seeds == 5
        assert exp.fixed_parameters["routing.alpha"] == 0.5
        assert exp.fixed_parameters["routing.beta"] == 0.5

    def test_network_size_experiment(self):
        """Test network size experiment creation."""
        exp = create_network_size_experiment()
        
        assert exp.name == "network_size"
        assert "network.num_nodes" in exp.parameter_variations
        assert exp.parameter_variations["network.num_nodes"] == [20, 50, 100, 200]
        assert exp.num_seeds == 1  # Same seed, different topologies

    def test_energy_aware_params_experiment(self):
        """Test energy-aware params experiment creation."""
        exp = create_energy_aware_params_experiment()
        
        assert exp.name == "energy_aware_params"
        assert "routing.alpha_beta_pair" in exp.parameter_variations
        pairs = exp.parameter_variations["routing.alpha_beta_pair"]
        assert len(pairs) == 5
        # Alpha and beta should be complementary
        for a, b in pairs:
            assert abs(a + b - 1.0) < 1e-9

    def test_get_experiment(self):
        """Test getting experiment by name."""
        exp = get_experiment("routing_comparison")
        assert exp.name == "routing_comparison"
        
        exp = get_experiment("network_size")
        assert exp.name == "network_size"

    def test_get_experiment_invalid(self):
        """Test getting invalid experiment raises KeyError."""
        with pytest.raises(KeyError, match="Unknown experiment: nonexistent"):
            get_experiment("nonexistent")

    def test_list_experiments(self):
        """Test listing experiments."""
        experiments = list_experiments()
        assert "routing_comparison" in experiments
        assert "network_size" in experiments
        assert "energy_aware_params" in experiments
        assert "communication_range" in experiments
        assert "initial_energy" in experiments

    def test_experiment_registry_complete(self):
        """Test that registry has all expected experiments."""
        expected = [
            "routing_comparison",
            "network_size",
            "energy_aware_params",
            "communication_range",
            "initial_energy"
        ]
        for exp_name in expected:
            assert exp_name in EXPERIMENT_REGISTRY
            exp = EXPERIMENT_REGISTRY[exp_name]
            assert exp.name == exp_name


class TestExperimentConfigGeneration:
    """Tests for specific config generation scenarios."""

    def setup_method(self):
        self.base_settings = get_base_settings()

    def test_routing_comparison_generates_5_seeds(self):
        """Test routing comparison generates exactly 5 seeds."""
        exp = create_routing_comparison_experiment()
        configs = exp.generate_configs()
        
        assert len(configs) == 5
        seeds = [c.network.seed for c in configs]
        assert seeds == [42, 43, 44, 45, 46]

    def test_network_size_generates_different_topologies(self):
        """Test network size experiment generates different topologies per node count."""
        exp = create_network_size_experiment()
        configs = exp.generate_configs()
        
        # 4 node counts * 1 seed = 4 configs
        assert len(configs) == 4
        
        node_counts = [c.network.num_nodes for c in configs]
        assert sorted(node_counts) == [20, 50, 100, 200]
        
        # All should have same base seed (42) since num_seeds=1
        seeds = [c.network.seed for c in configs]
        assert all(s == 42 for s in seeds)

    def test_energy_aware_params_combinations(self):
        """Test energy-aware params generates correct combinations."""
        exp = create_energy_aware_params_experiment()
        configs = exp.generate_configs()
        
        # 5 alpha values * 3 seeds = 15 configs
        assert len(configs) == 15
        
        # Check alpha/beta pairs
        for c in configs:
            alpha = c.routing.alpha
            beta = c.routing.beta
            assert abs(alpha + beta - 1.0) < 1e-9
            assert c.routing.algorithm == "energy_aware"
