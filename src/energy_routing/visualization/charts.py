"""
Charts and visualizations for simulation results.

Provides plotting functions for simulation metrics and comparisons.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from energy_routing.models.result import SimulationResult, RoundMetrics
from energy_routing.metrics.collector import AggregatedMetrics


class ResultVisualizer:
    """
    Visualizes simulation results and comparisons.
    
    Provides methods to plot:
    - Node lifetime curves (alive nodes over rounds)
    - Energy depletion over time
    - Packet delivery metrics
    - Algorithm comparison charts
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 6)):
        """
        Initialize visualizer.
        
        Args:
            figsize: Default figure size
        """
        self.figsize = figsize
    
    def plot_alive_nodes_over_time(
        self,
        results: List[SimulationResult],
        labels: Optional[List[str]] = None,
        title: str = "Alive Sensor Nodes Over Time",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot number of alive nodes over simulation rounds.
        
        Args:
            results: List of simulation results
            labels: Labels for each result (for legend)
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        for i, result in enumerate(results):
            rounds = [m.round for m in result.round_metrics]
            alive = [m.alive_nodes for m in result.round_metrics]
            label = labels[i] if labels else f"Run {i+1}"
            ax.plot(rounds, alive, label=label, linewidth=2)
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Alive Sensor Nodes')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        if labels:
            ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_energy_over_time(
        self,
        results: List[SimulationResult],
        labels: Optional[List[str]] = None,
        title: str = "Total Remaining Energy Over Time",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot total remaining energy over simulation rounds.
        
        Args:
            results: List of simulation results
            labels: Labels for each result
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        for i, result in enumerate(results):
            rounds = [m.round for m in result.round_metrics]
            energy = [m.total_remaining_energy for m in result.round_metrics]
            label = labels[i] if labels else f"Run {i+1}"
            ax.plot(rounds, energy, label=label, linewidth=2)
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Total Remaining Energy (J)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        if labels:
            ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_packets_over_time(
        self,
        results: List[SimulationResult],
        labels: Optional[List[str]] = None,
        title: str = "Packets Generated/Delivered/Lost Per Round",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot packet statistics over simulation rounds.
        
        Args:
            results: List of simulation results
            labels: Labels for each result
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        for i, result in enumerate(results):
            rounds = [m.round for m in result.round_metrics]
            label = labels[i] if labels else f"Run {i+1}"
            color = plt.cm.tab10(i % 10)
            
            # Generated
            gen = [m.packets_generated for m in result.round_metrics]
            axes[0].plot(rounds, gen, label=label, color=color, linewidth=2)
            
            # Delivered
            delv = [m.packets_delivered for m in result.round_metrics]
            axes[1].plot(rounds, delv, label=label, color=color, linewidth=2)
            
            # Lost
            lost = [m.packets_lost for m in result.round_metrics]
            axes[2].plot(rounds, lost, label=label, color=color, linewidth=2)
        
        axes[0].set_title('Packets Generated')
        axes[1].set_title('Packets Delivered')
        axes[2].set_title('Packets Lost')
        
        for ax in axes:
            ax.set_xlabel('Round')
            ax.set_ylabel('Count')
            ax.grid(True, alpha=0.3)
            if labels:
                ax.legend()
        
        fig.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_pdr_comparison(
        self,
        results_a: List[SimulationResult],
        results_b: List[SimulationResult],
        label_a: str = "Algorithm A",
        label_b: str = "Algorithm B",
        title: str = "Packet Delivery Ratio Comparison",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Compare PDR between two algorithms across seeds.
        
        Args:
            results_a: Results from first algorithm
            results_b: Results from second algorithm
            label_a: Label for algorithm A
            label_b: Label for algorithm B
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        pdr_a = [r.packet_delivery_ratio for r in results_a]
        pdr_b = [r.packet_delivery_ratio for r in results_b]
        
        seeds = list(range(1, max(len(pdr_a), len(pdr_b)) + 1))
        
        x = np.arange(len(seeds))
        width = 0.35
        
        bars_a = ax.bar(x - width/2, pdr_a, width, label=label_a, alpha=0.8)
        bars_b = ax.bar(x + width/2, pdr_b, width, label=label_b, alpha=0.8)
        
        ax.set_xlabel('Seed')
        ax.set_ylabel('Packet Delivery Ratio')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(seeds)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 1.05)
        
        # Add value labels on bars
        for bar in bars_a:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        for bar in bars_b:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_lifetime_comparison(
        self,
        results_a: List[SimulationResult],
        results_b: List[SimulationResult],
        label_a: str = "Algorithm A",
        label_b: str = "Algorithm B",
        title: str = "Network Lifetime Comparison (FND, HND, LND)",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Compare FND, HND, LND between two algorithms.
        
        Args:
            results_a: Results from first algorithm
            results_b: Results from second algorithm
            label_a: Label for algorithm A
            label_b: Label for algorithm B
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        def get_death_rounds(results: List[SimulationResult]) -> Dict[str, List[Optional[int]]]:
            return {
                'FND': [r.fnd for r in results],
                'HND': [r.hnd for r in results],
                'LND': [r.lnd for r in results]
            }
        
        death_a = get_death_rounds(results_a)
        death_b = get_death_rounds(results_b)
        
        categories = ['FND', 'HND', 'LND']
        x = np.arange(len(categories))
        width = 0.35
        
        # Calculate means (ignoring None)
        means_a = []
        means_b = []
        for cat in categories:
            vals_a = [v for v in death_a[cat] if v is not None]
            vals_b = [v for v in death_b[cat] if v is not None]
            means_a.append(np.mean(vals_a) if vals_a else 0)
            means_b.append(np.mean(vals_b) if vals_b else 0)
        
        bars_a = ax.bar(x - width/2, means_a, width, label=label_a, alpha=0.8)
        bars_b = ax.bar(x + width/2, means_b, width, label=label_b, alpha=0.8)
        
        ax.set_ylabel('Round Number')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars_a, means_a):
            if val > 0:
                ax.annotate(f'{val:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, val),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom')
        for bar, val in zip(bars_b, means_b):
            if val > 0:
                ax.annotate(f'{val:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, val),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_hop_count_distribution(
        self,
        results: List[SimulationResult],
        labels: Optional[List[str]] = None,
        title: str = "Average Hop Count per Delivered Packet",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot average hop count for delivered packets.
        
        Args:
            results: List of simulation results
            labels: Labels for each result
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        hop_counts = []
        valid_labels = []
        
        for i, result in enumerate(results):
            if result.avg_hop_count is not None:
                hop_counts.append(result.avg_hop_count)
                valid_labels.append(labels[i] if labels else f"Run {i+1}")
        
        if not hop_counts:
            ax.text(0.5, 0.5, 'No hop count data available', 
                   ha='center', va='center', transform=ax.transAxes)
        else:
            bars = ax.bar(range(len(hop_counts)), hop_counts, alpha=0.8)
            ax.set_xticks(range(len(hop_counts)))
            ax.set_xticklabels(valid_labels, rotation=45, ha='right')
            ax.set_ylabel('Average Hop Count')
            
            # Add value labels
            for bar, val in zip(bars, hop_counts):
                ax.annotate(f'{val:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, val),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom')
        
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_aggregated_metrics(
        self,
        metrics: AggregatedMetrics,
        title: str = "Aggregated Metrics",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot aggregated metrics with error bars.
        
        Args:
            metrics: AggregatedMetrics object
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        # PDR
        axes[0].bar(['PDR'], [metrics.mean_pdr], yerr=[metrics.std_pdr], 
                   capsize=5, alpha=0.8, color='blue')
        axes[0].set_ylabel('Packet Delivery Ratio')
        axes[0].set_ylim(0, 1.05)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Lifetime metrics
        lifetime_data = []
        lifetime_labels = []
        lifetime_errors = []
        for label, mean, std in [
            ('FND', metrics.mean_fnd, metrics.std_fnd),
            ('HND', metrics.mean_hnd, metrics.std_hnd),
            ('LND', metrics.mean_lnd, metrics.std_lnd)
        ]:
            if mean is not None:
                lifetime_data.append(mean)
                lifetime_labels.append(label)
                lifetime_errors.append(std if std is not None else 0)
        
        if lifetime_data:
            axes[1].bar(lifetime_labels, lifetime_data, yerr=lifetime_errors,
                       capsize=5, alpha=0.8, color='green')
            axes[1].set_ylabel('Round Number')
            axes[1].grid(True, alpha=0.3, axis='y')
        
        # Hop count
        if metrics.mean_avg_hop_count is not None:
            axes[2].bar(['Avg Hop Count'], [metrics.mean_avg_hop_count],
                       yerr=[metrics.std_avg_hop_count if metrics.std_avg_hop_count else 0],
                       capsize=5, alpha=0.8, color='orange')
            axes[2].set_ylabel('Hop Count')
            axes[2].grid(True, alpha=0.3, axis='y')
        
        # Route distance
        if metrics.mean_total_route_distance is not None:
            axes[3].bar(['Total Route Dist'], [metrics.mean_total_route_distance],
                       yerr=[metrics.std_total_route_distance if metrics.std_total_route_distance else 0],
                       capsize=5, alpha=0.8, color='red')
            axes[3].set_ylabel('Distance (m)')
            axes[3].grid(True, alpha=0.3, axis='y')
        
        for ax in axes:
            ax.set_title(ax.get_ylabel())
        
        fig.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_network_size_scaling(
        self,
        results_by_size: Dict[int, List[SimulationResult]],
        metric: str = 'fnd',
        title: str = "Network Lifetime vs Network Size",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot how a metric scales with network size.
        
        Args:
            results_by_size: Dict mapping network size to list of results
            metric: Metric to plot ('fnd', 'hnd', 'lnd', 'pdr', 'avg_hop_count', 'final_energy')
            title: Plot title
            save_path: Path to save figure
            show: Whether to display
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sizes = sorted(results_by_size.keys())
        means = []
        stds = []
        
        for size in sizes:
            results = results_by_size[size]
            if metric == 'fnd':
                vals = [r.fnd for r in results if r.fnd is not None]
            elif metric == 'hnd':
                vals = [r.hnd for r in results if r.hnd is not None]
            elif metric == 'lnd':
                vals = [r.lnd for r in results if r.lnd is not None]
            elif metric == 'pdr':
                vals = [r.packet_delivery_ratio for r in results]
            elif metric == 'avg_hop_count':
                vals = [r.avg_hop_count for r in results if r.avg_hop_count is not None]
            elif metric == 'final_energy':
                vals = [r.final_total_remaining_energy for r in results]
            else:
                vals = []
            
            if vals:
                means.append(np.mean(vals))
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            else:
                means.append(0)
                stds.append(0)
        
        ax.errorbar(sizes, means, yerr=stds, fmt='o-', capsize=5, linewidth=2, markersize=8)
        ax.set_xlabel('Number of Sensor Nodes')
        ax.set_ylabel(metric.upper())
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig