"""
run_experiment.py - run ONE scenario once inside Mininet and save the log.

Needs root:   sudo python run_experiment.py --scenario congested_qos --run 1 --duration 60

Scenarios
    baseline          no background traffic
    congested_noqos   heavy background traffic
    congested_qos     heavy background traffic
(QoS on/off is decided by WHICH CONTROLLER IS RUNNING - run_all.sh starts it.
 This script only builds the network, runs game + traffic, and collects the log.)

----------------------------------------------------------------------------
WHAT THIS FILE ASSUMES FROM TEAMMATES  (edit the CONFIG block if they differ)
  Student B: sdn/topology.py has   build_net() -> Mininet net   (already started with a
             remote controller, 10 Mbps bottleneck) with hosts named below.
  Student A: game/server.py and game/client.py accept the arguments in the
             command templates below, and the SERVER writes the CSV log
             (columns: player_id,seq,send_ts,recv_ts) to the path given by --log.
----------------------------------------------------------------------------
"""
import argparse
import os
import sys
import time

# ---------------------------- CONFIG ---------------------------------------
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "sdn"))            # so we can import B's topology.py
sys.path.insert(0, os.path.dirname(__file__))            # congestion.py

PLAYER_HOSTS = ["p1", "p2", "p3"]       # host names in B's topology
SERVER_HOST = "srv"
BG_HOST, SINK_HOST = "bg", "sink"
GAME_PORT = 5000
GAME_DIR = os.path.join(REPO, "game")

# {ip} {port} {log} {pid} {duration} are filled in below. Change to match A's CLI.
SERVER_CMD = "python3 {game}/server.py --port {port} --log {log} --duration {duration}"
CLIENT_CMD = "python3 {game}/client.py --server {ip} --port {port} --id {pid} --duration {duration}"

SCENARIO_LOAD = {"baseline": "none", "congested_noqos": "heavy", "congested_qos": "heavy"}
WARMUP, COOLDOWN = 3, 3                  # seconds
# ---------------------------------------------------------------------------

import congestion


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=SCENARIO_LOAD)
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--load", choices=list(congestion.INTENSITY_MBPS), help="override background load")
    args = ap.parse_args()

    load = args.load or SCENARIO_LOAD[args.scenario]
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs",
                                            f"{args.scenario}_run{args.run}.csv"))

    from topology import build_net            # Student B's file
    net = build_net()
    try:
        srv = net.get(SERVER_HOST)
        players = [net.get(h) for h in PLAYER_HOSTS]
        bg, sink = net.get(BG_HOST), net.get(SINK_HOST)

        print("[C] checking connectivity ...")
        if net.pingAll() > 0:
            sys.exit("[C] ping failed: check B's topology/controller before running experiments")

        run_time = args.duration + WARMUP + COOLDOWN
        print(f"[C] scenario={args.scenario} load={load} run={args.run} -> {log_path}")

        srv.cmd(SERVER_CMD.format(game=GAME_DIR, port=GAME_PORT, log=log_path, duration=run_time)
                + " > /tmp/server_out.log 2>&1 &")
        time.sleep(1)

        for i, p in enumerate(players, start=1):
            p.cmd(CLIENT_CMD.format(game=GAME_DIR, ip=srv.IP(), port=GAME_PORT, pid=i, duration=run_time)
                  + f" > /tmp/client{i}_out.log 2>&1 &")

        time.sleep(WARMUP)                     # let players join before the load starts
        congestion.start(bg, sink, load, args.duration)
        time.sleep(args.duration + COOLDOWN + 2)

        congestion.stop(bg, sink)
        srv.cmd("pkill -f server.py ; true")
        for p in players:
            p.cmd("pkill -f client.py ; true")
        time.sleep(1)
    finally:
        net.stop()

    if os.path.exists(log_path):
        print(f"[C] done: {log_path}")
    else:
        sys.exit("[C] no log file was written: check /tmp/server_out.log and A's --log option")


if __name__ == "__main__":
    main()
