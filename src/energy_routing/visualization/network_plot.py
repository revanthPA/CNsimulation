"""
Network topology visualization for Wireless Sensor Network simulation.

Provides functions to plot network topology with nodes and edges.
"""

import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from energy_routing.network.topology import Topology
from energy_routing.network.graph import build_graph
from energy_routing.models.node import Node
from energy_routing.config import NetworkConfig


def plot_network_topology(
    topology: Topology,
    graph=None,
    highlight_nodes: Optional[List[int]] = None,
    highlight_path: Optional[List[int]] = None,
    title: str = "WSN Topology",
    figsize: Tuple[int, int] = (10, 10),
    save_path: Optional[str] = None,
    show: bool = False,
    node_size: int = 100,
    base_station_size: int = 300,
    dead_node_alpha: float = 0.3
) -> plt.Figure:
    """
    Plot the network topology.
    
    Args:
        topology: Network topology with node positions
        graph: Optional pre-built graph (built if not provided)
        highlight_nodes: List of node IDs to highlight
        highlight_path: List of node IDs representing a path to highlight
        title: Plot title
        figsize: Figure size (width, height)
        save_path: Path to save figure (if provided)
        show: Whether to display the plot
        node_size: Size of regular nodes
        base_station_size: Size of base station node
        dead_node_alpha: Alpha value for dead nodes
        
    Returns:
        Matplotlib Figure object
    """
    if graph is None:
        # Need communication range - use a default or extract from topology
        # For now, build with a large range to show all possible edges
        comm_range = max(topology.width, topology.height) * 1.5
        graph = build_graph(topology, comm_range)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Get node positions
    pos = {nid: (node.x, node.y) for nid, node in topology.nodes.items()}
    
    # Separate nodes by type
    base_station_id = topology.base_station_id
    sensor_nodes = [nid for nid in topology.nodes if nid != base_station_id]
    
    # Separate alive and dead sensor nodes
    alive_sensors = [nid for nid in sensor_nodes if topology.nodes[nid].is_alive]
    dead_sensors = [nid for nid in sensor_nodes if not topology.nodes[nid].is_alive]
    
    # Draw edges
    nx.draw_networkx_edges(
        graph, pos,
        edge_color='gray',
        alpha=0.3,
        width=0.5,
        ax=ax
    )
    
    # Draw highlighted path edges if provided
    if highlight_path and len(highlight_path) >= 2:
        path_edges = list(zip(highlight_path[:-1], highlight_path[1:]))
        nx.draw_networkx_edges(
            graph, pos,
            edgelist=path_edges,
            edge_color='red',
            width=3,
            alpha=0.8,
            ax=ax
        )
    
    # Draw dead sensor nodes
    if dead_sensors:
        nx.draw_networkx_nodes(
            graph, pos,
            nodelist=dead_sensors,
            node_color='red',
            node_size=node_size,
            alpha=dead_node_alpha,
            ax=ax,
            label='Dead Sensors'
        )
    
    # Draw alive sensor nodes
    if alive_sensors:
        node_colors = []
        for nid in alive_sensors:
            if highlight_nodes and nid in highlight_nodes:
                node_colors.append('orange')
            else:
                node_colors.append('blue')
        
        nx.draw_networkx_nodes(
            graph, pos,
            nodelist=alive_sensors,
            node_color=node_colors,
            node_size=node_size,
            alpha=1.0,
            ax=ax,
            label='Alive Sensors'
        )
    
    # Draw base station
    nx.draw_networkx_nodes(
        graph, pos,
        nodelist=[base_station_id],
        node_color='green',
        node_size=base_station_size,
        node_shape='s',  # Square for base station
        alpha=1.0,
        ax=ax,
        label='Base Station'
    )
    
    # Draw node labels (optional, can be cluttered)
    # nx.draw_networkx_labels(graph, pos, font_size=8, ax=ax)
    
    ax.set_title(title)
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    # Set axis limits with some padding
    padding = max(topology.width, topology.height) * 0.05
    ax.set_xlim(-padding, topology.width + padding)
    ax.set_ylim(-padding, topology.height + padding)
    
    plt.tight_layout()
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_energy_heatmap(
    topology: Topology,
    graph=None,
    title: str = "Node Energy Levels",
    figsize: Tuple[int, int] = (10, 10),
    save_path: Optional[str] = None,
    show: bool = False,
    cmap: str = 'RdYlGn'
) -> plt.Figure:
    """
    Plot network topology colored by residual energy.
    
    Args:
        topology: Network topology with node positions and energy
        graph: Optional pre-built graph
        title: Plot title
        figsize: Figure size
        save_path: Path to save figure
        show: Whether to display the plot
        cmap: Colormap for energy levels
        
    Returns:
        Matplotlib Figure object
    """
    if graph is None:
        comm_range = max(topology.width, topology.height) * 1.5
        graph = build_graph(topology, comm_range)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    pos = {nid: (node.x, node.y) for nid, node in topology.nodes.items()}
    
    # Get energy levels for sensor nodes (normalized 0-1)
    sensor_nodes = [nid for nid in topology.nodes if nid != topology.base_station_id]
    energies = []
    for nid in sensor_nodes:
        node = topology.nodes[nid]
        if node.initial_energy == float('inf'):
            energies.append(1.0)
        elif node.initial_energy > 0:
            energies.append(min(1.0, node.remaining_energy / node.initial_energy))
        else:
            energies.append(0.0)
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.2, width=0.5, ax=ax)
    
    # Draw nodes colored by energy
    scatter = nx.draw_networkx_nodes(
        graph, pos,
        nodelist=sensor_nodes,
        node_color=energies,
        cmap=cmap,
        vmin=0,
        vmax=1,
        node_size=150,
        ax=ax
    )
    
    # Draw base station
    nx.draw_networkx_nodes(
        graph, pos,
        nodelist=[topology.base_station_id],
        node_color='black',
        node_size=300,
        node_shape='s',
        ax=ax,
        label='Base Station'
    )
    
    # Add colorbar
    plt.colorbar(scatter, ax=ax, label='Normalized Residual Energy')
    
    ax.set_title(title)
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    padding = max(topology.width, topology.height) * 0.05
    ax.set_xlim(-padding, topology.width + padding)
    ax.set_ylim(-padding, topology.height + padding)
    
    plt.tight_layout()
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig