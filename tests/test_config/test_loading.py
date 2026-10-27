"""
Tests for configuration loading and validation error handling.

Covers:
- Missing configuration file
- Missing YAML keys
- Invalid configuration values
- Configuration validation edge cases
"""

import pytest
import tempfile
import os
from pathlib import Path
from energy_routing.config import (
    load_config, save_config, SimulationSettings,
    NetworkConfig, EnergyConfig, SimulationParameters,
    RoutingConfig, OutputConfig
)


class TestLoadConfigMissingFile:
    """Tests for load_config with missing files."""

    def test_load_config_file_not_found(self):
        """Test that load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_empty_file(self):
        """Test that load_config fails on empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            tmp_path = f.name
        try:
            with pytest.raises((TypeError, KeyError)):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_config_missing_network_key(self):
        """Test that load_config fails when 'network' key is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("energy:\n  initial_energy: 1.0\n")
            tmp_path = f.name
        try:
            with pytest.raises(KeyError):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestLoadConfigInvalidValues:
    """Tests for load_config with invalid configuration values."""

    def test_load_config_negative_num_nodes(self):
        """Test that negative num_nodes raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
network:
  num_nodes: -5
  area_width: 100.0
  area_height: 100.0
  communication_range: 20.0
  seed: 42
  base_station_x: 50.0
  base_station_y: 50.0
energy:
  initial_energy: 1.0
  E_elec: 50.0
  E_amp: 0.0013
  packet_size: 512
simulation:
  num_rounds: 100
  packets_per_round: 1
  packet_size: 512
routing:
  algorithm: "shortest_path"
  alpha: 0.5
  beta: 0.5
""")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="num_nodes must be > 0"):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_config_alpha_beta_not_sum_one(self):
        """Test that alpha + beta != 1 raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
network:
  num_nodes: 50
  area_width: 100.0
  area_height: 100.0
  communication_range: 20.0
  seed: 42
  base_station_x: 50.0
  base_station_y: 50.0
energy:
  initial_energy: 1.0
  E_elec: 50.0
  E_amp: 0.0013
  packet_size: 512
simulation:
  num_rounds: 100
  packets_per_round: 1
  packet_size: 512
routing:
  algorithm: "shortest_path"
  alpha: 0.3
  beta: 0.3
""")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="alpha \\+ beta must equal 1.0"):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestConfigValidation:
    """Tests for dataclass configuration validation."""

    def test_network_config_negative_area(self):
        """Test that negative area dimensions raise ValueError."""
        with pytest.raises(ValueError, match="area dimensions must be > 0"):
            NetworkConfig(
                num_nodes=10, area_width=-10.0, area_height=100.0,
                communication_range=20.0, seed=42,
                base_station_x=50.0, base_station_y=50.0
            )

    def test_network_config_zero_range(self):
        """Test that zero communication range raises ValueError."""
        with pytest.raises(ValueError, match="communication_range must be > 0"):
            NetworkConfig(
                num_nodes=10, area_width=100.0, area_height=100.0,
                communication_range=0.0, seed=42,
                base_station_x=50.0, base_station_y=50.0
            )

    def test_energy_config_negative_initial(self):
        """Test that negative initial energy raises ValueError."""
        with pytest.raises(ValueError, match="initial_energy must be > 0"):
            EnergyConfig(
                initial_energy=-1.0, E_elec=50.0, E_amp=0.0013, packet_size=512
            )

    def test_simulation_config_negative_rounds(self):
        """Test that negative num_rounds raises ValueError."""
        with pytest.raises(ValueError, match="num_rounds must be > 0"):
            SimulationParameters(
                num_rounds=-5, packets_per_round=1, packet_size=512
            )

    def test_routing_config_alpha_out_of_range(self):
        """Test that alpha outside [0,1] raises ValueError."""
        with pytest.raises(ValueError, match="alpha must be in \[0, 1\]"):
            RoutingConfig(
                algorithm="energy_aware", alpha=1.5, beta=-0.5
            )

    def test_routing_config_literal_type_hint(self):
        """Test that algorithm field accepts Literal values (type hint only, not runtime enforced)."""
        # Literal["shortest_path", "energy_aware"] is a type hint, not runtime validation
        # Any string is accepted at runtime; callers are responsible for valid values
        config = RoutingConfig(
            algorithm="shortest_path", alpha=0.5, beta=0.5
        )
        assert config.algorithm == "shortest_path"
        config = RoutingConfig(
            algorithm="energy_aware", alpha=0.5, beta=0.5
        )
        assert config.algorithm == "energy_aware"

    def test_save_config_roundtrip(self):
        """Test that save_config then load_config produces equivalent settings."""
        import tempfile
        settings = SimulationSettings(
            network=NetworkConfig(
                num_nodes=10, area_width=50.0, area_height=50.0,
                communication_range=25.0, seed=42,
                base_station_x=25.0, base_station_y=25.0
            ),
            energy=EnergyConfig(
                initial_energy=1.0, E_elec=50.0, E_amp=0.0013, packet_size=512
            ),
            simulation=SimulationParameters(
                num_rounds=50, packets_per_round=1, packet_size=512
            ),
            routing=RoutingConfig(
                algorithm="energy_aware", alpha=0.3, beta=0.7
            )
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            tmp_path = f.name
        try:
            save_config(settings, tmp_path)
            loaded = load_config(tmp_path)
            assert loaded.network.num_nodes == settings.network.num_nodes
            assert loaded.network.seed == settings.network.seed
            assert loaded.energy.initial_energy == settings.energy.initial_energy
            assert loaded.simulation.num_rounds == settings.simulation.num_rounds
            assert loaded.routing.algorithm == settings.routing.algorithm
            assert loaded.routing.alpha == settings.routing.alpha
            assert loaded.routing.beta == settings.routing.beta
        finally:
            os.unlink(tmp_path)