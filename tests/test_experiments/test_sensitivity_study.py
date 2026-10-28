from scripts.sensitivity_study import SCENARIOS, make_settings


def test_alpha_sensitivity_scenarios_compare_both_algorithms_at_same_weights():
    for scenario in SCENARIOS:
        if not scenario["name"].startswith("ea_alpha_"):
            continue
        overrides = scenario["overrides"]
        shortest = make_settings(42, "shortest_path", overrides)
        energy_aware = make_settings(42, "energy_aware", overrides)

        assert shortest.routing.algorithm == "shortest_path"
        assert energy_aware.routing.algorithm == "energy_aware"
        assert shortest.network.seed == energy_aware.network.seed == 42
        assert shortest.routing.alpha == energy_aware.routing.alpha
        assert shortest.routing.beta == energy_aware.routing.beta


def test_sensitivity_run_has_a_unique_output_directory():
    from scripts.sensitivity_study import OUTPUT_DIR, RAW_DIR

    assert RAW_DIR.parent == OUTPUT_DIR
    assert "routing_sensitivity" in OUTPUT_DIR.parts
    assert OUTPUT_DIR.name.count("_") >= 1
