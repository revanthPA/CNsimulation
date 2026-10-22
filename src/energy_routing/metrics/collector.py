"""
Metrics collection and analysis for Wireless Sensor Network simulation.

Provides utilities for computing aggregate metrics across simulation runs.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import statistics

from energy_routing.models.result import SimulationResult, RoundMetrics


@dataclass
class AggregatedMetrics:
    """
    Aggregated metrics across multiple simulation runs.
    
    Attributes:
        num_runs: Number of simulation runs aggregated
        mean_fnd: Mean First Node Death round
        std_fnd: Standard deviation of FND
        mean_hnd: Mean Half Node Death round
        std_hnd: Standard deviation of HND
        mean_lnd: Mean Last Node Death round
        std_lnd: Standard deviation of LND
        mean_pdr: Mean Packet Delivery Ratio
        std_pdr: Standard deviation of PDR
        mean_avg_hop_count: Mean average hop count
        std_avg_hop_count: Standard deviation of average hop count
        mean_total_route_distance: Mean total route distance
        std_total_route_distance: Standard deviation of total route distance
        mean_final_energy: Mean final total remaining energy
        std_final_energy: Standard deviation of final total remaining energy
    """
    num_runs: int
    mean_fnd: Optional[float]
    std_fnd: Optional[float]
    mean_hnd: Optional[float]
    std_hnd: Optional[float]
    mean_lnd: Optional[float]
    std_lnd: Optional[float]
    mean_pdr: float
    std_pdr: float
    mean_avg_hop_count: Optional[float]
    std_avg_hop_count: Optional[float]
    mean_total_route_distance: Optional[float]
    std_total_route_distance: Optional[float]
    mean_final_energy: float
    std_final_energy: float


class MetricsCollector:
    """
    Collects and analyzes metrics from simulation runs.
    
    Can compute aggregate statistics across multiple simulation results
    for comparative analysis.
    """
    
    def __init__(self):
        """Initialize an empty metrics collector."""
        self.results: List[SimulationResult] = []
    
    def add_result(self, result: SimulationResult):
        """
        Add a simulation result to the collector.
        
        Args:
            result: SimulationResult to add
        """
        self.results.append(result)
    
    def add_results(self, results: List[SimulationResult]):
        """
        Add multiple simulation results.
        
        Args:
            results: List of SimulationResult objects
        """
        self.results.extend(results)
    
    def clear(self):
        """Clear all collected results."""
        self.results.clear()
    
    def get_results(self) -> List[SimulationResult]:
        """Get all collected results."""
        return self.results.copy()
    
    def compute_aggregated_metrics(self) -> AggregatedMetrics:
        """
        Compute aggregated metrics across all collected results.
        
        Returns:
            AggregatedMetrics with mean and std for key metrics
        """
        if not self.results:
            return AggregatedMetrics(
                num_runs=0,
                mean_fnd=None, std_fnd=None,
                mean_hnd=None, std_hnd=None,
                mean_lnd=None, std_lnd=None,
                mean_pdr=0.0, std_pdr=0.0,
                mean_avg_hop_count=None, std_avg_hop_count=None,
                mean_total_route_distance=None, std_total_route_distance=None,
                mean_final_energy=0.0, std_final_energy=0.0
            )
        
        # Helper to compute mean and std, handling None values
        def compute_stats(values: List[Optional[float]]) -> tuple:
            valid = [v for v in values if v is not None]
            if not valid:
                return None, None
            mean = statistics.mean(valid)
            std = statistics.stdev(valid) if len(valid) > 1 else 0.0
            return mean, std
        
        # FND, HND, LND
        fnd_values = [r.fnd for r in self.results]
        hnd_values = [r.hnd for r in self.results]
        lnd_values = [r.lnd for r in self.results]
        
        mean_fnd, std_fnd = compute_stats(fnd_values)
        mean_hnd, std_hnd = compute_stats(hnd_values)
        mean_lnd, std_lnd = compute_stats(lnd_values)
        
        # PDR
        pdr_values = [r.packet_delivery_ratio for r in self.results]
        mean_pdr = statistics.mean(pdr_values)
        std_pdr = statistics.stdev(pdr_values) if len(pdr_values) > 1 else 0.0
        
        # Avg hop count
        hop_values = [r.avg_hop_count for r in self.results]
        mean_hop, std_hop = compute_stats(hop_values)
        
        # Total route distance
        dist_values = [r.total_route_distance for r in self.results]
        mean_dist, std_dist = compute_stats(dist_values)
        
        # Final energy
        energy_values = [r.final_total_remaining_energy for r in self.results]
        mean_energy = statistics.mean(energy_values)
        std_energy = statistics.stdev(energy_values) if len(energy_values) > 1 else 0.0
        
        return AggregatedMetrics(
            num_runs=len(self.results),
            mean_fnd=mean_fnd, std_fnd=std_fnd,
            mean_hnd=mean_hnd, std_hnd=std_hnd,
            mean_lnd=mean_lnd, std_lnd=std_lnd,
            mean_pdr=mean_pdr, std_pdr=std_pdr,
            mean_avg_hop_count=mean_hop, std_avg_hop_count=std_hop,
            mean_total_route_distance=mean_dist, std_total_route_distance=std_dist,
            mean_final_energy=mean_energy, std_final_energy=std_energy
        )
    
    def compute_round_aggregates(self) -> Dict[int, Dict[str, float]]:
        """
        Compute aggregate metrics per round across all runs.
        
        Returns:
            Dictionary mapping round number to aggregate metrics:
            - mean_alive_nodes, std_alive_nodes
            - mean_dead_nodes, std_dead_nodes
            - mean_remaining_energy, std_remaining_energy
            - mean_energy_consumed, std_energy_consumed
            - mean_packets_generated, std_packets_generated
            - mean_packets_delivered, std_packets_delivered
            - mean_packets_lost, std_packets_lost
        """
        if not self.results:
            return {}
        
        # Find max rounds across all results
        max_rounds = max(len(r.round_metrics) for r in self.results)
        
        aggregates = {}
        for round_num in range(max_rounds):
            # Collect values for this round from all results that have it
            alive_vals = []
            dead_vals = []
            energy_rem_vals = []
            energy_cons_vals = []
            gen_vals = []
            del_vals = []
            lost_vals = []
            
            for result in self.results:
                if round_num < len(result.round_metrics):
                    m = result.round_metrics[round_num]
                    alive_vals.append(m.alive_nodes)
                    dead_vals.append(m.dead_nodes)
                    energy_rem_vals.append(m.total_remaining_energy)
                    energy_cons_vals.append(m.total_energy_consumed)
                    gen_vals.append(m.packets_generated)
                    del_vals.append(m.packets_delivered)
                    lost_vals.append(m.packets_lost)
            
            if alive_vals:
                aggregates[round_num] = {
                    "mean_alive_nodes": statistics.mean(alive_vals),
                    "std_alive_nodes": statistics.stdev(alive_vals) if len(alive_vals) > 1 else 0.0,
                    "mean_dead_nodes": statistics.mean(dead_vals),
                    "std_dead_nodes": statistics.stdev(dead_vals) if len(dead_vals) > 1 else 0.0,
                    "mean_remaining_energy": statistics.mean(energy_rem_vals),
                    "std_remaining_energy": statistics.stdev(energy_rem_vals) if len(energy_rem_vals) > 1 else 0.0,
                    "mean_energy_consumed": statistics.mean(energy_cons_vals),
                    "std_energy_consumed": statistics.stdev(energy_cons_vals) if len(energy_cons_vals) > 1 else 0.0,
                    "mean_packets_generated": statistics.mean(gen_vals),
                    "std_packets_generated": statistics.stdev(gen_vals) if len(gen_vals) > 1 else 0.0,
                    "mean_packets_delivered": statistics.mean(del_vals),
                    "std_packets_delivered": statistics.stdev(del_vals) if len(del_vals) > 1 else 0.0,
                    "mean_packets_lost": statistics.mean(lost_vals),
                    "std_packets_lost": statistics.stdev(lost_vals) if len(lost_vals) > 1 else 0.0,
                }
        
        return aggregates
    
    def compare_algorithms(
        self,
        results_a: List[SimulationResult],
        results_b: List[SimulationResult],
        label_a: str = "Algorithm A",
        label_b: str = "Algorithm B"
    ) -> Dict[str, Any]:
        """
        Compare two sets of simulation results (e.g., two routing algorithms).
        
        Args:
            results_a: Results from first algorithm
            results_b: Results from second algorithm
            label_a: Label for first algorithm
            label_b: Label for second algorithm
            
        Returns:
            Dictionary with comparison metrics
        """
        def get_stats(results: List[SimulationResult]) -> Dict[str, Any]:
            if not results:
                return {}
            fnd = [r.fnd for r in results if r.fnd is not None]
            hnd = [r.hnd for r in results if r.hnd is not None]
            lnd = [r.lnd for r in results if r.lnd is not None]
            pdr = [r.packet_delivery_ratio for r in results]
            hop = [r.avg_hop_count for r in results if r.avg_hop_count is not None]
            dist = [r.total_route_distance for r in results if r.total_route_distance is not None]
            energy = [r.final_total_remaining_energy for r in results]
            
            return {
                "fnd_mean": statistics.mean(fnd) if fnd else None,
                "fnd_std": statistics.stdev(fnd) if len(fnd) > 1 else 0.0,
                "hnd_mean": statistics.mean(hnd) if hnd else None,
                "hnd_std": statistics.stdev(hnd) if len(hnd) > 1 else 0.0,
                "lnd_mean": statistics.mean(lnd) if lnd else None,
                "lnd_std": statistics.stdev(lnd) if len(lnd) > 1 else 0.0,
                "pdr_mean": statistics.mean(pdr),
                "pdr_std": statistics.stdev(pdr) if len(pdr) > 1 else 0.0,
                "avg_hop_count_mean": statistics.mean(hop) if hop else None,
                "avg_hop_count_std": statistics.stdev(hop) if len(hop) > 1 else 0.0,
                "total_route_distance_mean": statistics.mean(dist) if dist else None,
                "total_route_distance_std": statistics.stdev(dist) if len(dist) > 1 else 0.0,
                "final_energy_mean": statistics.mean(energy),
                "final_energy_std": statistics.stdev(energy) if len(energy) > 1 else 0.0,
                "num_runs": len(results)
            }
        
        stats_a = get_stats(results_a)
        stats_b = get_stats(results_b)
        
        comparison = {
            label_a: stats_a,
            label_b: stats_b,
            "improvement": {}
        }
        
        # Calculate percentage improvements (positive = B better than A)
        for key in ["fnd_mean", "hnd_mean", "lnd_mean", "pdr_mean", "final_energy_mean"]:
            val_a = stats_a.get(key)
            val_b = stats_b.get(key)
            if val_a is not None and val_b is not None and val_a != 0:
                pct = ((val_b - val_a) / abs(val_a)) * 100
                comparison["improvement"][key] = pct
        
        # For hop count and distance, lower is better
        for key in ["avg_hop_count_mean", "total_route_distance_mean"]:
            val_a = stats_a.get(key)
            val_b = stats_b.get(key)
            if val_a is not None and val_b is not None and val_a != 0:
                pct = ((val_a - val_b) / abs(val_a)) * 100  # Inverted: lower is better
                comparison["improvement"][key] = pct
        
        return comparison
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export all collected results and aggregates to dictionary.
        
        Returns:
            Dictionary with all results and aggregated metrics
        """
        return {
            "num_results": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "aggregated_metrics": self.compute_aggregated_metrics().__dict__,
            "round_aggregates": self.compute_round_aggregates()
        }


def calculate_avg_hop_count(delivered_packets: List) -> Optional[float]:
    """
    Calculate average hop count from delivered packets.
    
    Args:
        delivered_packets: List of delivered Packet objects
        
    Returns:
        Average hop count, or None if no packets delivered
    """
    if not delivered_packets:
        return None
    
    total_hops = sum(len(p.path) - 1 for p in delivered_packets)
    return total_hops / len(delivered_packets)


def calculate_total_route_distance(
    delivered_packets: List,
    graph
) -> Optional[float]:
    """
    Calculate total route distance from delivered packets.
    
    Args:
        delivered_packets: List of delivered Packet objects
        graph: NetworkX graph with distance edge attributes
        
    Returns:
        Total route distance in meters, or None if no packets delivered
    """
    if not delivered_packets:
        return None
    
    total_dist = 0.0
    for packet in delivered_packets:
        for i in range(len(packet.path) - 1):
            u = packet.path[i]
            v = packet.path[i + 1]
            if graph.has_edge(u, v):
                total_dist += graph[u][v].get("distance", 0.0)
    return total_dist