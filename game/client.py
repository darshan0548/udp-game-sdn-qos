"""Interactive UDP game client with JOIN retries and random-walk movement."""
import socket
import random
import time
import argparse

import protocol

SERVER_ADDRESS = ("127.0.0.1", 5000)
BUFFER_SIZE = protocol.BUFFER_SIZE
JOIN_TIMEOUT = 1.0
JOIN_RETRIES = 5
STATE_RATE = 10  # Position updates per second


def receive_message(sock, timeout):
    """Receive and decode one packet; return None if the timeout expires."""
    sock.settimeout(timeout)
    try:
        data, address = sock.recvfrom(BUFFER_SIZE)
    except socket.timeout:
        return None

    message = protocol.decode_packet(data)
    if message is None:
        print(f"Received an invalid packet from {address}")
        return None
    return message


def join_server(sock):
    """Retry JOIN until JOIN_ACK arrives or the retry limit is reached."""
    for attempt in range(1, JOIN_RETRIES + 1):
        sock.sendto(
            protocol.encode_packet({"type": protocol.JOIN}),
            SERVER_ADDRESS,
        )
        print(f"JOIN sent (attempt {attempt}/{JOIN_RETRIES})")

        deadline = time.monotonic() + JOIN_TIMEOUT
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            message = receive_message(sock, max(0.01, remaining))

            if message is None:
                continue

            if message.get("type") == protocol.JOIN_ACK:
                player_id = message.get("player_id")
                if isinstance(player_id, int):
                    print(f"Joined server as player {player_id}")
                    return player_id

            elif message.get("type") == protocol.JOIN_REJECT:
                raise RuntimeError(
                    f"Join rejected: {message.get('reason', 'unknown reason')}"
                )

            # Ignore WORLD or unrelated packets while waiting for JOIN_ACK.

    raise TimeoutError(
        "No JOIN_ACK received. Check that the server is running and that "
        "the packet-loss setting is not too high."
    )


def main():
    parser = argparse.ArgumentParser(description="UDP localhost game client")
    parser.add_argument(
        "--name",
        default="Player",
        help="Name shown in this client's terminal",
    )
    parser.add_argument(
        "--drop",
        type=float,
        default=0.0,
        help="Client-side simulated packet drop rate, e.g. 0.15 for 15%%",
    )
    args = parser.parse_args()

    drop_rate = max(0.0, min(1.0, args.drop))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # The operating system chooses a unique local port for each client.
    sock.bind(("127.0.0.1", 0))

    try:
        player_id = join_server(sock)
        x, y = 0.0, 0.0
        seq = 0
        update_interval = 1.0 / STATE_RATE
        next_update = time.monotonic()

        print(f"{args.name} (player {player_id}) is active.")
        print("Random-walk movement is running. Press Ctrl+C to leave.\n")

        while True:
            now = time.monotonic()

            # Send the newest position at a fixed rate.
            if now >= next_update:
                x += random.choice((-1, 0, 1))
                y += random.choice((-1, 0, 1))

                message = {
                    "type": protocol.STATE,
                    "seq": seq,
                    "x": x,
                    "y": y,
                }
                seq += 1

                if drop_rate > 0 and random.random() < drop_rate:
                    print("SIMULATED DROP: outgoing STATE packet")
                else:
                    sock.sendto(
                        protocol.encode_packet(message),
                        SERVER_ADDRESS,
                    )

                next_update += update_interval
                # Avoid sending a burst of old updates after a pause.
                if next_update < now - update_interval:
                    next_update = now + update_interval

            # Receive server broadcasts and display the latest world state.
            try:
                sock.settimeout(0.01)
                data, address = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            message = protocol.decode_packet(data)
            if message is None:
                continue

            message_type = message.get("type")

            if message_type == protocol.WORLD:
                world_players = message.get("players", [])
                positions = []

                for player in world_players:
                    if not isinstance(player, dict):
                        continue
                    px = player.get("x")
                    py = player.get("y")
                    if isinstance(px, (int, float)) and isinstance(py, (int, float)):
                        positions.append(
                            f"P{player.get('player_id')}:({px:.1f},{py:.1f})"
                        )

                print(f"WORLD | {', '.join(positions)}")

            elif message_type == protocol.ERROR:
                print(f"Server error: {message.get('reason', 'unknown error')}")

    except KeyboardInterrupt:
        print("\nLeaving the game...")
    except (TimeoutError, RuntimeError) as error:
        print(error)
    finally:
        # Tell the server this player is leaving, then close the socket.
        try:
            sock.sendto(
                protocol.encode_packet({"type": protocol.LEAVE}),
                SERVER_ADDRESS,
            )
        except OSError:
            pass
        sock.close()


if __name__ == "__main__":
    main()
