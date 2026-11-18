import argparse
import csv
import os
import socket
import sys
import threading
import time
import _thread

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))

parser = argparse.ArgumentParser()
parser.add_argument("role", choices=["server", "client"])
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--server", default="127.0.0.1")
parser.add_argument("--port", type=int, default=5000)
parser.add_argument("--log", default="game_log.csv")
parser.add_argument("--duration", type=float, default=0)
args, rest = parser.parse_known_args()
sys.argv = [sys.argv[0]] + rest


def stop():
    _thread.interrupt_main()
    if args.role == "server":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"", ("127.0.0.1", args.port))


if args.duration > 0:
    threading.Timer(args.duration, stop).start()

if args.role == "server":
    import server
    server.HOST = args.host
    server.PORT = args.port
    f = open(args.log, "w", newline="")
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["player_id", "seq", "send_ts", "recv_ts"])
    old_handle_state = server.handle_state

    def new_handle_state(sock, message, address):
        recv_ts = time.time()
        pid = server.find_player_by_address(address)
        if pid is not None and "seq" in message and "send_ts" in message:
            w.writerow([pid, message["seq"], message["send_ts"], recv_ts])
            f.flush()
        old_handle_state(sock, message, address)

    server.handle_state = new_handle_state
    try:
        server.main()
    finally:
        f.close()
else:
    import client
    import protocol
    client.SERVER_ADDRESS = (args.server, args.port)
    old_encode = protocol.encode_packet

    def new_encode(message):
        if message.get("type") == protocol.STATE:
            message = dict(message)
            message["send_ts"] = time.time()
        return old_encode(message)

    protocol.encode_packet = new_encode
    old_bind = socket.socket.bind

    def new_bind(sock, address):
        return old_bind(sock, ("0.0.0.0", address[1]))

    socket.socket.bind = new_bind
    client.main()
