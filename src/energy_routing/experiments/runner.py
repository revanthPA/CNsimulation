"""
Experiment runner for Wireless Sensor Network simulation.

Defines experiment classes and runner for executing controlled comparisons.
"""

import copy
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
from uuid import uuid4

from energy_routing.config import SimulationSettings
from energy_routing.simulation import create_simulator
from energy_routing.models.result import SimulationResult
from energy_routing.metrics.paired import compare_paired_lifetimes


def write_json_atomic(filepath: Path, data: Any) -> None:
    """Atomically write JSON so readers never observe a partial result file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=filepath.parent,
            prefix=f".{filepath.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            json.dump(data, stream, indent=2, default=str)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, filepath)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


@dataclass
class Experiment:
    """
    Represents a single simulation experiment configuration.
    
    Attributes:
        name: Unique experiment name
        description: Human-readable description
        base_settings: Base simulation settings
        parameter_variations: Dict of parameter names to lists of values to vary
        fixed_parameters: Dict of parameters that remain fixed
        num_seeds: Number of random seeds to run (for multi-seed experiments)
        seed_offset: Starting seed offset
    """
    name: str
    description: str
    base_settings: SimulationSettings
    parameter_variations: Dict[str, List[Any]] = field(default_factory=dict)
    fixed_parameters: Dict[str, Any] = field(default_factory=dict)
    num_seeds: int = 1
    seed_offset: int = 0
    
    def generate_configs(self) -> List[SimulationSettings]:
        """
        Generate all simulation configurations for this experiment.
        
        For multi-seed experiments: varies the seed.
        For parameter sweep experiments: varies specified parameters.
        
        Returns:
            List of SimulationSettings for each run
        """
        configs = []
        
        if self.parameter_variations:
            # Parameter sweep: generate all combinations
            import itertools
            param_names = list(self.parameter_variations.keys())
            param_values = list(self.parameter_variations.values())
            
            for combination in itertools.product(*param_values):
                for seed_idx in range(self.num_seeds):
                    settings = copy.deepcopy(self.base_settings)
                    
                    # Apply fixed parameters
                    for key, value in self.fixed_parameters.items():
                        self._set_nested_attr(settings, key, value)
                    
                    # Apply varied parameters
                    for param_name, param_value in zip(param_names, combination):
                        # Special handling for paired alpha/beta parameter
                        if param_name == "routing.alpha_beta_pair":
                            alpha, beta = param_value
                            self._set_nested_attr(settings, "routing.alpha", alpha)
                            self._set_nested_attr(settings, "routing.beta", beta)
                        else:
                            self._set_nested_attr(settings, param_name, param_value)
                    
                    # Set seed
                    base_seed = settings.network.seed
                    settings.network.seed = base_seed + self.seed_offset + seed_idx
                    
                    configs.append(settings)
        else:
            # Simple multi-seed experiment
            for seed_idx in range(self.num_seeds):
                settings = copy.deepcopy(self.base_settings)
                
                # Apply fixed parameters
                for key, value in self.fixed_parameters.items():
                    self._set_nested_attr(settings, key, value)
                
                # Set seed
                base_seed = settings.network.seed
                settings.network.seed = base_seed + self.seed_offset + seed_idx
                
                configs.append(settings)
        
        return configs
    
    def _set_nested_attr(self, obj: Any, attr_path: str, value: Any):
        """Set nested attribute using dot notation (e.g., 'network.num_nodes')."""
        parts = attr_path.split('.')
        current = obj
        for part in parts[:-1]:
            current = getattr(current, part)
        setattr(current, parts[-1], value)


class ExperimentRunner:
    """
    Runs experiments and collects results.
    
    Handles execution of multiple simulation runs with proper
    result collection and storage.
    """
    
    def __init__(self, output_dir: str = "results"):
        """
        Initialize experiment runner.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir = self.output_dir / "summary"
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = self._new_run_id()

    @staticmethod
    def _new_run_id() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    
    def run_experiment(self, experiment: Experiment) -> List[SimulationResult]:
        """
        Run a complete experiment.
        
        Args:
            experiment: Experiment to run
            
        Returns:
            List of SimulationResult objects
        """
        self.run_id = self._new_run_id()
        configs = experiment.generate_configs()
        results = []
        
        print(f"Running experiment: {experiment.name}")
        print(f"  Description: {experiment.description}")
        print(f"  Configurations: {len(configs)}")
        
        for i, settings in enumerate(configs):
            print(f"  Run {i+1}/{len(configs)} (seed={settings.network.seed})...")
            
            simulator = create_simulator(settings)
            result = simulator.run()
            results.append(result)
            
            # Save individual result
            self._save_result(result, experiment.name, i)
        
        # Save summary
        self._save_summary(results, experiment.name)
        
        print(f"  Completed: {len(results)} runs")
        return results
    
    def run_comparison(
        self,
        experiment: Experiment,
        algorithm_a: str = "shortest_path",
        algorithm_b: str = "energy_aware",
        alpha: float = 0.5,
        beta: float = 0.5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, List[SimulationResult]]:
        """
        Run a routing algorithm comparison experiment.
        
        Runs the same experiment with two different routing algorithms
        using the SAME seeds for fair comparison.
        
        Args:
            experiment: Base experiment (seed variations will be used)
            algorithm_a: First algorithm name
            algorithm_b: Second algorithm name
            alpha: Alpha for energy-aware routing
            beta: Beta for energy-aware routing
            
        Returns:
            Dict with 'algorithm_a' and 'algorithm_b' result lists
        """
        self.run_id = self._new_run_id()
        # Generate base configs (seeds only)
        base_configs = experiment.generate_configs()
        
        results_a = []
        results_b = []
        
        print(f"Running comparison: {algorithm_a} vs {algorithm_b}")
        print(f"  Seeds: {len(base_configs)}")
        
        for i, settings in enumerate(base_configs):
            print(f"  Seed {i+1}/{len(base_configs)} (seed={settings.network.seed})...")
            
            # Run with algorithm A
            settings_a = copy.deepcopy(settings)
            settings_a.routing.algorithm = algorithm_a
            settings_a.routing.alpha = alpha
            settings_a.routing.beta = beta
            simulator_a = create_simulator(settings_a)
            result_a = simulator_a.run()
            results_a.append(result_a)
            
            # Run with algorithm B (SAME seed)
            settings_b = copy.deepcopy(settings)
            settings_b.routing.algorithm = algorithm_b
            settings_b.routing.alpha = alpha
            settings_b.routing.beta = beta
            simulator_b = create_simulator(settings_b)
            result_b = simulator_b.run()
            results_b.append(result_b)
            
            # Save pair
            self._save_comparison_pair(result_a, result_b, experiment.name, i, algorithm_a, algorithm_b)
            if progress_callback is not None:
                progress_callback(i + 1, len(base_configs))
        
        # Save comparison summary
        self._save_comparison_summary(results_a, results_b, experiment.name, algorithm_a, algorithm_b)
        
        return {
            algorithm_a: results_a,
            algorithm_b: results_b
        }
    
    def _save_result(self, result: SimulationResult, experiment_name: str, run_idx: int):
        """Save individual simulation result to JSON."""
        filename = f"{experiment_name}_{self.run_id}_run{run_idx}.json"
        filepath = self.raw_dir / filename
        write_json_atomic(filepath, result.to_dict())
    
    def _save_summary(self, results: List[SimulationResult], experiment_name: str):
        """Save experiment summary."""
        # Compute basic statistics
        summary = {
            "experiment": experiment_name,
            "run_id": self.run_id,
            "num_runs": len(results),
            "results": []
        }
        
        for i, r in enumerate(results):
            summary["results"].append({
                "run_index": i,
                "seed": r.config.get("network", {}).get("seed", "unknown"),
                "fnd": r.fnd,
                "hnd": r.hnd,
                "lnd": r.lnd,
                "pdr": r.packet_delivery_ratio,
                "avg_hop_count": r.avg_hop_count,
                "total_route_distance": r.total_route_distance,
                "final_energy": r.final_total_remaining_energy,
                "total_packets_generated": r.total_packets_generated,
                "total_packets_delivered": r.total_packets_delivered,
                "total_packets_lost": r.total_packets_lost
            })
        
        filename = f"{experiment_name}_{self.run_id}_summary.json"
        filepath = self.summary_dir / filename
        write_json_atomic(filepath, summary)
    
    def _save_comparison_pair(
        self,
        result_a: SimulationResult,
        result_b: SimulationResult,
        experiment_name: str,
        run_idx: int,
        algo_a: str,
        algo_b: str
    ):
        """Save a comparison pair."""
        filename = f"{experiment_name}_{self.run_id}_{algo_a}_vs_{algo_b}_run{run_idx}.json"
        filepath = self.raw_dir / filename
        
        data = {
            "experiment": experiment_name,
            "run_index": run_idx,
            algo_a: result_a.to_dict(),
            algo_b: result_b.to_dict()
        }
        
        write_json_atomic(filepath, data)
    
    def _save_comparison_summary(
        self,
        results_a: List[SimulationResult],
        results_b: List[SimulationResult],
        experiment_name: str,
        algo_a: str,
        algo_b: str
    ):
        """Save comparison summary."""
        from energy_routing.metrics import MetricsCollector
        
        collector_a = MetricsCollector()
        collector_a.add_results(results_a)
        
        collector_b = MetricsCollector()
        collector_b.add_results(results_b)
        
        agg_a = collector_a.compute_aggregated_metrics()
        agg_b = collector_b.compute_aggregated_metrics()
        
        comparison = collector_a.compare_algorithms(results_a, results_b, algo_a, algo_b)
        try:
            paired_lifetime = compare_paired_lifetimes(
                results_a, results_b, label_a=algo_a, label_b=algo_b
            )
        except ValueError as error:
            # Preserve outputs from legacy/mocked results, but make the
            # missing pairing metadata explicit in the saved summary.
            paired_lifetime = {"unavailable_reason": str(error)}
        
        summary = {
            "experiment": experiment_name,
            "run_id": self.run_id,
            "algorithm_a": algo_a,
            "algorithm_b": algo_b,
            "num_seeds": len(results_a),
            algo_a: agg_a.__dict__,
            algo_b: agg_b.__dict__,
            "comparison": comparison,
            "paired_lifetime_analysis": paired_lifetime,
        }
        
        filename = f"{experiment_name}_{self.run_id}_{algo_a}_vs_{algo_b}_summary.json"
        filepath = self.summary_dir / filename
        write_json_atomic(filepath, summary)
