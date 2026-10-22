#!/usr/bin/env python3
"""
Streamlit Dashboard for Energy-Aware Routing Protocol Simulation.

Provides an interactive web interface for running simulations,
visualizing results, and comparing routing algorithms.

Run with: streamlit run src/energy_routing/dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from energy_routing.config import load_config, SimulationSettings
from energy_routing.simulation import create_simulator
from energy_routing.experiments import (
    ExperimentRunner,
    get_experiment,
    list_experiments
)
from energy_routing.visualization import ResultVisualizer, plot_network_topology, plot_energy_heatmap
from energy_routing.network.topology import generate_topology
from energy_routing.network.graph import build_graph
from energy_routing.metrics import MetricsCollector


# Page configuration
st.set_page_config(
    page_title="Energy-Aware Routing Protocol Simulator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Load custom CSS styles."""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .sidebar-section {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)


def run_single_simulation(settings: SimulationSettings) -> Dict[str, Any]:
    """Run a single simulation and return results as dict."""
    simulator = create_simulator(settings)
    result = simulator.run()
    return result.to_dict()


def run_comparison_experiment(base_settings: SimulationSettings, num_seeds: int = 5) -> Dict[str, List[Dict]]:
    """Run routing comparison experiment."""
    from energy_routing.experiments.runner import Experiment
    import copy
    
    exp = Experiment(
        name="routing_comparison",
        description="Compare shortest-path vs energy-aware routing",
        base_settings=base_settings,
        num_seeds=num_seeds,
        fixed_parameters={
            "routing.alpha": 0.5,
            "routing.beta": 0.5
        }
    )
    
    runner = ExperimentRunner(output_dir="results/dashboard")
    results = runner.run_comparison(exp)
    
    return {
        algo: [r.to_dict() for r in res_list]
        for algo, res_list in results.items()
    }


def plot_to_streamlit(fig):
    """Convert matplotlib figure to streamlit image."""
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


def display_simulation_results(result: Dict[str, Any]):
    """Display simulation results in a nice format."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("FND (First Node Death)", result.get('fnd') or "N/A")
    with col2:
        st.metric("HND (Half Node Death)", result.get('hnd') or "N/A")
    with col3:
        st.metric("LND (Last Node Death)", result.get('lnd') or "N/A")
    with col4:
        st.metric("PDR", f"{result.get('packet_delivery_ratio', 0):.4f}")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("Avg Hop Count", f"{result.get('avg_hop_count', 0):.2f}" if result.get('avg_hop_count') else "N/A")
    with col6:
        st.metric("Total Route Distance", f"{result.get('total_route_distance', 0):.1f}m" if result.get('total_route_distance') else "N/A")
    with col7:
        st.metric("Final Energy", f"{result.get('final_total_remaining_energy', 0):.4f} J")
    with col8:
        st.metric("Packets Delivered", f"{result.get('total_packets_delivered', 0)} / {result.get('total_packets_generated', 0)}")


def plot_comparison_results(results_a: List[Dict], results_b: List[Dict], label_a: str, label_b: str):
    """Create comparison plots."""
    visualizer = ResultVisualizer(figsize=(10, 6))
    
    # PDR comparison
    fig1 = visualizer.plot_pdr_comparison(
        [type('obj', (object,), r) for r in results_a],
        [type('obj', (object,), r) for r in results_b],
        label_a=label_a,
        label_b=label_b,
        show=False
    )
    st.pyplot(fig1)
    plt.close(fig1)
    
    # Lifetime comparison
    fig2 = visualizer.plot_lifetime_comparison(
        [type('obj', (object,), r) for r in results_a],
        [type('obj', (object,), r) for r in results_b],
        label_a=label_a,
        label_b=label_b,
        show=False
    )
    st.pyplot(fig2)
    plt.close(fig2)


def main():
    load_css()
    
    # Header
    st.markdown('<div class="main-header">📡 Energy-Aware Routing Protocol Simulator</div>', unsafe_allow_html=True)
    st.markdown("Compare **Shortest-Path** vs **Energy-Aware** routing in Wireless Sensor Networks")
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
        
        # Config file upload
        config_file = st.file_uploader(
            "Upload Config YAML (optional)",
            type=['yaml', 'yml'],
            help="Upload a custom configuration file"
        )
        
        # Or use built-in configs
        config_option = st.selectbox(
            "Or select built-in config:",
            ["base.yaml (50 nodes)", "small.yaml (20 nodes)", "large.yaml (100 nodes)", "test_quick.yaml (10 nodes, 50 rounds)"]
        )
        
        config_map = {
            "base.yaml (50 nodes)": "configs/base.yaml",
            "small.yaml (20 nodes)": "configs/small.yaml",
            "large.yaml (100 nodes)": "configs/large.yaml",
            "test_quick.yaml (10 nodes, 50 rounds)": "configs/test_quick.yaml"
        }
        
        # Routing algorithm selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 Routing Algorithm")
        
        algorithm = st.radio(
            "Select algorithm:",
            ["shortest_path", "energy_aware"],
            format_func=lambda x: "Shortest Path (Dijkstra)" if x == "shortest_path" else "Energy-Aware (α·dist + β·energy)"
        )
        
        if algorithm == "energy_aware":
            alpha = st.slider("α (Distance Weight)", 0.0, 1.0, 0.5, 0.05)
            beta = 1.0 - alpha
            st.info(f"β (Energy Weight) = {beta:.2f}")
        else:
            alpha = 0.5
            beta = 0.5
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Network parameters
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🌐 Network Parameters")
        
        if config_file:
            settings = load_config(config_file)
        else:
            settings = load_config(config_map[config_option])
        
        # Allow overriding key parameters
        num_nodes = st.number_input("Number of Sensor Nodes", 5, 500, settings.network.num_nodes)
        area_width = st.number_input("Area Width (m)", 10.0, 1000.0, settings.network.area_width)
        area_height = st.number_input("Area Height (m)", 10.0, 1000.0, settings.network.area_height)
        comm_range = st.number_input("Communication Range (m)", 5.0, 200.0, settings.network.communication_range)
        initial_energy = st.number_input("Initial Energy (J)", 0.01, 100.0, settings.energy.initial_energy)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Simulation parameters
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🔄 Simulation Parameters")
        
        num_rounds = st.number_input("Number of Rounds", 10, 10000, settings.simulation.num_rounds)
        packets_per_round = st.number_input("Packets per Round per Node", 1, 10, settings.simulation.packets_per_round)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Experiment options
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🧪 Experiments")
        
        run_experiment = st.checkbox("Run Routing Comparison Experiment (5 seeds)", value=False)
        if run_experiment:
            exp_seeds = st.number_input("Number of Seeds", 1, 20, 5)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["🏃 Run Simulation", "📊 Results", "🔬 Experiments", "📈 Network Topology"])
    
    with tab1:
        st.markdown('<div class="section-header">Single Simulation Run</div>', unsafe_allow_html=True)
        
        # Build settings from UI
        if config_file:
            settings = load_config(config_file)
        else:
            settings = load_config(config_map[config_option])
        
        # Override with UI values
        settings.network.num_nodes = num_nodes
        settings.network.area_width = area_width
        settings.network.area_height = area_height
        settings.network.communication_range = comm_range
        settings.energy.initial_energy = initial_energy
        settings.simulation.num_rounds = num_rounds
        settings.simulation.packets_per_round = packets_per_round
        settings.routing.algorithm = algorithm
        settings.routing.alpha = alpha
        settings.routing.beta = beta
        
        # Display current config
        with st.expander("Current Configuration"):
            st.json({
                "network": {k: v for k, v in settings.network.__dict__.items()},
                "energy": {k: v for k, v in settings.energy.__dict__.items()},
                "simulation": {k: v for k, v in settings.simulation.__dict__.items()},
                "routing": {k: v for k, v in settings.routing.__dict__.items()}
            })
        
        # Run button
        if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
            with st.spinner("Running simulation..."):
                try:
                    result = run_single_simulation(settings)
                    st.session_state['last_result'] = result
                    st.session_state['last_settings'] = settings
                    st.success("Simulation completed successfully!")
                except Exception as e:
                    st.error(f"Simulation failed: {e}")
        
        # Display results if available
        if 'last_result' in st.session_state:
            st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)
            display_simulation_results(st.session_state['last_result'])
            
            # Download button
            st.download_button(
                label="📥 Download Results (JSON)",
                data=json.dumps(st.session_state['last_result'], indent=2),
                file_name=f"simulation_result_{st.session_state['last_settings'].network.seed}.json",
                mime="application/json"
            )
    
    with tab2:
        st.markdown('<div class="section-header">Results Visualization</div>', unsafe_allow_html=True)
        
        if 'last_result' in st.session_state and 'last_settings' in st.session_state:
            result = st.session_state['last_result']
            settings = st.session_state['last_settings']
            
            # Recreate topology for plotting
            topology = generate_topology(settings.network, settings.energy)
            graph = build_graph(topology, settings.network.communication_range)
            
            visualizer = ResultVisualizer()
            
            # Plot alive nodes over time
            st.subheader("Alive Nodes Over Time")
            fig = visualizer.plot_alive_nodes_over_time(
                [type('obj', (object,), result)],
                show=False
            )
            st.pyplot(fig)
            plt.close(fig)
            
            # Plot energy over time
            st.subheader("Total Remaining Energy Over Time")
            fig = visualizer.plot_energy_over_time(
                [type('obj', (object,), result)],
                show=False
            )
            st.pyplot(fig)
            plt.close(fig)
            
            # Plot packets
            st.subheader("Packets Per Round")
            fig = visualizer.plot_packets_over_time(
                [type('obj', (object,), result)],
                show=False
            )
            st.pyplot(fig)
            plt.close(fig)
            
            # Hop count
            if result.get('avg_hop_count'):
                st.subheader("Average Hop Count")
                fig = visualizer.plot_hop_count_distribution(
                    [type('obj', (object,), result)],
                    show=False
                )
                st.pyplot(fig)
                plt.close(fig)
        else:
            st.info("Run a simulation first to see visualizations.")
    
    with tab3:
        st.markdown('<div class="section-header">Routing Comparison Experiment</div>', unsafe_allow_html=True)
        
        st.markdown("""
        This experiment runs both routing algorithms with the **same seeds** (same topologies)
        for fair comparison. Uses 5 seeds by default.
        """)
        
        if 'last_settings' in st.session_state:
            base_settings = st.session_state['last_settings']
        else:
            if config_file:
                base_settings = load_config(config_file)
            else:
                base_settings = load_config(config_map[config_option])
            
            base_settings.network.num_nodes = num_nodes
            base_settings.network.area_width = area_width
            base_settings.network.area_height = area_height
            base_settings.network.communication_range = comm_range
            base_settings.energy.initial_energy = initial_energy
            base_settings.simulation.num_rounds = num_rounds
            base_settings.simulation.packets_per_round = packets_per_round
        
        if st.button("🔬 Run Comparison Experiment", type="primary", use_container_width=True):
            with st.spinner("Running comparison experiment (this may take a while)..."):
                try:
                    if run_experiment:
                        num_seeds = exp_seeds
                    else:
                        num_seeds = 5
                    
                    results = run_comparison_experiment(base_settings, num_seeds)
                    st.session_state['comparison_results'] = results
                    st.success(f"Comparison completed with {num_seeds} seeds!")
                except Exception as e:
                    st.error(f"Experiment failed: {e}")
        
        if 'comparison_results' in st.session_state:
            results = st.session_state['comparison_results']
            
            st.subheader("Comparison Results")
            
            # Summary metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Shortest Path")
                sp_results = results.get('shortest_path', [])
                if sp_results:
                    fnds = [r.get('fnd') for r in sp_results if r.get('fnd') is not None]
                    pdrs = [r.get('packet_delivery_ratio', 0) for r in sp_results]
                    st.metric("Mean FND", f"{np.mean(fnds):.1f}" if fnds else "N/A")
                    st.metric("Mean PDR", f"{np.mean(pdrs):.4f}")
                    st.metric("Seeds Run", len(sp_results))
            
            with col2:
                st.markdown("#### Energy-Aware (α=0.5, β=0.5)")
                ea_results = results.get('energy_aware', [])
                if ea_results:
                    fnds = [r.get('fnd') for r in ea_results if r.get('fnd') is not None]
                    pdrs = [r.get('packet_delivery_ratio', 0) for r in ea_results]
                    st.metric("Mean FND", f"{np.mean(fnds):.1f}" if fnds else "N/A")
                    st.metric("Mean PDR", f"{np.mean(pdrs):.4f}")
                    st.metric("Seeds Run", len(ea_results))
            
            # Comparison plots
            if sp_results and ea_results:
                st.subheader("Comparison Plots")
                plot_comparison_results(sp_results, ea_results, "Shortest Path", "Energy-Aware")
            
            # Download button
            st.download_button(
                label="📥 Download Comparison Results (JSON)",
                data=json.dumps(results, indent=2),
                file_name=f"comparison_results_{base_settings.network.seed}.json",
                mime="application/json"
            )
        else:
            st.info("Configure settings in the sidebar first.")
    
    with tab4:
        st.markdown('<div class="section-header">Network Topology Visualization</div>', unsafe_allow_html=True)
        
        if 'last_settings' in st.session_state:
            settings = st.session_state['last_settings']
        else:
            if config_file:
                settings = load_config(config_file)
            else:
                settings = load_config(config_map[config_option])
            
            settings.network.num_nodes = num_nodes
            settings.network.area_width = area_width
            settings.network.area_height = area_height
            settings.network.communication_range = comm_range
            settings.energy.initial_energy = initial_energy
        
        # Generate topology
        topology = generate_topology(settings.network, settings.energy)
        graph = build_graph(topology, settings.network.communication_range)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Network Topology")
            fig = plot_network_topology(topology, graph, show=False)
            st.pyplot(fig)
            plt.close(fig)
        
        with col2:
            st.subheader("Energy Heatmap")
            fig = plot_energy_heatmap(topology, graph, show=False)
            st.pyplot(fig)
            plt.close(fig)
        
        # Network statistics
        st.subheader("Network Statistics")
        alive_sensors = sum(1 for nid, node in topology.nodes.items() 
                          if nid != topology.base_station_id and node.is_alive)
        dead_sensors = sum(1 for nid, node in topology.nodes.items() 
                         if nid != topology.base_station_id and not node.is_alive)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sensor Nodes", settings.network.num_nodes)
        with col2:
            st.metric("Alive Nodes", alive_sensors)
        with col3:
            st.metric("Dead Nodes", dead_sensors)
        with col4:
            st.metric("Edges in Graph", graph.number_of_edges())
        
        # Show path if simulation was run
        if 'last_result' in st.session_state and st.session_state['last_result'].get('round_metrics'):
            st.subheader("Sample Packet Paths")
            # Show first few delivered packet paths
            result = st.session_state['last_result']
            # We'd need to store delivered packets to show paths
            st.info("Run a simulation to see sample packet paths.")


if __name__ == "__main__":
    main()