import glob
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metrics import load, summary

names = ["baseline", "noqos", "qos"]
labels = {"baseline": "No load", "noqos": "Load, QoS off", "qos": "Load, QoS on"}

os.makedirs("graphs", exist_ok=True)
os.makedirs("results", exist_ok=True)

logs = {}
for name in names:
    files = sorted(glob.glob("logs/" + name + "_*.csv"))
    if len(files) > 0:
        logs[name] = [load(f) for f in files]

if len(logs) == 0:
    print("no log files found in logs/")
    raise SystemExit

rows = []
for name in logs:
    for df in logs[name]:
        row = summary(df)
        row["scenario"] = name
        rows.append(row)

table = pd.DataFrame(rows)
average = table.groupby("scenario").mean().reindex(list(logs.keys())).round(3)
average.to_csv("results/summary.csv")
print(average)

fig, axes = plt.subplots(len(logs), 1, figsize=(9, 3 * len(logs)), sharex=True, sharey=True, squeeze=False)
i = 0
for name in logs:
    df = logs[name][0]
    start = df["send_ts"].min()
    for pid in df["player_id"].unique():
        one = df[df["player_id"] == pid]
        axes[i][0].plot(one["send_ts"] - start, one["latency"], label="player " + str(pid))
    axes[i][0].set_title(labels[name])
    axes[i][0].set_ylabel("latency (ms)")
    i = i + 1
axes[0][0].legend()
axes[-1][0].set_xlabel("time (s)")
plt.tight_layout()
plt.savefig("graphs/latency_over_time.png")
plt.close()

data = []
for name in logs:
    data.append(pd.concat([df["latency"] for df in logs[name]]))
plt.boxplot(data, showfliers=False)
plt.xticks(range(1, len(data) + 1), [labels[n] for n in logs])
plt.ylabel("latency (ms)")
plt.title("Latency per scenario")
plt.savefig("graphs/latency_boxplot.png")
plt.close()


def bar(column, ylabel, filename):
    plt.bar([labels[n] for n in average.index], average[column])
    plt.ylabel(ylabel)
    plt.title(ylabel + " per scenario")
    plt.savefig("graphs/" + filename)
    plt.close()


bar("jitter", "jitter (ms)", "jitter.png")
bar("loss_percent", "packet loss (%)", "loss.png")
