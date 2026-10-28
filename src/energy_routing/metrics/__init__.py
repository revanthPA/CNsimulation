"""
Metrics module for Wireless Sensor Network simulation.

Contains:
- MetricsCollector
- Utility functions for metric calculation
"""

from energy_routing.metrics.collector import (
    MetricsCollector,
    AggregatedMetrics,
    calculate_avg_hop_count,
    calculate_total_route_distance
)
from energy_routing.metrics.paired import compare_paired_lifetimes

__all__ = [
    "MetricsCollector",
    "AggregatedMetrics",
    "calculate_avg_hop_count",
    "calculate_total_route_distance",
    "compare_paired_lifetimes",
]
