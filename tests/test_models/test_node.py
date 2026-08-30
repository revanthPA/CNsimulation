"""
Tests for the Node model.
"""

import pytest
from energy_routing.models.node import Node


class TestNodeCreation:
    """Tests for Node creation and initialization."""

    def test_node_creation_with_defaults(self):
        """Test creating a node with default values."""
        node = Node(
            node_id=1,
            x=0.0,
            y=0.0,
            initial_energy=1.0,
            remaining_energy=1.0
        )
        assert node.node_id == 1
        assert node.x == 0.0
        assert node.y == 0.0
        assert node.initial_energy == 1.0
        assert node.remaining_energy == 1.0
        assert node.is_alive is True
        assert node.packets_sent == 0
        assert node.packets_received == 0
        assert node.packets_forwarded == 0
        assert node.packets_dropped == 0

    def test_node_creation_with_all_stats(self):
        """Test creating a node with all statistics."""
        node = Node(
            node_id=2,
            x=10.0,
            y=20.0,
            initial_energy=5.0,
            remaining_energy=3.0,
            is_alive=True,
            packets_sent=10,
            packets_received=5,
            packets_forwarded=3,
            packets_dropped=2
        )
        assert node.node_id == 2
        assert node.x == 10.0
        assert node.y == 20.0
        assert node.initial_energy == 5.0
        assert node.remaining_energy == 3.0
        assert node.is_alive is True
        assert node.packets_sent == 10

    def test_node_negative_initial_energy_raises(self):
        """Test that negative initial energy raises ValueError."""
        with pytest.raises(ValueError, match="initial_energy must be >= 0"):
            Node(1, 0, 0, -1.0, 1.0)

    def test_node_negative_remaining_energy_raises(self):
        """Test that negative remaining energy raises ValueError."""
        with pytest.raises(ValueError, match="remaining_energy must be >= 0"):
            Node(1, 0, 0, 1.0, -1.0)

    def test_node_remaining_exceeds_initial_clamped(self):
        """Test that remaining energy exceeding initial is clamped."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=2.0)
        assert node.remaining_energy == 1.0


class TestNodeEnergyConsumption:
    """Tests for Node energy consumption."""

    def test_consume_energy_success(self):
        """Test successful energy consumption."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        died = node.consume_energy(0.5)
        assert not died
        assert node.remaining_energy == 0.5
        assert node.is_alive is True

    def test_consume_energy_node_dies(self):
        """Test that node dies when energy reaches zero."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        died = node.consume_energy(1.5)
        assert died
        assert node.remaining_energy == 0.0
        assert node.is_alive is False

    def test_consume_energy_exactly_zero(self):
        """Test consuming exactly all remaining energy."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        died = node.consume_energy(1.0)
        assert died
        assert node.remaining_energy == 0.0
        assert node.is_alive is False

    def test_consume_energy_negative_amount_raises(self):
        """Test that negative energy amount raises ValueError."""
        node = Node(1, 0, 0, 1.0, 1.0)
        with pytest.raises(ValueError, match="Energy consumption amount must be >= 0"):
            node.consume_energy(-0.5)

    def test_consume_energy_dead_node(self):
        """Test consuming energy on a dead node."""
        node = Node(1, 0, 0, 1.0, 0.0, is_alive=False)
        died = node.consume_energy(0.5)
        assert not died  # Already dead
        assert node.remaining_energy == 0.0
        assert node.is_alive is False

    def test_energy_clamped_to_zero(self):
        """Test that energy is clamped to zero, not negative."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        node.consume_energy(2.0)
        assert node.remaining_energy == 0.0


class TestNodeTransmission:
    """Tests for Node transmission capability."""

    def test_can_transmit_with_sufficient_energy(self):
        """Test that node can transmit with sufficient energy."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        assert node.can_transmit(0.5) is True

    def test_can_transmit_with_exact_energy(self):
        """Test that node can transmit with exact energy."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=1.0)
        assert node.can_transmit(1.0) is True

    def test_can_transmit_with_insufficient_energy(self):
        """Test that node cannot transmit with insufficient energy."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=0.5)
        assert node.can_transmit(1.0) is False

    def test_can_transmit_dead_node(self):
        """Test that dead node cannot transmit."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=0.0, is_alive=False)
        assert node.can_transmit(0.1) is False

    def test_can_transmit_zero_cost(self):
        """Test that node can transmit with zero cost."""
        node = Node(1, 0, 0, initial_energy=1.0, remaining_energy=0.0, is_alive=True)
        assert node.can_transmit(0.0) is True
