#!/usr/bin/env python3
"""
Main CLI entry point for Energy-Aware Routing Protocol simulation.

Usage:
    python -m energy_routing.main run --config configs/base.yaml
    python -m energy_routing.main experiment --name routing_comparison --base-config configs/base.yaml
    python -m energy_routing.main list-experiments
"""

import argparse
import sys
from pathlib import Path

from energy_routing.config import load_config
from energy_routing.simulation import create_simulator
from energy_routing.experiments import (
    ExperimentRunner,
    get_experiment,
    list_experiments,
    create_all_experiments
)
from energy_routing.visualization import ResultVisualizer


def run_simulation(config_path: str, output_dir: str = None):
    """Run a single simulation from config file."""
    print(f"Loading configuration from: {config_path}")
    settings = load_config(config_path)
    
    print("Creating simulator...")
    simulator = create_simulator(settings)
    
    print("Running simulation...")
    result = simulator.run()
    
    print(f"\nSimulation Complete!")
    print(f"  Rounds completed: {len(result.round_metrics)}")
    print(f"  Packets generated: {result.total_packets_generated}")
    print(f"  Packets delivered: {result.total_packets_delivered}")
    print(f"  Packets lost: {result.total_packets_lost}")
    print(f"  PDR: {result.packet_delivery_ratio:.4f}")
    print(f"  FND: {result.fnd}")
    print(f"  HND: {result.hnd}")
    print(f"  LND: {result.lnd}")
    print(f"  Avg hop count: {result.avg_hop_count}")
    print(f"  Final energy: {result.final_total_remaining_energy:.4f} J")
    
    # Save results if output dir specified
    if output_dir or settings.output.save_results:
        out_dir = Path(output_dir or settings.output.results_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        result_file = out_dir / f"result_{settings.network.seed}.json"
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"Results saved to: {result_file}")
        
        # Generate visualizations
        if settings.output.generate_plots:
            generate_visualizations(result, settings, out_dir)
    
    return result


def run_experiment_cmd(name: str, base_config: str = None, output_dir: str = None):
    """Run a named experiment."""
    print(f"Running experiment: {name}")
    
    # Get experiment
    experiment = get_experiment(name)
    
    # Override base settings if config provided
    if base_config:
        base_settings = load_config(base_config)
        experiment.base_settings = base_settings
    
    # Create runner
    runner = ExperimentRunner(output_dir=output_dir or "results")
    
    # Run experiment
    if name == "routing_comparison":
        # Special handling for comparison
        results = runner.run_comparison(experiment)
        print(f"\nComparison complete!")
        print(f"  Seeds run: {len(results['shortest_path'])}")
        
        # Print summary
        for algo, res_list in results.items():
            fnds = [r.fnd for r in res_list if r.fnd is not None]
            pdr = [r.packet_delivery_ratio for r in res_list]
            print(f"  {algo}:")
            print(f"    FND: {fnds}")
            print(f"    Mean PDR: {sum(pdr)/len(pdr):.4f}")
    else:
        results = runner.run_experiment(experiment)
        print(f"\nExperiment complete!")
        print(f"  Runs completed: {len(results)}")
    
    return results


def list_experiments_cmd():
    """List all available experiments."""
    experiments = list_experiments()
    print("Available experiments:")
    for exp_name in experiments:
        exp = get_experiment(exp_name)
        print(f"  {exp_name}: {exp.description}")


def generate_visualizations(result, settings, output_dir: Path):
    """Generate visualization plots for simulation result."""
    try:
        print("Generating visualizations...")
        
        # Recreate topology and graph for plotting
        from energy_routing.network.topology import generate_topology
        from energy_routing.network.graph import build_graph
        
        topology = generate_topology(settings.network, settings.energy)
        graph = build_graph(topology, settings.network.communication_range)
        
        visualizer = ResultVisualizer()
        
        # Plot topology
        topology_path = output_dir / f"topology_{settings.network.seed}.png"
        visualizer.plot_alive_nodes_over_time(
            [result],
            save_path=str(topology_path)
        )
        # Actually use network_plot for topology
        from energy_routing.visualization.network_plot import plot_network_topology
        plot_network_topology(topology, graph, save_path=str(topology_path))
        
        # Plot energy heatmap
        heatmap_path = output_dir / f"energy_heatmap_{settings.network.seed}.png"
        from energy_routing.visualization.network_plot import plot_energy_heatmap
        plot_energy_heatmap(topology, graph, save_path=str(heatmap_path))
        
        # Plot alive nodes over time
        alive_path = output_dir / f"alive_nodes_{settings.network.seed}.png"
        visualizer.plot_alive_nodes_over_time([result], save_path=str(alive_path))
        
        # Plot energy over time
        energy_path = output_dir / f"energy_over_time_{settings.network.seed}.png"
        visualizer.plot_energy_over_time([result], save_path=str(energy_path))
        
        # Plot packets over time
        packets_path = output_dir / f"packets_{settings.network.seed}.png"
        visualizer.plot_packets_over_time([result], save_path=str(packets_path))
        
        print(f"Visualizations saved to: {output_dir}")
        
    except Exception as e:
        print(f"Warning: Failed to generate visualizations: {e}")


def launch_gui(port: int = 8501):
    """Launch the Streamlit GUI."""
    import subprocess
    dashboard_path = Path(__file__).parent / "dashboard.py"
    print(f"Launching Streamlit GUI from {dashboard_path} (port {port})...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port", str(port)]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nGUI stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Energy-Aware Routing Protocol for WSN - Simulation CLI"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run simulation command
    run_parser = subparsers.add_parser('run', help='Run single simulation')
    run_parser.add_argument('--config', '-c', required=True, help='Path to config YAML')
    run_parser.add_argument('--output', '-o', help='Output directory')
    
    # Run experiment command
    exp_parser = subparsers.add_parser('experiment', help='Run experiment')
    exp_parser.add_argument('--name', '-n', required=True, help='Experiment name')
    exp_parser.add_argument('--base-config', '-c', help='Base config YAML (optional)')
    exp_parser.add_argument('--output', '-o', help='Output directory')
    
    # List experiments command
    subparsers.add_parser('list-experiments', help='List available experiments')

    # Launch GUI command
    gui_parser = subparsers.add_parser('gui', help='Launch Streamlit GUI')
    gui_parser.add_argument('--port', '-p', type=int, default=8501, help='Port to run Streamlit on (default: 8501)')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_simulation(args.config, args.output)
    elif args.command == 'experiment':
        run_experiment_cmd(args.name, args.base_config, args.output)
    elif args.command == 'list-experiments':
        list_experiments_cmd()
    elif args.command == 'gui':
        launch_gui(args.port)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()