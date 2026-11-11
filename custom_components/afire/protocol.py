"""Pure protocol helpers for the AFIRE Gizwits GAgent connection."""

from __future__ import annotations

from dataclasses import dataclass

MAGIC = b"\x00\x00\x00\x03"


class ProtocolError(Exception):
    """Raised when a GAgent frame is invalid."""


@dataclass(frozen=True, slots=True)
class AfireState:
    """Decoded five-byte AFIRE datapoint state."""

    bits: int
    flame: int
    speed: int

    def enabled(self, flag: int) -> bool:
        """Return whether a boolean datapoint is enabled."""
        return bool(self.bits & flag)


def encode_varint(value: int) -> bytes:
    """Encode a non-negative integer using protobuf-style varint encoding."""
    if value < 0:
        raise ValueError("value must be non-negative")
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            return bytes(result)


def build_frame(command: int, body: bytes = b"") -> bytes:
    """Build a GAgent LAN frame."""
    payload = b"\x00" + command.to_bytes(2, "big") + body
    return MAGIC + encode_varint(len(payload)) + payload


def decode_state(values: bytes) -> AfireState:
    """Decode the fixed five-byte AFIRE value block."""
    if len(values) < 5:
        raise ProtocolError(f"state is too short: {len(values)} bytes")
    return AfireState(
        bits=int.from_bytes(values[0:3], "big"),
        flame=values[3] + 1,
        speed=values[4] + 1,
    )


def build_control_body(
    sequence: int,
    flags: int,
    bits: int,
    flame: int,
    speed: int,
) -> bytes:
    """Build the body of command 0x93 for the AFIRE datapoint layout."""
    if not 1 <= flame <= 8 or not 1 <= speed <= 8:
        raise ValueError("flame and speed must be between 1 and 8")
    if not 0 <= flags <= 0xFFFFFF or not 0 <= bits <= 0xFFFFFF:
        raise ValueError("flags and bits must fit into three bytes")

    return b"".join(
        (
            sequence.to_bytes(4, "big"),
            b"\x01",
            flags.to_bytes(3, "big"),
            bits.to_bytes(3, "big"),
            bytes((flame - 1, speed - 1)),
        )
    )
