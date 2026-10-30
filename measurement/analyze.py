"""
analyze.py - read every CSV in logs/, compute metrics, make graphs + summary table.

File naming (made by run_experiment.py / fake_data.py):
    logs/<scenario>_run<N>.csv      scenarios: baseline, congested_noqos, congested_qos

Outputs:
    graphs/latency_over_time.png    (run 1 of each scenario)
    graphs/latency_cdf.png          (all runs pooled per scenario)
    graphs/latency_boxplot.png
    graphs/jitter_bar.png           (mean over runs, error bar = std)
    graphs/loss_bar.png
    results/summary_per_run.csv
    results/summary_table.csv       (mean over runs, goes in the report)

Usage:
    python analyze.py
"""
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrics import load_log, summarize

LOG_DIR, GRAPH_DIR, RESULT_DIR = "logs", "graphs", "results"
ORDER = ["baseline", "congested_noqos", "congested_qos"]
LABELS = {"baseline": "Baseline\n(no load)",
          "congested_noqos": "Congested\n(QoS off)",
          "congested_qos": "Congested\n(QoS on)"}
COLORS = {"baseline": "tab:green", "congested_noqos": "tab:red", "congested_qos": "tab:blue"}


def load_all():
    runs = {}                       # scenario -> list of (run_no, dataframe)
    for path in sorted(glob.glob(os.path.join(LOG_DIR, "*_run*.csv"))):
        m = re.match(r"(.+)_run(\d+)\.csv$", os.path.basename(path))
        if not m:
            continue
        runs.setdefault(m.group(1), []).append((int(m.group(2)), load_log(path)))
    if not runs:
        raise SystemExit(f"No logs found in {LOG_DIR}/. Run fake_data.py or the experiments first.")
    return runs


def scenarios_present(runs):
    return [s for s in ORDER if s in runs] + [s for s in runs if s not in ORDER]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(GRAPH_DIR, name), dpi=150)
    plt.close(fig)
    print("saved", os.path.join(GRAPH_DIR, name))


def plot_latency_over_time(runs, scs):
    fig, axes = plt.subplots(len(scs), 1, figsize=(9, 2.6 * len(scs)), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, s in zip(axes, scs):
        df = runs[s][0][1].drop_duplicates(["player_id", "seq"])
        t0 = df["send_ts"].min()
        for pid, g in df.groupby("player_id"):
            ax.plot(g["send_ts"] - t0, g["latency_ms"], lw=0.6, alpha=0.8, label=f"player {pid}")
        ax.set_title(LABELS[s].replace("\n", " ") + f"  (run {runs[s][0][0]})", fontsize=10)
        ax.set_ylabel("latency (ms)")
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper right", fontsize=8, ncol=3)
    axes[-1].set_xlabel("time (s)")
    save(fig, "latency_over_time.png")


def plot_cdf(runs, scs):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for s in scs:
        lat = np.sort(pd.concat([d.drop_duplicates(["player_id", "seq"])["latency_ms"] for _, d in runs[s]]))
        ax.plot(lat, np.arange(1, len(lat) + 1) / len(lat), label=LABELS[s].replace("\n", " "),
                color=COLORS.get(s))
    ax.set_xlabel("latency (ms)")
    ax.set_ylabel("fraction of packets")
    ax.set_title("Latency CDF (all runs pooled)")
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, "latency_cdf.png")


def plot_box(runs, scs):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    data = [pd.concat([d.drop_duplicates(["player_id", "seq"])["latency_ms"] for _, d in runs[s]]) for s in scs]
    ax.boxplot(data, tick_labels=[LABELS[s] for s in scs], showfliers=False)
    ax.set_ylabel("latency (ms)")
    ax.set_title("Latency distribution per scenario")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "latency_boxplot.png")


def plot_bar(summary, scs, col, ylabel, title, fname):
    g = summary.groupby("scenario")[col]
    means, stds = g.mean().reindex(scs), g.std().reindex(scs).fillna(0)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar([LABELS[s] for s in scs], means, yerr=stds, capsize=5,
                  color=[COLORS.get(s, "gray") for s in scs])
    for b, v in zip(bars, means):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    save(fig, fname)


def main():
    os.makedirs(GRAPH_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    runs = load_all()
    scs = scenarios_present(runs)

    rows = []
    for s in scs:
        for n, df in runs[s]:
            rows.append({"scenario": s, "run": n, **summarize(df)})
    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(RESULT_DIR, "summary_per_run.csv"), index=False)

    cols = ["latency_mean_ms", "latency_p95_ms", "latency_max_ms", "jitter_ms", "jitter_rfc3550_ms", "loss_percent"]
    table = summary.groupby("scenario")[cols].mean().reindex(scs).round(2)
    table.insert(0, "runs", summary.groupby("scenario").size().reindex(scs))
    table.to_csv(os.path.join(RESULT_DIR, "summary_table.csv"))
    print("\nSummary (mean over runs):\n", table.to_string(), "\n")

    plot_latency_over_time(runs, scs)
    plot_cdf(runs, scs)
    plot_box(runs, scs)
    plot_bar(summary, scs, "jitter_ms", "jitter (ms)", "Jitter per scenario (mean of runs, bar = std)", "jitter_bar.png")
    plot_bar(summary, scs, "loss_percent", "packet loss (%)", "Packet loss per scenario", "loss_bar.png")


if __name__ == "__main__":
    main()
