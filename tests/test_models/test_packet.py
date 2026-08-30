"""
Tests for the Packet model.
"""

import pytest
from dataclasses import replace
from energy_routing.models.packet import Packet, PacketStatus


class TestPacketCreation:
    """Tests for Packet creation and initialization."""

    def test_packet_creation_with_defaults(self):
        """Test creating a packet with default values."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=5,
            generation_round=0,
            size=512
        )
        assert packet.packet_id == 1
        assert packet.source_id == 0
        assert packet.dest_id == 5
        assert packet.generation_round == 0
        assert packet.size == 512
        assert packet.status == PacketStatus.GENERATED
        assert packet.path == ()
        assert packet.delivery_round is None

    def test_packet_creation_with_all_fields(self):
        """Test creating a packet with all fields specified."""
        packet = Packet(
            packet_id=2,
            source_id=1,
            dest_id=6,
            generation_round=5,
            size=1024,
            status=PacketStatus.DELIVERED,
            path=(1, 3, 6),
            delivery_round=10
        )
        assert packet.packet_id == 2
        assert packet.source_id == 1
        assert packet.dest_id == 6
        assert packet.generation_round == 5
        assert packet.size == 1024
        assert packet.status == PacketStatus.DELIVERED
        assert packet.path == (1, 3, 6)
        assert packet.delivery_round == 10

    def test_packet_negative_id_raises(self):
        """Test that negative packet_id raises ValueError."""
        with pytest.raises(ValueError, match="packet_id must be >= 0"):
            Packet(packet_id=-1, source_id=0, dest_id=1, generation_round=0, size=512)

    def test_packet_negative_source_raises(self):
        """Test that negative source_id raises ValueError."""
        with pytest.raises(ValueError, match="Node IDs must be >= 0"):
            Packet(packet_id=1, source_id=-1, dest_id=1, generation_round=0, size=512)

    def test_packet_negative_dest_raises(self):
        """Test that negative dest_id raises ValueError."""
        with pytest.raises(ValueError, match="Node IDs must be >= 0"):
            Packet(packet_id=1, source_id=0, dest_id=-1, generation_round=0, size=512)

    def test_packet_negative_round_raises(self):
        """Test that negative generation_round raises ValueError."""
        with pytest.raises(ValueError, match="generation_round must be >= 0"):
            Packet(packet_id=1, source_id=0, dest_id=1, generation_round=-1, size=512)

    def test_packet_zero_size_raises(self):
        """Test that zero size raises ValueError."""
        with pytest.raises(ValueError, match="size must be > 0"):
            Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=0)

    def test_packet_negative_size_raises(self):
        """Test that negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be > 0"):
            Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=-10)


class TestPacketImmutability:
    """Tests for Packet immutability (frozen dataclass)."""

    def test_packet_is_frozen(self):
        """Test that Packet cannot be modified directly."""
        packet = Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=512)
        with pytest.raises(AttributeError):
            packet.packet_id = 2

    def test_packet_path_is_tuple(self):
        """Test that path is a tuple (immutable)."""
        packet = Packet(
            packet_id=1,
            source_id=0,
            dest_id=1,
            generation_round=0,
            size=512,
            path=(0, 2, 1)
        )
        assert isinstance(packet.path, tuple)


class TestPacketUpdateMethods:
    """Tests for Packet update methods (using dataclasses.replace)."""

    def test_with_status(self):
        """Test updating packet status."""
        packet = Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=512)
        new_packet = packet.with_status(PacketStatus.DELIVERED)
        assert new_packet.status == PacketStatus.DELIVERED
        assert new_packet.packet_id == 1
        assert new_packet.source_id == 0
        # Original packet unchanged
        assert packet.status == PacketStatus.GENERATED

    def test_with_path(self):
        """Test updating packet path."""
        packet = Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=512)
        new_packet = packet.with_path((0, 2, 1))
        assert new_packet.path == (0, 2, 1)
        assert new_packet.packet_id == 1
        # Original packet unchanged
        assert packet.path == ()

    def test_with_delivery_round(self):
        """Test updating delivery round."""
        packet = Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=512)
        new_packet = packet.with_delivery_round(10)
        assert new_packet.delivery_round == 10
        assert new_packet.packet_id == 1
        # Original packet unchanged
        assert packet.delivery_round is None

    def test_chained_updates(self):
        """Test chaining multiple updates."""
        packet = Packet(packet_id=1, source_id=0, dest_id=1, generation_round=0, size=512)
        updated = packet.with_status(PacketStatus.DELIVERED).with_path((0, 1)).with_delivery_round(5)
        assert updated.status == PacketStatus.DELIVERED
        assert updated.path == (0, 1)
        assert updated.delivery_round == 5
        # Original unchanged
        assert packet.status == PacketStatus.GENERATED
        assert packet.path == ()
        assert packet.delivery_round is None
