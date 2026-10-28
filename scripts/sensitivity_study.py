"""
Controlled robustness and sensitivity study for Energy-Aware Routing.

One-factor-at-a-time design comparing shortest-path vs energy-aware routing
across varied network conditions. Results written to results/routing_sensitivity/.

Does NOT modify any simulation code or existing result files.
"""
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from energy_routing.config import (
    SimulationSettings, NetworkConfig, EnergyConfig,
    SimulationParameters, RoutingConfig, OutputConfig
)
from energy_routing.simulation import create_simulator

# Every execution gets its own directory; reruns never replace earlier results.
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
OUTPUT_DIR = PROJECT_ROOT / "results" / "routing_sensitivity" / RUN_ID
RAW_DIR = OUTPUT_DIR / "raw"

# Base configuration (from configs/base.yaml)
BASE = {
    'num_nodes': 50,
    'area_width': 100.0,
    'area_height': 100.0,
    'communication_range': 20.0,
    'seed': 42,
    'base_station_x': 50.0,
    'base_station_y': 50.0,
    'topology': 'random',
    'initial_energy': 1.0,
    'E_elec': 50.0,
    'E_amp': 0.0013,
    'packet_size': 512,
    'num_rounds': 1000,
    'packets_per_round': 1,
    'algorithm': 'shortest_path',
    'alpha': 0.5,
    'beta': 0.5,
}

# Seeds for paired runs
SEEDS = list(range(42, 52))  # 10 seeds: 42-51

# One-factor-at-a-time scenarios
SCENARIOS = [
    {
        'name': 'base_reference',
        'description': 'Base configuration: 50 nodes, range 20m, 1.0J, alpha=0.5',
        'overrides': {},
    },
    {
        'name': 'net_size_20',
        'description': 'Network size 20 nodes (smaller than baseline 50)',
        'overrides': {'num_nodes': 20},
    },
    {
        'name': 'net_size_100',
        'description': 'Network size 100 nodes (larger than baseline 50)',
        'overrides': {'num_nodes': 100},
    },
    {
        'name': 'comm_range_15m',
        'description': 'Communication range 15m (smaller than baseline 20m)',
        'overrides': {'communication_range': 15.0},
    },
    {
        'name': 'comm_range_30m',
        'description': 'Communication range 30m (larger than baseline 20m)',
        'overrides': {'communication_range': 30.0},
    },
    {
        'name': 'init_energy_0.5J',
        'description': 'Initial energy 0.5J (lower than baseline 1.0J)',
        'overrides': {'initial_energy': 0.5},
    },
    {
        'name': 'init_energy_2.0J',
        'description': 'Initial energy 2.0J (higher than baseline 1.0J)',
        'overrides': {'initial_energy': 2.0},
    },
    {
        'name': 'ea_alpha_0.25',
        'description': 'Energy-aware alpha=0.25, beta=0.75 (more energy-focused)',
        'overrides': {'alpha': 0.25, 'beta': 0.75},
    },
    {
        'name': 'ea_alpha_0.75',
        'description': 'Energy-aware alpha=0.75, beta=0.25 (more distance-focused)',
        'overrides': {'alpha': 0.75, 'beta': 0.25},
    },
]


def make_settings(seed, algorithm, overrides):
    """Build SimulationSettings from base config + overrides."""
    cfg = dict(BASE)
    cfg.update(overrides)
    cfg['seed'] = seed
    # The loop's algorithm is the experimental contrast; scenario overrides
    # may vary weights but must not silently replace the requested strategy.
    cfg['algorithm'] = algorithm

    return SimulationSettings(
        network=NetworkConfig(
            num_nodes=cfg['num_nodes'],
            area_width=cfg['area_width'],
            area_height=cfg['area_height'],
            communication_range=cfg['communication_range'],
            seed=cfg['seed'],
            base_station_x=cfg['base_station_x'],
            base_station_y=cfg['base_station_y'],
            topology=cfg['topology'],
        ),
        energy=EnergyConfig(
            initial_energy=cfg['initial_energy'],
            E_elec=cfg['E_elec'],
            E_amp=cfg['E_amp'],
            packet_size=cfg['packet_size'],
        ),
        simulation=SimulationParameters(
            num_rounds=cfg['num_rounds'],
            packets_per_round=cfg['packets_per_round'],
            packet_size=cfg['packet_size'],
        ),
        routing=RoutingConfig(
            algorithm=cfg['algorithm'],
            alpha=cfg['alpha'],
            beta=cfg['beta'],
        ),
        output=OutputConfig(
            results_dir=str(OUTPUT_DIR),
            save_results=False,
            generate_plots=False,
        ),
    )


def _write_json_atomic(path, data):
    """Write a complete JSON artifact without exposing a partial final file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _settings_fingerprint(settings):
    payload = json.dumps(asdict(settings), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def run_single(seed, algorithm, overrides):
    """Run a single simulation and return the result dict."""
    settings = make_settings(seed, algorithm, overrides)
    safe_name = overrides.get('_scenario_name', 'unknown').replace(' ', '_').replace('.', '_')
    fingerprint = _settings_fingerprint(settings)
    run_file = RAW_DIR / f'sens_{safe_name}_{algorithm}_seed{seed}_{fingerprint}.json'
    if run_file.exists():
        print(f"  seed={seed:3d} {algorithm:16s} SKIP (matching configuration already exists)", flush=True)
        with open(run_file) as f:
            return json.load(f)

    t0 = time.perf_counter()
    sim = create_simulator(settings)
    result = sim.run()
    t1 = time.perf_counter()

    d = result.to_dict()
    d['_seed'] = seed
    d['_algorithm'] = algorithm
    d['_time_s'] = round(t1 - t0, 3)
    d['_scenario'] = overrides.get('_scenario_name', 'unknown')
    d['_overrides'] = {k: v for k, v in overrides.items() if k != '_scenario_name'}
    d['_settings_fingerprint'] = fingerprint
    _write_json_atomic(run_file, d)
    return d


def run_scenario(scenario):
    """Run a full scenario: 10 seeds x 2 algorithms = 20 runs."""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"Seeds: {SEEDS}")
    print(f"{'='*70}", flush=True)

    results = []
    for seed in SEEDS:
        for algo in ['shortest_path', 'energy_aware']:
            overrides = dict(scenario['overrides'])
            overrides['_scenario_name'] = scenario['name']

            d = run_single(seed, algo, overrides)
            results.append(d)

            print(f"  seed={seed:3d} {algo:16s} PDR={d['packet_delivery_ratio']:.4f} "
                  f"FND={d['fnd']} HND={d['hnd']} LND={d['lnd']} "
                  f"time={d['_time_s']:.1f}s", flush=True)

    # Save scenario results
    safe_name = scenario['name'].replace(' ', '_').replace('.', '_')
    scenario_file = OUTPUT_DIR / f'{safe_name}_results.json'
    _write_json_atomic(scenario_file, results)

    # Print per-seed paired summary
    print(f"\n  Paired summary for {scenario['name']}:")
    print(f"  {'Seed':>5} | {'SP FND':>7} {'EA FND':>7} | {'EA-SP FND':>9} | {'SP PDR':>8} {'EA PDR':>8}")
    print(f"  {'-'*5} | {'-'*7} {'-'*7} | {'-'*9} | {'-'*8} {'-'*8}")

    sp_by_seed = {r['_seed']: r for r in results if r['_algorithm'] == 'shortest_path'}
    ea_by_seed = {r['_seed']: r for r in results if r['_algorithm'] == 'energy_aware'}

    for seed in SEEDS:
        sp = sp_by_seed[seed]
        ea = ea_by_seed[seed]
        sp_fnd = sp['fnd']
        ea_fnd = ea['fnd']
        diff = (ea_fnd - sp_fnd) if (ea_fnd is not None and sp_fnd is not None) else None
        print(f"  {seed:>5} | {str(sp_fnd):>7} {str(ea_fnd):>7} | {str(diff):>9} | "
              f"{sp['packet_delivery_ratio']:>8.4f} {ea['packet_delivery_ratio']:>8.4f}")

    return results


if __name__ == '__main__':
    import sys

    # Parse arguments: scenario names and optional --seeds=start,end
    args = sys.argv[1:]
    scenario_names = []
    seed_range = None
    for arg in args:
        if arg.startswith('--seeds='):
            seed_range = arg.split('=', 1)[1]
        else:
            scenario_names.append(arg)

    if scenario_names:
        scenarios_to_run = [s for s in SCENARIOS if s['name'] in scenario_names]
        if not scenarios_to_run:
            print(f"Unknown scenario names: {scenario_names}")
            print(f"Available: {[s['name'] for s in SCENARIOS]}")
            sys.exit(1)
    else:
        scenarios_to_run = SCENARIOS

    # Override seeds if specified
    if seed_range:
        try:
            start, end = seed_range.split('-')
            SEEDS.clear()
            SEEDS.extend(range(int(start), int(end) + 1))
        except ValueError:
            print(f"Invalid seed range: {seed_range}. Use format --seeds=42-51")
            sys.exit(1)

    print(f"Using seeds: {SEEDS}")

    all_results = []
    for scenario in scenarios_to_run:
        results = run_scenario(scenario)
        all_results.extend(results)

    # Save all combined results
    combined_file = OUTPUT_DIR / 'all_sensitivity_results.json'
    _write_json_atomic(combined_file, all_results)

    print(f"\n{'='*70}")
    print(f"ALL SCENARIOS COMPLETE")
    print(f"Total runs: {len(all_results)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'='*70}")
