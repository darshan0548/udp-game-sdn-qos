"""UDP multiplayer game server for localhost testing."""
import socket
import logging
import random
import time

import protocol

# -------------------- CONFIGURATION --------------------
HOST = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = protocol.BUFFER_SIZE
MAX_PLAYERS = 16

# Set to 0.10 or 0.20 to simulate 10% or 20% packet loss.
DROP_RATE = 0.0

# -------------------- LOGGING --------------------
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# player_id -> player details
players = {}
next_player_id = 1

# player_id -> packet statistics
stats = {}


def send_packet(sock, message, address):
    """Encode and send one UDP packet, with optional simulated packet loss."""
    if DROP_RATE > 0 and random.random() < DROP_RATE:
        logging.warning("SIMULATED DROP: outgoing %s to %s", message.get("type"), address)
        return
    sock.sendto(protocol.encode_packet(message), address)


def find_player_by_address(address):
    """Find the player ID belonging to a client's UDP address."""
    for player_id, player in players.items():
        if player["address"] == address:
            return player_id
    return None


def broadcast_world(sock):
    """Broadcast the latest positions to every registered client."""
    world = {
        "type": protocol.WORLD,
        "players": [
            {"player_id": player_id, "x": player["x"], "y": player["y"]}
            for player_id, player in players.items()
        ],
        "server_time": time.time(),
    }
    for player in list(players.values()):
        send_packet(sock, world, player["address"])


def handle_join(sock, address):
    """Register a client. Repeated JOIN packets get the same acknowledgement."""
    global next_player_id

    existing_id = find_player_by_address(address)
    if existing_id is not None:
        send_packet(sock, {"type": protocol.JOIN_ACK, "player_id": existing_id}, address)
        logging.info("JOIN retry acknowledged player_id=%s address=%s", existing_id, address)
        return

    if len(players) >= MAX_PLAYERS:
        send_packet(sock, {"type": protocol.JOIN_REJECT, "reason": "server_full"}, address)
        logging.warning("JOIN rejected: server full address=%s", address)
        return

    player_id = next_player_id
    next_player_id += 1
    players[player_id] = {
        "address": address,
        "x": 0.0,
        "y": 0.0,
        "last_seq": -1,
    }
    stats[player_id] = {"lost": 0, "out_of_order": 0, "duplicates": 0}

    send_packet(sock, {"type": protocol.JOIN_ACK, "player_id": player_id}, address)
    logging.info("PLAYER JOINED player_id=%s address=%s", player_id, address)
    print(f"Player {player_id} joined from {address}. Total players: {len(players)}", flush=True)
    broadcast_world(sock)


def handle_state(sock, message, address):
    """Accept fresh movement updates and broadcast the current world."""
    player_id = find_player_by_address(address)
    if player_id is None:
        send_packet(sock, {"type": protocol.ERROR, "reason": "join_first"}, address)
        logging.warning("STATE from unregistered address=%s", address)
        return

    seq = message.get("seq")
    x = message.get("x")
    y = message.get("y")

    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
        logging.warning("Invalid sequence number from player_id=%s", player_id)
        return

    if (
        isinstance(x, bool) or isinstance(y, bool)
        or not isinstance(x, (int, float)) or not isinstance(y, (int, float))
        or not (-1_000_000 <= x <= 1_000_000)
        or not (-1_000_000 <= y <= 1_000_000)
    ):
        logging.warning("Invalid position from player_id=%s", player_id)
        return

    player = players[player_id]
    counter = stats[player_id]
    last_seq = player["last_seq"]

    if seq == last_seq:
        counter["duplicates"] += 1
        logging.info("DUPLICATE player_id=%s seq=%s total=%s", player_id, seq, counter["duplicates"])
        return

    if seq < last_seq:
        counter["out_of_order"] += 1
        logging.info(
            "STALE/OUT_OF_ORDER player_id=%s seq=%s last_seq=%s total=%s",
            player_id, seq, last_seq, counter["out_of_order"]
        )
        return

    if last_seq >= 0 and seq > last_seq + 1:
        missing = seq - last_seq - 1
        counter["lost"] += missing
        logging.warning(
            "SEQUENCE_GAP player_id=%s previous=%s current=%s missing=%s total=%s",
            player_id, last_seq, seq, missing, counter["lost"]
        )

    player["last_seq"] = seq
    player["x"] = float(x)
    player["y"] = float(y)
    logging.info("STATE player_id=%s seq=%s x=%.2f y=%.2f", player_id, seq, x, y)
    broadcast_world(sock)


def print_stats():
    """Print packet statistics for all players."""
    print("\n--- Packet statistics ---")
    for player_id, counter in stats.items():
        line = (
            f"Player {player_id}: inferred_lost={counter['lost']}, "
            f"out_of_order={counter['out_of_order']}, "
            f"duplicates={counter['duplicates']}"
        )
        print(line)
        logging.info("STATS %s", line)
    print("-------------------------\n")


def main():
    """Create the UDP socket and process incoming client packets."""
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server.bind((HOST, PORT))
    except OSError as error:
        print(f"Could not bind to {HOST}:{PORT}: {error}")
        server.close()
        return

    print(f"UDP game server listening on {HOST}:{PORT}", flush=True)
    print(f"Packet-loss simulation: {DROP_RATE * 100:.0f}%", flush=True)
    print("Press Ctrl+C to stop the server.\n", flush=True)
    logging.info("SERVER STARTED host=%s port=%s drop_rate=%.2f", HOST, PORT, DROP_RATE)

    try:
        while True:
            data, address = server.recvfrom(BUFFER_SIZE)

            if DROP_RATE > 0 and random.random() < DROP_RATE:
                logging.warning("SIMULATED DROP: incoming packet from %s", address)
                continue

            message = protocol.decode_packet(data)
            if message is None:
                logging.warning("Invalid packet from %s", address)
                continue

            message_type = message["type"].upper()
            if message_type == protocol.JOIN:
                handle_join(server, address)
            elif message_type == protocol.STATE:
                handle_state(server, message, address)
            elif message_type == protocol.PING:
                send_packet(server, {"type": protocol.PONG, "server_time": time.time()}, address)
            elif message_type == protocol.LEAVE:
                player_id = find_player_by_address(address)
                if player_id is not None:
                    del players[player_id]
                    logging.info("PLAYER LEFT player_id=%s address=%s", player_id, address)
                    print(f"Player {player_id} left. Total players: {len(players)}", flush=True)
                    broadcast_world(server)
            elif message_type == protocol.STATS:
                print_stats()
                send_packet(server, {
                    "type": protocol.STATS_ACK,
                    "message": "Statistics printed in server terminal/log",
                }, address)
            else:
                send_packet(server, {"type": protocol.ERROR, "reason": "unknown_message_type"}, address)
                logging.warning("Unknown packet type=%s from %s", message_type, address)

    except KeyboardInterrupt:
        print("\nStopping UDP game server...", flush=True)
        logging.info("SERVER STOPPED")
        print_stats()
    finally:
        server.close()


if __name__ == "__main__":
    main()
