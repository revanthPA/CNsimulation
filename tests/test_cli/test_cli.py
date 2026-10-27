"""
Tests for CLI argument validation and error behavior.

Covers:
- Missing required arguments
- Invalid subcommands
- run command with missing config
- list-experiments command
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch
from energy_routing.main import main, list_experiments_cmd, run_simulation


class TestCLIArgumentValidation:
    """Tests for CLI argument parsing and validation."""

    def test_main_no_args_exits(self):
        """Test that main() with no args exits with error code."""
        with patch.object(sys, 'argv', ['energy_routing.main']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_main_unknown_command_exits(self):
        """Test that main() with unknown command exits with error."""
        with patch.object(sys, 'argv', ['energy_routing.main', 'unknown_cmd']):
            with pytest.raises(SystemExit):
                main()

    def test_main_run_missing_config(self):
        """Test that 'run' without --config exits with error."""
        with patch.object(sys, 'argv', ['energy_routing.main', 'run']):
            with pytest.raises(SystemExit):
                main()

    def test_main_list_experiments(self):
        """Test that 'list-experiments' runs without error."""
        with patch.object(sys, 'argv', ['energy_routing.main', 'list-experiments']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass
            output = mock_stdout.getvalue()
            assert "Available experiments" in output
            assert "routing_comparison" in output


class TestRunSimulationFunction:
    """Tests for run_simulation function directly."""

    def test_run_simulation_nonexistent_config(self):
        """Test that run_simulation raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            run_simulation("/nonexistent/config.yaml")

    def test_run_simulation_valid_config(self, tmp_path):
        """Test that run_simulation works with a valid config."""
        # Create a minimal valid config
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text("""
network:
  num_nodes: 5
  area_width: 50.0
  area_height: 50.0
  communication_range: 30.0
  seed: 42
  base_station_x: 25.0
  base_station_y: 25.0
  topology: "random"
energy:
  initial_energy: 1.0
  E_elec: 50.0
  E_amp: 0.0013
  packet_size: 512
simulation:
  num_rounds: 5
  packets_per_round: 1
  packet_size: 512
routing:
  algorithm: "shortest_path"
  alpha: 0.5
  beta: 0.5
output:
  results_dir: "results"
  save_results: false
  generate_plots: false
  plot_format: "png"
""")
        result = run_simulation(str(config_path))
        assert result is not None
        assert result.total_packets_generated >= 0
        assert 0.0 <= result.packet_delivery_ratio <= 1.0


class TestListExperimentsFunction:
    """Tests for list_experiments_cmd function."""

    def test_list_experiments_output(self):
        """Test that list_experiments_cmd prints experiment list."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            list_experiments_cmd()
        output = mock_stdout.getvalue()
        assert "Available experiments" in output
        assert "routing_comparison" in output
        assert "network_size" in output