"""Paired analysis helpers for algorithm comparisons."""

import random
import statistics
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _value(result: Any, name: str) -> Any:
    return result.get(name) if isinstance(result, dict) else getattr(result, name)


def _config(result: Any) -> Dict[str, Any]:
    return _value(result, "config") or {}


def _comparison_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the intended algorithm difference before validating each pair."""
    comparable = {key: value for key, value in config.items()}
    routing = dict(comparable.get("routing", {}))
    routing.pop("algorithm", None)
    comparable["routing"] = routing
    return comparable


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    """Linearly interpolated percentile for a sorted sequence."""
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return float(sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction)


def compare_paired_lifetimes(
    results_a: Sequence[Any],
    results_b: Sequence[Any],
    label_a: str = "shortest_path",
    label_b: str = "energy_aware",
    bootstrap_samples: int = 5000,
    random_seed: int = 0,
) -> Dict[str, Any]:
    """Compare paired, horizon-limited FND outcomes with a paired bootstrap.

    An unobserved FND is right-censored at the configured simulation horizon.
    The reported means therefore estimate restricted mean FND through that
    horizon, rather than averaging only runs that happened to observe a death.
    """
    if not results_a or len(results_a) != len(results_b):
        raise ValueError("Paired results must be non-empty and have equal lengths.")
    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be at least 1.")

    per_seed: List[Dict[str, Any]] = []
    times_a: List[float] = []
    times_b: List[float] = []
    differences: List[float] = []
    seen_seeds = set()

    for result_a, result_b in zip(results_a, results_b):
        config_a = _config(result_a)
        config_b = _config(result_b)
        network_a = config_a.get("network", {})
        network_b = config_b.get("network", {})
        seed_a, seed_b = network_a.get("seed"), network_b.get("seed")
        if seed_a != seed_b:
            raise ValueError(f"Paired runs must use the same seed (got {seed_a} and {seed_b}).")
        if _comparison_config(config_a) != _comparison_config(config_b):
            raise ValueError("Paired runs differ in settings other than routing.algorithm.")
        if seed_a is not None:
            if seed_a in seen_seeds:
                raise ValueError(f"Duplicate paired seed: {seed_a}.")
            seen_seeds.add(seed_a)

        rounds_a = config_a.get("simulation", {}).get("num_rounds")
        rounds_b = config_b.get("simulation", {}).get("num_rounds")
        if not isinstance(rounds_a, int) or rounds_a < 1 or rounds_a != rounds_b:
            raise ValueError("Paired runs must share a positive simulation round horizon.")
        horizon = rounds_a

        fnd_a = _value(result_a, "fnd")
        fnd_b = _value(result_b, "fnd")
        restricted_a = float(horizon if fnd_a is None else min(fnd_a, horizon))
        restricted_b = float(horizon if fnd_b is None else min(fnd_b, horizon))
        difference = restricted_b - restricted_a
        times_a.append(restricted_a)
        times_b.append(restricted_b)
        differences.append(difference)
        per_seed.append({
            "seed": seed_a,
            label_a: fnd_a,
            label_b: fnd_b,
            f"{label_a}_censored": fnd_a is None,
            f"{label_b}_censored": fnd_b is None,
            "restricted_fnd_difference": difference,
        })

    mean_difference = statistics.mean(differences)
    ci: Optional[Tuple[float, float]] = None
    if len(differences) >= 2:
        rng = random.Random(random_seed)
        boot_means = sorted(
            statistics.mean(rng.choices(differences, k=len(differences)))
            for _ in range(bootstrap_samples)
        )
        ci = (_percentile(boot_means, 0.025), _percentile(boot_means, 0.975))

    return {
        "n_pairs": len(differences),
        "horizon_rounds": rounds_a,
        "restricted_mean_fnd_a": statistics.mean(times_a),
        "restricted_mean_fnd_b": statistics.mean(times_b),
        "mean_paired_difference": mean_difference,
        "median_paired_difference": statistics.median(differences),
        "bootstrap_95_ci": ci,
        "bootstrap_samples": bootstrap_samples if ci is not None else 0,
        "censored_a": sum(item[f"{label_a}_censored"] for item in per_seed),
        "censored_b": sum(item[f"{label_b}_censored"] for item in per_seed),
        "improved_pairs": sum(value > 0 for value in differences),
        "tied_pairs": sum(value == 0 for value in differences),
        "regressed_pairs": sum(value < 0 for value in differences),
        "per_seed": per_seed,
    }
