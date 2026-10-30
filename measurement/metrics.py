"""
metrics.py - pure functions that turn a game log into latency, jitter and loss.
No networking in here, so it is easy to test.

Definitions (copy these into the report):
    latency      = recv_ts - send_ts                       (reported in ms)
    jitter       = mean(|latency[i] - latency[i-1]|)       per player, packets in seq order
    jitter_rfc   = RFC 3550 running estimate J += (|D| - J)/16   (extra, optional)
    packet loss% = (expected - unique received) / expected * 100
                   expected = max_seq - min_seq + 1 per player
                   (note: lost packets at the very end of a run can't be seen)
    duplicates   = rows whose (player_id, seq) was already received
    out-of-order = packets that arrive after a packet with a higher seq

CSV columns: player_id, seq, send_ts, recv_ts

Usage:
    python metrics.py logs/baseline_run1.csv
"""
import sys
import numpy as np
import pandas as pd


def load_log(path):
    df = pd.read_csv(path)
    missing = {"player_id", "seq", "send_ts", "recv_ts"} - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    df["latency_ms"] = (df["recv_ts"] - df["send_ts"]) * 1000.0
    return df


def count_duplicates(df):
    return int(df.duplicated(subset=["player_id", "seq"]).sum())


def count_out_of_order(df):
    """Per player, in arrival order: how many packets arrived with a seq lower than one already seen."""
    total = 0
    for _, g in df.drop_duplicates(["player_id", "seq"]).sort_values("recv_ts").groupby("player_id"):
        total += int((g["seq"] < g["seq"].cummax().shift(fill_value=-1)).sum())
    return total


def loss_stats(df):
    """Returns (expected, received_unique, lost, loss_percent) summed over all players."""
    expected = received = 0
    for _, g in df.groupby("player_id"):
        u = g.drop_duplicates("seq")
        expected += int(u["seq"].max() - u["seq"].min() + 1)
        received += len(u)
    lost = expected - received
    pct = 100.0 * lost / expected if expected else 0.0
    return expected, received, lost, pct


def _per_player_latency(df):
    """Yield latency arrays (ms) per player, duplicates removed, in seq order."""
    u = df.drop_duplicates(["player_id", "seq"]).sort_values(["player_id", "seq"])
    for _, g in u.groupby("player_id"):
        yield g["latency_ms"].to_numpy()


def jitter_simple(df):
    """Main jitter metric: mean absolute difference of consecutive latencies (ms)."""
    diffs = [np.abs(np.diff(lat)) for lat in _per_player_latency(df) if len(lat) > 1]
    return float(np.concatenate(diffs).mean()) if diffs else 0.0


def jitter_rfc3550(df):
    """Optional extra: RFC 3550 smoothed jitter estimate (ms), averaged over players."""
    finals = []
    for lat in _per_player_latency(df):
        j = 0.0
        for d in np.abs(np.diff(lat)):
            j += (d - j) / 16.0
        finals.append(j)
    return float(np.mean(finals)) if finals else 0.0


def summarize(df):
    """One row of headline numbers for a whole run."""
    expected, received, lost, pct = loss_stats(df)
    lat = df.drop_duplicates(["player_id", "seq"])["latency_ms"]
    return {
        "packets_received": received,
        "packets_expected": expected,
        "packets_lost": lost,
        "loss_percent": round(pct, 3),
        "duplicates": count_duplicates(df),
        "out_of_order": count_out_of_order(df),
        "latency_mean_ms": round(lat.mean(), 3),
        "latency_p95_ms": round(lat.quantile(0.95), 3),
        "latency_max_ms": round(lat.max(), 3),
        "jitter_ms": round(jitter_simple(df), 3),
        "jitter_rfc3550_ms": round(jitter_rfc3550(df), 3),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python metrics.py <logfile.csv>")
    for k, v in summarize(load_log(sys.argv[1])).items():
        print(f"{k:20s} {v}")
