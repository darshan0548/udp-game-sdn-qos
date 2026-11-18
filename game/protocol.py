"""Shared packet format for the UDP multiplayer game.

All packets are UTF-8 JSON dictionaries. Both server.py and client.py import
these helpers so message encoding and decoding stay consistent.
"""
import json

BUFFER_SIZE = 4096

# Packet types
JOIN = "JOIN"
JOIN_ACK = "JOIN_ACK"
JOIN_REJECT = "JOIN_REJECT"
STATE = "STATE"
WORLD = "WORLD"
PING = "PING"
PONG = "PONG"
LEAVE = "LEAVE"
STATS = "STATS"
STATS_ACK = "STATS_ACK"
ERROR = "ERROR"


def encode_packet(message):
    """Convert a Python dictionary to UTF-8 JSON bytes."""
    return json.dumps(message, separators=(",", ":")).encode("utf-8")


def decode_packet(data):
    """Convert UTF-8 JSON bytes to a dictionary, or return None if invalid."""
    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(message, dict):
        return None
    if not isinstance(message.get("type"), str):
        return None

    return message
