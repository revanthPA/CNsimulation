#!/usr/bin/env python3
"""
Streamlit GUI for Energy-Aware Routing Protocol Simulation.

Provides a professional, clean, and scientifically faithful interface for:
  - Section A: Configuring and running a single WSN simulation
  - Section B: Running paired comparisons between Shortest-Path and Energy-Aware routing
  - Section C: Browsing and inspecting previous simulation and comparison results

Launch with:
    streamlit run src/energy_routing/dashboard.py
or:
    python -m streamlit run src/energy_routing/dashboard.py
"""

import copy
import io
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from energy_routing.config import (
    EnergyConfig,
    NetworkConfig,
    OutputConfig,
    RoutingConfig,
    SimulationParameters,
    SimulationSettings,
    load_config,
)
from energy_routing.experiments import ExperimentRunner
from energy_routing.experiments.runner import Experiment
from energy_routing.simulation import create_simulator


# ---------------------------------------------------------------------------
# Core Helper & Execution Functions (reused by UI and tested by test suite)
# ---------------------------------------------------------------------------

def validate_simulation_parameters(
    num_nodes: int,
    comm_range: float,
    initial_energy: float,
    num_rounds: int,
    seed: int,
    algorithm: str,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> List[str]:
    """
    Validate user inputs against domain constraints.

    Returns:
        List of human-readable error messages (empty if valid).
    """
    errors: List[str] = []
    if num_nodes < 2:
        errors.append("Number of sensor nodes must be at least 2.")
    if comm_range <= 0:
        errors.append("Communication range must be greater than 0 meters.")
    if initial_energy <= 0:
        errors.append("Initial energy must be greater than 0 Joules.")
    if num_rounds < 1:
        errors.append("Number of rounds must be at least 1.")
    if seed < 0:
        errors.append("Random seed must be non-negative.")
    if algorithm not in ("shortest_path", "energy_aware"):
        errors.append(f"Unsupported routing algorithm: {algorithm}")
    if algorithm == "energy_aware":
        if alpha < 0 or alpha > 1:
            errors.append("Alpha (distance weight) must be in [0.0, 1.0].")
        if beta < 0 or beta > 1:
            errors.append("Beta (energy weight) must be in [0.0, 1.0].")
        if not math.isclose(alpha + beta, 1.0, abs_tol=1e-6):
            errors.append(f"Alpha ({alpha:.2f}) and Beta ({beta:.2f}) must sum to 1.0.")
    return errors


def format_lifetime_metric(value: Optional[int], max_rounds: Optional[int] = None) -> str:
    """Format FND/HND/LND lifetime metrics with scientific accuracy."""
    if value is None:
        if max_rounds is not None:
            return f"Not observed (>{max_rounds} rounds)"
        return "Not observed"
    return f"Round {value}"


def run_single_simulation(
    settings: SimulationSettings,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a single simulation run via the existing backend engine.

    Optionally saves the result JSON to a unique file in output_dir.
    """
    simulator = create_simulator(settings)
    result = simulator.run()
    result_dict = result.to_dict()

    # Automatically save to a non-colliding location if requested or default
    target_dir = Path(output_dir or "results/dashboard/single_runs")
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    algo = settings.routing.algorithm
    seed = settings.network.seed
    result_path = target_dir / f"sim_{algo}_seed{seed}_{timestamp}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)
    result_dict["_saved_filepath"] = str(result_path)

    return result_dict


def run_comparison_experiment(
    base_settings: SimulationSettings,
    num_seeds: int = 5,
    output_dir: Optional[str] = None,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Execute a paired comparison experiment across multiple seeds.

    Ensures both algorithms run on identical topology and traffic for each seed.
    """
    exp = Experiment(
        name="routing_comparison",
        description="Paired comparison: Shortest-Path vs Energy-Aware",
        base_settings=base_settings,
        num_seeds=num_seeds,
        fixed_parameters={
            "routing.alpha": alpha,
            "routing.beta": beta,
        },
    )

    save_dir = output_dir or "results/dashboard/comparisons"
    runner = ExperimentRunner(output_dir=save_dir)
    results = runner.run_comparison(
        exp,
        algorithm_a="shortest_path",
        algorithm_b="energy_aware",
        alpha=alpha,
        beta=beta,
    )

    return {
        algo: [r.to_dict() for r in res_list]
        for algo, res_list in results.items()
    }


def plot_to_streamlit(fig: plt.Figure) -> io.BytesIO:
    """Convert a Matplotlib figure into a PNG BytesIO buffer for Streamlit."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def display_simulation_results(result: Dict[str, Any]):
    """Display key simulation metrics in clean, readable cards."""
    max_rounds = result.get("config", {}).get("simulation", {}).get("num_rounds")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fnd_str = format_lifetime_metric(result.get("fnd"), max_rounds)
        st.metric("First Node Death (FND)", fnd_str, help="First round where >= 1 sensor depleted its energy.")
    with c2:
        pdr = result.get("packet_delivery_ratio", 0.0)
        st.metric("Packet Delivery Ratio (PDR)", f"{pdr:.4f} ({pdr*100:.1f}%)", help="Delivered packets / Generated packets.")
    with c3:
        delivered = result.get("total_packets_delivered", 0)
        lost = result.get("total_packets_lost", 0)
        st.metric("Packets (Delivered / Lost)", f"{delivered} / {lost}", help="Total packets delivered vs lost during routing.")
    with c4:
        alive = result.get("final_alive_nodes", 0)
        dead = result.get("final_dead_nodes", 0)
        st.metric("Sensors (Alive / Dead)", f"{alive} / {dead}", help="Number of operational vs depleted sensors at finish.")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        hnd_str = format_lifetime_metric(result.get("hnd"), max_rounds)
        st.metric("Half Node Death (HND)", hnd_str, help="First round where <= half sensor nodes remain alive.")
    with c6:
        lnd_str = format_lifetime_metric(result.get("lnd"), max_rounds)
        st.metric("Last Node Death (LND)", lnd_str, help="First round where all sensor nodes are dead.")
    with c7:
        rem_e = result.get("final_total_remaining_energy", 0.0)
        st.metric("Remaining Energy", f"{rem_e:.4f} J", help="Total residual energy across all operational sensor nodes.")
    with c8:
        cons_e = result.get("final_total_energy_consumed", 0.0)
        st.metric("Consumed Energy", f"{cons_e:.4f} J", help="Total energy dissipated in radio transmissions and receptions.")


def plot_simulation_metrics(result: Dict[str, Any]) -> Optional[plt.Figure]:
    """Plot alive nodes and remaining energy over simulation rounds with academic styling."""
    round_metrics = result.get("round_metrics", [])
    if not round_metrics:
        return None

    rounds = [m.get("round", i) for i, m in enumerate(round_metrics)]
    alive_nodes = [m.get("alive_nodes", 0) for m in round_metrics]
    rem_energy = [m.get("total_remaining_energy", 0.0) for m in round_metrics]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), dpi=150)
    fig.patch.set_facecolor('#ffffff')

    # Subplot 1: Operational Sensors Curve
    ax1.set_facecolor('#ffffff')
    ax1.plot(rounds, alive_nodes, color="#1e40af", linewidth=2.2, label="Operational Sensors")
    ax1.set_title("Operational Sensor Nodes Over Rounds", fontsize=12, fontweight="600", color="#0f172a", pad=12)
    ax1.set_xlabel("Simulation Round", fontsize=10.5, color="#334155")
    ax1.set_ylabel("Operational Nodes", fontsize=10.5, color="#334155")
    ax1.tick_params(colors="#475569", labelsize=10)
    ax1.grid(True, linestyle="--", linewidth=0.7, color="#e2e8f0", alpha=0.9)
    ax1.set_ylim(bottom=0)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#cbd5e1')
    ax1.spines['bottom'].set_color('#cbd5e1')

    # Mark FND if observed
    fnd = result.get("fnd")
    if fnd is not None and fnd < len(rounds):
        ax1.axvline(fnd, color="#dc2626", linestyle=":", linewidth=1.8, label=f"FND (Round {fnd})")
    ax1.legend(loc="best", fontsize=9.5, framealpha=0.95, edgecolor="#e2e8f0")

    # Subplot 2: Residual Network Energy Curve
    ax2.set_facecolor('#ffffff')
    ax2.plot(rounds, rem_energy, color="#0f766e", linewidth=2.2, label="Residual Energy (J)")
    ax2.set_title("Network Residual Energy Over Rounds", fontsize=12, fontweight="600", color="#0f172a", pad=12)
    ax2.set_xlabel("Simulation Round", fontsize=10.5, color="#334155")
    ax2.set_ylabel("Remaining Energy (Joules)", fontsize=10.5, color="#334155")
    ax2.tick_params(colors="#475569", labelsize=10)
    ax2.grid(True, linestyle="--", linewidth=0.7, color="#e2e8f0", alpha=0.9)
    ax2.set_ylim(bottom=0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#cbd5e1')
    ax2.spines['bottom'].set_color('#cbd5e1')
    ax2.legend(loc="best", fontsize=9.5, framealpha=0.95, edgecolor="#e2e8f0")

    plt.tight_layout()
    return fig


def plot_comparison_results(
    results_a: List[Dict[str, Any]],
    results_b: List[Dict[str, Any]],
    label_a: str = "Shortest Path",
    label_b: str = "Energy-Aware",
) -> Optional[plt.Figure]:
    """Create a paired comparison plot of FND and PDR across seeds with academic styling."""
    if not results_a or not results_b:
        return None

    n = min(len(results_a), len(results_b))
    seeds = [r.get("config", {}).get("network", {}).get("seed", i + 1) for i, r in enumerate(results_a[:n])]

    fnd_a = [r.get("fnd") if r.get("fnd") is not None else 0 for r in results_a[:n]]
    fnd_b = [r.get("fnd") if r.get("fnd") is not None else 0 for r in results_b[:n]]
    pdr_a = [r.get("packet_delivery_ratio", 0.0) for r in results_a[:n]]
    pdr_b = [r.get("packet_delivery_ratio", 0.0) for r in results_b[:n]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), dpi=150)
    fig.patch.set_facecolor('#ffffff')

    x = np.arange(n)
    width = 0.35

    # Subplot 1: FND Comparison Bar Chart
    ax1.set_facecolor('#ffffff')
    ax1.bar(x - width/2, fnd_a, width, label=label_a, color="#475569", alpha=0.92, edgecolor="none")
    ax1.bar(x + width/2, fnd_b, width, label=label_b, color="#0284c7", alpha=0.92, edgecolor="none")
    ax1.set_title("First Node Death (FND) by Seed", fontsize=12, fontweight="600", color="#0f172a", pad=12)
    ax1.set_xlabel("Simulation Seed", fontsize=10.5, color="#334155")
    ax1.set_ylabel("FND Round (Higher is Better)", fontsize=10.5, color="#334155")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"S-{s}" for s in seeds], rotation=0, fontsize=9.5)
    ax1.tick_params(colors="#475569", labelsize=10)
    ax1.grid(True, linestyle="--", linewidth=0.7, color="#e2e8f0", alpha=0.9, axis="y")
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#cbd5e1')
    ax1.spines['bottom'].set_color('#cbd5e1')
    ax1.legend(loc="best", fontsize=9.5, framealpha=0.95, edgecolor="#e2e8f0")

    # Subplot 2: PDR Comparison Bar Chart
    ax2.set_facecolor('#ffffff')
    ax2.bar(x - width/2, pdr_a, width, label=label_a, color="#475569", alpha=0.92, edgecolor="none")
    ax2.bar(x + width/2, pdr_b, width, label=label_b, color="#0284c7", alpha=0.92, edgecolor="none")
    ax2.set_title("Packet Delivery Ratio (PDR) by Seed", fontsize=12, fontweight="600", color="#0f172a", pad=12)
    ax2.set_xlabel("Simulation Seed", fontsize=10.5, color="#334155")
    ax2.set_ylabel("PDR (0.0 to 1.0)", fontsize=10.5, color="#334155")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"S-{s}" for s in seeds], rotation=0, fontsize=9.5)
    ax2.set_ylim([0.0, 1.05])
    ax2.tick_params(colors="#475569", labelsize=10)
    ax2.grid(True, linestyle="--", linewidth=0.7, color="#e2e8f0", alpha=0.9, axis="y")
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#cbd5e1')
    ax2.spines['bottom'].set_color('#cbd5e1')
    ax2.legend(loc="best", fontsize=9.5, framealpha=0.95, edgecolor="#e2e8f0")

    plt.tight_layout()
    return fig


def find_saved_result_files(base_dir: str = "results") -> List[Path]:
    """Recursively discover all valid JSON result files in the results directory."""
    root = Path(base_dir)
    if not root.exists():
        return []

    json_files = []
    for p in root.rglob("*.json"):
        if p.is_file() and p.stat().st_size > 0:
            json_files.append(p)

    # Sort newest files first
    json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return json_files


def load_result_file(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Safely load and parse a JSON result file."""
    try:
        if not file_path.exists():
            return None, f"File not found: {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON format in {file_path.name}: {e}"
    except Exception as e:
        return None, f"Failed to read {file_path.name}: {e}"


# ---------------------------------------------------------------------------
# Streamlit Application Layout
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Energy-Aware Routing Protocol Simulator",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Custom Clean & Professional Scientific CSS with Scaled Typography
    st.markdown("""
    <style>
    /* Global Base Scale */
    html, body, [class*="css"] {
        font-size: 17.5px !important;
    }
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Constrain ultra-wide stretch on 4K/high-res screens for optimal reading layout */
    .block-container {
        max-width: 1900px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    /* Header Area */
    .app-header {
        padding: 1.5rem 0 1.25rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .app-title {
        font-size: 2.65rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 0.45rem;
    }
    .app-subtitle {
        font-size: 1.15rem;
        color: #475569;
        line-height: 1.6;
        max-width: 1100px;
    }

    /* Section Headers */
    .section-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.5rem;
        margin-bottom: 0.35rem;
    }
    .section-desc {
        font-size: 1.05rem;
        color: #64748b;
        line-height: 1.55;
        margin-bottom: 1.35rem;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.75rem;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        padding: 0.75rem 1.25rem !important;
        background-color: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        border-bottom: 3px solid #0284c7 !important;
    }

    /* Form & Container Polish */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.75rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
    }

    /* Input Labels and Widgets */
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] div,
    div[data-testid="stWidgetLabel"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 0.35rem !important;
    }
    div[data-baseweb="input"] input {
        font-size: 1.1rem !important;
        min-height: 44px !important;
        padding: 0.5rem 0.75rem !important;
    }
    div[data-baseweb="select"] div {
        font-size: 1.1rem !important;
        min-height: 44px !important;
    }

    /* Action Buttons */
    button[kind="primary"],
    button[kind="secondary"],
    .stButton button,
    div[data-testid="stDownloadButton"] button {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        min-height: 48px !important;
        padding: 0.65rem 1.75rem !important;
        border-radius: 8px !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1.15rem 1.25rem !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03) !important;
    }
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] div {
        color: #64748b !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #0f172a !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        margin-top: 0.2rem !important;
    }

    /* Table Typography */
    .stTable table,
    div[data-testid="stTable"] table {
        font-size: 1.05rem !important;
    }
    .stTable th,
    div[data-testid="stTable"] th {
        font-size: 1.08rem !important;
        padding: 0.85rem 1rem !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    .stTable td,
    div[data-testid="stTable"] td {
        font-size: 1.02rem !important;
        padding: 0.85rem 1rem !important;
        color: #1e293b !important;
    }
    div[data-testid="stDataFrame"] {
        font-size: 1.02rem !important;
    }

    /* Summary Outcome Banner */
    .outcome-box {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 1.15rem 1.4rem;
        border-radius: 8px;
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 1.25rem 0;
    }

    /* Formula Note */
    .formula-note {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.95rem;
        color: #334155;
        background-color: #f1f5f9;
        padding: 0.55rem 0.95rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        display: inline-block;
        margin-bottom: 0.85rem;
    }

    /* Expander header font */
    div[data-testid="stExpander"] details summary p {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #0f172a !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Professional Academic Header Banner
    st.markdown("""
    <div class="app-header">
        <div class="app-title">Energy-Aware Routing Protocol Simulator</div>
        <div class="app-subtitle">
            A scientific simulation environment for Wireless Sensor Networks (WSNs).
            Evaluates whether incorporating residual sensor energy into routing decisions increases network lifetime
            compared to conventional shortest-path routing under identical topologies and traffic loads.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Default settings baseline
    try:
        default_settings = load_config("configs/base.yaml")
    except Exception:
        default_settings = SimulationSettings(
            network=NetworkConfig(num_nodes=50, area_width=100.0, area_height=100.0, communication_range=20.0, seed=42, base_station_x=50.0, base_station_y=50.0),
            energy=EnergyConfig(initial_energy=1.0, E_elec=50.0, E_amp=0.0013, packet_size=512),
            simulation=SimulationParameters(num_rounds=1000, packets_per_round=1, packet_size=512),
            routing=RoutingConfig(algorithm="shortest_path", alpha=0.5, beta=0.5),
            output=OutputConfig(results_dir="results", save_results=True),
        )

    # First-run orientation: keep the existing simulation workflow visible after a short overview.
    with st.container(border=True):
        intro_left, intro_right = st.columns([1.35, 1])
        with intro_left:
            st.markdown("### Start with a controlled run")
            st.caption("Configure one network, run either routing strategy, then compare both strategies on matching seeds and inspect saved results.")
            step1, step2, step3 = st.columns(3)
            with step1:
                st.markdown("**1 · Configure**")
                st.caption("Set network size, range, energy, rounds, and seed.")
            with step2:
                st.markdown("**2 · Run or compare**")
                st.caption("A comparison pairs both algorithms on the same topology for each seed.")
            with step3:
                st.markdown("**3 · Review**")
                st.caption("Read lifetime and delivery metrics, then browse saved JSON results.")
        with intro_right:
            st.markdown("### Reading the results")
            st.caption("**FND / HND / LND** mark first, half, and last sensor death. **PDR** is the fraction of generated packets delivered. A lifetime marked ‘Not observed’ means the configured round limit ended first.")
            st.caption("New dashboard runs are stored under `results/dashboard/`. Use the Results tab to inspect earlier files.")
    # Three Clean Sections (Tabs without emojis)
    tab_sim, tab_comp, tab_results = st.tabs([
        "Run a Simulation",
        "Compare Algorithms",
        "Saved Results",
    ])

    # -----------------------------------------------------------------------
    # SECTION A: RUN SIMULATION
    # -----------------------------------------------------------------------
    with tab_sim:
        st.markdown('<div class="section-title">Configure and Run Simulation</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">Specify network topology parameters, energy budgets, and routing behavior for a single simulation run.</div>', unsafe_allow_html=True)

        with st.form("simulation_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                num_nodes = st.number_input(
                    "Number of Sensor Nodes",
                    min_value=5,
                    max_value=300,
                    value=int(default_settings.network.num_nodes),
                    step=5,
                    help="Total sensor nodes randomly placed across the network area.",
                )
                comm_range = st.number_input(
                    "Communication Range (m)",
                    min_value=5.0,
                    max_value=150.0,
                    value=float(default_settings.network.communication_range),
                    step=5.0,
                    help="Maximum transmission radius for direct single-hop links.",
                )
            with col2:
                initial_energy = st.number_input(
                    "Initial Sensor Energy (J)",
                    min_value=0.05,
                    max_value=50.0,
                    value=float(default_settings.energy.initial_energy),
                    step=0.25,
                    help="Starting energy budget per sensor node in Joules (Base station has infinite energy).",
                )
                num_rounds = st.number_input(
                    "Simulation Rounds",
                    min_value=10,
                    max_value=5000,
                    value=int(default_settings.simulation.num_rounds),
                    step=50,
                    help="Maximum number of rounds to execute (stops early if all sensors deplete).",
                )
            with col3:
                seed = st.number_input(
                    "Random Seed",
                    min_value=0,
                    max_value=999999,
                    value=int(default_settings.network.seed),
                    step=1,
                    help="Ensures exact deterministic reproduction of network topology and traffic.",
                )
                algorithm_label = st.selectbox(
                    "Routing Algorithm",
                    ["Shortest Path (Dijkstra)", "Energy-Aware (Residual Energy)"],
                    index=0,
                    help="Shortest Path minimizes distance. Energy-Aware balances distance and remaining node energy.",
                )

            algo_code = "energy_aware" if "Energy-Aware" in algorithm_label else "shortest_path"

            if algo_code == "energy_aware":
                st.markdown('<div class="formula-note">Cost Formula: cost(u, v) = alpha * (dist / max_dist) + beta * (1 - E_res / E_init)</div>', unsafe_allow_html=True)
                w_col1, w_col2 = st.columns(2)
                with w_col1:
                    alpha = st.slider("Distance Weight (alpha)", 0.0, 1.0, 0.5, 0.05, help="Weight given to transmission distance.")
                with w_col2:
                    beta = round(1.0 - alpha, 4)
                    st.slider("Energy Weight (beta = 1 - alpha)", 0.0, 1.0, beta, disabled=True, help="Automatically complementary so alpha + beta = 1.0.")
            else:
                alpha, beta = 0.5, 0.5

            submit_sim = st.form_submit_button("Run Simulation", type="primary", use_container_width=True)

        if submit_sim:
            validation_errors = validate_simulation_parameters(
                num_nodes, comm_range, initial_energy, num_rounds, seed, algo_code, alpha, beta
            )
            if validation_errors:
                for err in validation_errors:
                    st.error(f"Validation Error: {err}")
            else:
                sim_settings = copy.deepcopy(default_settings)
                sim_settings.network.num_nodes = num_nodes
                sim_settings.network.communication_range = comm_range
                sim_settings.energy.initial_energy = initial_energy
                sim_settings.simulation.num_rounds = num_rounds
                sim_settings.network.seed = seed
                sim_settings.routing.algorithm = algo_code
                sim_settings.routing.alpha = alpha
                sim_settings.routing.beta = beta

                with st.spinner(f"Executing simulation ({num_nodes} nodes, up to {num_rounds} rounds, algorithm: {algorithm_label})..."):
                    try:
                        result = run_single_simulation(sim_settings)
                        st.session_state["single_sim_result"] = result
                        saved_path = result.get("_saved_filepath", "results/dashboard/")
                        st.success(f"Simulation completed successfully. Output saved to: {saved_path}")
                    except Exception as e:
                        st.error(f"Simulation execution failed: {e}")

        # Display Single Simulation Results
        if "single_sim_result" in st.session_state:
            res = st.session_state["single_sim_result"]
            st.divider()
            st.markdown('<div class="section-title">Simulation Results Summary</div>', unsafe_allow_html=True)
            display_simulation_results(res)

            fig = plot_simulation_metrics(res)
            if fig:
                st.markdown('<div class="section-desc" style="margin-top: 1rem;">Time-series degradation curves for operational sensors and total network residual energy:</div>', unsafe_allow_html=True)
                st.pyplot(fig)
                plt.close(fig)

            # JSON download
            res_clean = {k: v for k, v in res.items() if not k.startswith("_")}
            st.download_button(
                label="Download Result Data (JSON)",
                data=json.dumps(res_clean, indent=2),
                file_name=f"sim_result_{res.get('config', {}).get('network', {}).get('seed', 'run')}.json",
                mime="application/json",
            )

    # -----------------------------------------------------------------------
    # SECTION B: COMPARE ALGORITHMS
    # -----------------------------------------------------------------------
    with tab_comp:
        st.markdown('<div class="section-title">Paired Algorithm Comparison</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">'
            'Execute a paired, controlled experiment comparing Shortest-Path vs Energy-Aware routing. '
            'Both algorithms execute on identical random topologies and packet traffic loads for every seed.'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.form("comparison_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                comp_num_seeds = st.slider(
                    "Number of Paired Seeds",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Number of independent random topologies to evaluate.",
                )
                comp_start_seed = st.number_input(
                    "Starting Seed",
                    min_value=0,
                    max_value=999999,
                    value=42,
                    step=1,
                    help="Initial seed; subsequent runs increment sequentially from this value.",
                )
            with c2:
                comp_nodes = st.number_input("Nodes per Network", 5, 200, 50, step=5)
                comp_range = st.number_input("Communication Range (m)", 5.0, 100.0, 20.0, step=5.0)
            with c3:
                comp_energy = st.number_input("Initial Energy (J)", 0.1, 10.0, 1.0, step=0.1)
                comp_rounds = st.number_input("Simulation Rounds", 50, 2000, 1000, step=50)

            comp_alpha = st.slider("Energy-Aware Distance Weight (alpha)", 0.0, 1.0, 0.5, 0.05)
            comp_beta = round(1.0 - comp_alpha, 4)

            submit_comp = st.form_submit_button("Compare Algorithms", type="primary", use_container_width=True)

        if submit_comp:
            comp_settings = copy.deepcopy(default_settings)
            comp_settings.network.num_nodes = comp_nodes
            comp_settings.network.communication_range = comp_range
            comp_settings.energy.initial_energy = comp_energy
            comp_settings.simulation.num_rounds = comp_rounds
            comp_settings.network.seed = comp_start_seed

            with st.spinner(f"Executing paired comparison across {comp_num_seeds} seeds (2 x {comp_num_seeds} simulations)..."):
                try:
                    comp_results = run_comparison_experiment(
                        base_settings=comp_settings,
                        num_seeds=comp_num_seeds,
                        alpha=comp_alpha,
                        beta=comp_beta,
                    )
                    st.session_state["comparison_results"] = comp_results
                    st.success(f"Comparison completed successfully across {comp_num_seeds} paired seeds.")
                except Exception as e:
                    st.error(f"Experiment execution failed: {e}")

        # Display Comparison Table and Chart
        if "comparison_results" in st.session_state:
            comp_data = st.session_state["comparison_results"]
            sp_runs = comp_data.get("shortest_path", [])
            ea_runs = comp_data.get("energy_aware", [])

            if sp_runs and ea_runs:
                st.divider()
                st.markdown('<div class="section-title">Comparative Analysis Results</div>', unsafe_allow_html=True)

                # Extract paired metrics
                n_seeds = min(len(sp_runs), len(ea_runs))
                paired_rows = []
                ea_improvements = 0
                ea_ties = 0
                sp_better = 0

                sp_fnds = []
                ea_fnds = []
                sp_pdrs = [r.get("packet_delivery_ratio", 0.0) for r in sp_runs[:n_seeds]]
                ea_pdrs = [r.get("packet_delivery_ratio", 0.0) for r in ea_runs[:n_seeds]]
                sp_energies = [r.get("final_total_energy_consumed", 0.0) for r in sp_runs[:n_seeds]]
                ea_energies = [r.get("final_total_energy_consumed", 0.0) for r in ea_runs[:n_seeds]]

                for i in range(n_seeds):
                    r_sp = sp_runs[i]
                    r_ea = ea_runs[i]
                    seed_val = r_sp.get("config", {}).get("network", {}).get("seed", i + 1)
                    fnd_sp = r_sp.get("fnd")
                    fnd_ea = r_ea.get("fnd")

                    if fnd_sp is not None:
                        sp_fnds.append(fnd_sp)
                    if fnd_ea is not None:
                        ea_fnds.append(fnd_ea)

                    # Determine winner with professional text
                    if fnd_ea is not None and fnd_sp is not None:
                        diff = fnd_ea - fnd_sp
                        if diff > 0:
                            outcome = f"Energy-Aware (+{diff} rounds)"
                            ea_improvements += 1
                        elif diff == 0:
                            outcome = "Tie"
                            ea_ties += 1
                        else:
                            outcome = f"Shortest-Path (+{abs(diff)} rounds)"
                            sp_better += 1
                    elif fnd_ea is not None and fnd_sp is None:
                        diff = "N/A"
                        outcome = "Shortest-Path (survived longer)"
                        sp_better += 1
                    elif fnd_ea is None and fnd_sp is not None:
                        diff = "N/A"
                        outcome = "Energy-Aware (survived longer)"
                        ea_improvements += 1
                    else:
                        diff = 0
                        outcome = "Tie (Neither reached FND)"
                        ea_ties += 1

                    paired_rows.append({
                        "Seed": seed_val,
                        "Shortest-Path FND": format_lifetime_metric(fnd_sp),
                        "Energy-Aware FND": format_lifetime_metric(fnd_ea),
                        "FND Difference": f"+{diff}" if isinstance(diff, (int, float)) and diff > 0 else str(diff),
                        "Shortest-Path PDR": f"{r_sp.get('packet_delivery_ratio', 0.0):.4f}",
                        "Energy-Aware PDR": f"{r_ea.get('packet_delivery_ratio', 0.0):.4f}",
                        "Better Lifetime": outcome,
                    })

                # High-level outcome summary banner
                st.markdown(
                    f'<div class="outcome-box">'
                    f'<strong>Evaluation Summary ({n_seeds} paired seeds):</strong> '
                    f'Energy-Aware improved FND in <strong>{ea_improvements}</strong> seeds, '
                    f'tied in <strong>{ea_ties}</strong> seeds, '
                    f'and Shortest-Path was better in <strong>{sp_better}</strong> seeds.'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Aggregate summary table
                sp_mean_fnd = np.mean(sp_fnds) if sp_fnds else "Not observed"
                ea_mean_fnd = np.mean(ea_fnds) if ea_fnds else "Not observed"
                sp_mean_pdr = np.mean(sp_pdrs) if sp_pdrs else 0.0
                ea_mean_pdr = np.mean(ea_pdrs) if ea_pdrs else 0.0
                sp_mean_eng = np.mean(sp_energies) if sp_energies else 0.0
                ea_mean_eng = np.mean(ea_energies) if ea_energies else 0.0

                summary_df = pd.DataFrame([
                    {
                        "Performance Metric": "Mean First Node Death (FND)",
                        "Shortest Path": f"{sp_mean_fnd:.1f} rounds" if isinstance(sp_mean_fnd, float) else str(sp_mean_fnd),
                        "Energy-Aware": f"{ea_mean_fnd:.1f} rounds" if isinstance(ea_mean_fnd, float) else str(ea_mean_fnd),
                        "Difference (EA - SP)": f"{(ea_mean_fnd - sp_mean_fnd):+.1f} rounds" if isinstance(sp_mean_fnd, float) and isinstance(ea_mean_fnd, float) else "N/A",
                    },
                    {
                        "Performance Metric": "Mean Packet Delivery Ratio (PDR)",
                        "Shortest Path": f"{sp_mean_pdr:.4f} ({sp_mean_pdr*100:.1f}%)",
                        "Energy-Aware": f"{ea_mean_pdr:.4f} ({ea_mean_pdr*100:.1f}%)",
                        "Difference (EA - SP)": f"{(ea_mean_pdr - sp_mean_pdr):+.4f}",
                    },
                    {
                        "Performance Metric": "Mean Total Energy Consumed",
                        "Shortest Path": f"{sp_mean_eng:.4f} J",
                        "Energy-Aware": f"{ea_mean_eng:.4f} J",
                        "Difference (EA - SP)": f"{(ea_mean_eng - sp_mean_eng):+.4f} J",
                    },
                ])
                st.table(summary_df)

                # Detailed Per-seed breakdown
                with st.expander("Detailed Per-Seed Breakdown", expanded=True):
                    st.dataframe(pd.DataFrame(paired_rows), use_container_width=True)

                # Paired Comparison Chart
                st.markdown('<div class="section-title">Comparative Visualizations</div>', unsafe_allow_html=True)
                fig_comp = plot_comparison_results(sp_runs, ea_runs, "Shortest Path", "Energy-Aware")
                if fig_comp:
                    st.pyplot(fig_comp)
                    plt.close(fig_comp)

                # Download comparison results
                st.download_button(
                    label="Download Comparison Data (JSON)",
                    data=json.dumps(comp_data, indent=2),
                    file_name="paired_comparison_results.json",
                    mime="application/json",
                )

    # -----------------------------------------------------------------------
    # SECTION C: VIEW PREVIOUS RESULTS
    # -----------------------------------------------------------------------
    with tab_results:
        st.markdown('<div class="section-title">Inspect Saved Simulation and Experiment Results</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">Browse previously generated result files from the results directory or upload an external JSON file.</div>', unsafe_allow_html=True)

        result_files = find_saved_result_files("results")
        selected_file: Optional[Path] = None

        r_col1, r_col2 = st.columns([2, 1])
        with r_col1:
            if result_files:
                file_options = [str(f.relative_to(Path("."))) if str(f).startswith(".") else str(f) for f in result_files]
                selected_rel_path = st.selectbox("Select saved result file:", file_options)
                if selected_rel_path:
                    selected_file = Path(selected_rel_path)
            else:
                st.info("No saved JSON result files found in the results directory.")

        with r_col2:
            uploaded_file = st.file_uploader("Upload external result JSON:", type=["json"])
            if uploaded_file is not None:
                try:
                    uploaded_data = json.load(uploaded_file)
                    st.success(f"File loaded: {uploaded_file.name}")
                    selected_file = None  # Prioritize uploaded data
                except Exception as e:
                    st.error(f"Failed to parse uploaded JSON: {e}")
                    uploaded_data = None
            else:
                uploaded_data = None

        # Render loaded data
        data_to_show = None
        if uploaded_data is not None:
            data_to_show = uploaded_data
        elif selected_file is not None:
            data_to_show, err = load_result_file(selected_file)
            if err:
                st.error(f"Error: {err}")

        if data_to_show:
            st.divider()

            # Check if this is a comparison summary file
            if "comparison" in data_to_show or "algorithm_a" in data_to_show:
                st.markdown('<div class="section-title">Comparison Experiment Summary</div>', unsafe_allow_html=True)
                st.json(data_to_show)

            # Check if this is a single simulation result
            elif "round_metrics" in data_to_show or "packet_delivery_ratio" in data_to_show:
                st.markdown('<div class="section-title">Single Simulation Result</div>', unsafe_allow_html=True)
                display_simulation_results(data_to_show)

                # Show configuration
                cfg = data_to_show.get("config", {})
                if cfg:
                    with st.expander("Simulation Configuration", expanded=False):
                        st.json(cfg)

                # Render reconstructed metrics chart
                fig = plot_simulation_metrics(data_to_show)
                if fig:
                    st.markdown('<div class="section-desc" style="margin-top: 1rem;">Reconstructed round-by-round time-series curves:</div>', unsafe_allow_html=True)
                    st.pyplot(fig)
                    plt.close(fig)
                else:
                    st.info("No round-by-round time-series metrics available in this result file.")
            else:
                st.markdown('<div class="section-title">Raw Result Data</div>', unsafe_allow_html=True)
                st.json(data_to_show)


if __name__ == "__main__":
    main()
