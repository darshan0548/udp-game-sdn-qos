"""
fake_data.py - generate fake game logs so metrics.py / analyze.py can be
built and tested before Student A and B have anything running.

Log format (CSV, one row per packet RECEIVED):
    player_id, seq, send_ts, recv_ts      (timestamps in seconds)

Lost packets simply do not appear in the file (the receiver never saw them).

Usage:
    python fake_data.py                 # makes 3 scenarios x 3 runs in logs/
    python fake_data.py --duration 30   # shorter runs
"""
import argparse
import csv
import os
import random

RATE = 30          # updates per second per player
PLAYERS = [1, 2, 3]

# Scenario behaviour: base delay, random noise, congestion spikes, loss, etc. (delays in seconds)
SCENARIOS = {
    "baseline":         dict(base=0.005, noise=0.0005, spike=0.0,   loss=0.002),
    "congested_noqos":  dict(base=0.005, noise=0.002,  spike=0.150, loss=0.08),
    "congested_qos":    dict(base=0.006, noise=0.001,  spike=0.008, loss=0.005),
}


def queue_delay(t, spike):
    """Sawtooth: queue slowly fills then drains, like a congested buffer."""
    if spike == 0:
        return 0.0
    period = 4.0
    phase = (t % period) / period
    return spike * phase * random.uniform(0.7, 1.0)


def generate(scenario, duration, seed):
    random.seed(seed)
    p = SCENARIOS[scenario]
    rows = []
    for pid in PLAYERS:
        start = 1000.0 + random.uniform(0, 0.03)
        for seq in range(int(duration * RATE)):
            send_ts = start + seq / RATE
            if random.random() < p["loss"]:
                continue                                   # packet lost
            delay = p["base"] + abs(random.gauss(0, p["noise"]))
            delay += queue_delay(send_ts - start, p["spike"])
            recv_ts = send_ts + delay
            rows.append((pid, seq, send_ts, recv_ts))
            if random.random() < 0.002:                    # rare duplicate
                rows.append((pid, seq, send_ts, recv_ts + 0.001))
    rows.sort(key=lambda r: r[3])                          # arrival order
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="logs")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    for scenario in SCENARIOS:
        for run in range(1, args.runs + 1):
            rows = generate(scenario, args.duration, seed=hash((scenario, run)) % 10**6)
            path = os.path.join(args.out, f"{scenario}_run{run}.csv")
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["player_id", "seq", "send_ts", "recv_ts"])
                w.writerows(rows)
            print(f"wrote {path} ({len(rows)} packets)")


if __name__ == "__main__":
    main()
