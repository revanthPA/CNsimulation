import pytest

from energy_routing.metrics.paired import compare_paired_lifetimes


def result(seed, fnd, algorithm, num_rounds=10):
    return {
        "config": {
            "network": {"seed": seed},
            "simulation": {"num_rounds": num_rounds},
            "routing": {"algorithm": algorithm, "alpha": 0.5, "beta": 0.5},
        },
        "fnd": fnd,
    }


def test_unobserved_fnd_is_censored_at_horizon_and_paired_ci_is_reproducible():
    shortest = [result(1, 4, "shortest_path"), result(2, None, "shortest_path")]
    energy_aware = [result(1, 6, "energy_aware"), result(2, 8, "energy_aware")]

    first = compare_paired_lifetimes(shortest, energy_aware, bootstrap_samples=500)
    second = compare_paired_lifetimes(shortest, energy_aware, bootstrap_samples=500)

    assert first["restricted_mean_fnd_a"] == pytest.approx(7.0)
    assert first["restricted_mean_fnd_b"] == pytest.approx(7.0)
    assert first["mean_paired_difference"] == pytest.approx(0.0)
    assert first["censored_a"] == 1
    assert first["censored_b"] == 0
    assert first["bootstrap_95_ci"] == second["bootstrap_95_ci"]


def test_pairing_rejects_different_seeds():
    with pytest.raises(ValueError, match="same seed"):
        compare_paired_lifetimes(
            [result(1, 4, "shortest_path")],
            [result(2, 6, "energy_aware")],
        )


def test_pairing_rejects_different_non_algorithm_settings():
    other = result(1, 6, "energy_aware")
    other["config"]["network"]["num_nodes"] = 100
    with pytest.raises(ValueError, match="other than routing.algorithm"):
        compare_paired_lifetimes([result(1, 4, "shortest_path")], [other])


def test_single_pair_has_no_bootstrap_interval():
    summary = compare_paired_lifetimes(
        [result(1, 4, "shortest_path")],
        [result(1, 6, "energy_aware")],
    )
    assert summary["mean_paired_difference"] == 2
    assert summary["bootstrap_95_ci"] is None
