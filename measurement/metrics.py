import sys
import pandas as pd


def load(path):
    df = pd.read_csv(path)
    df["latency"] = (df["recv_ts"] - df["send_ts"]) * 1000
    return df


def get_jitter(df):
    df = df.drop_duplicates(["player_id", "seq"])
    df = df.sort_values(["player_id", "seq"])
    diffs = []
    for pid in df["player_id"].unique():
        lat = df[df["player_id"] == pid]["latency"].tolist()
        for i in range(1, len(lat)):
            diffs.append(abs(lat[i] - lat[i - 1]))
    if len(diffs) == 0:
        return 0
    return sum(diffs) / len(diffs)


def get_loss(df):
    expected = 0
    received = 0
    for pid in df["player_id"].unique():
        one = df[df["player_id"] == pid].drop_duplicates("seq")
        expected = expected + one["seq"].max() - one["seq"].min() + 1
        received = received + len(one)
    lost = expected - received
    return lost, 100 * lost / expected


def summary(df):
    lost, loss_percent = get_loss(df)
    lat = df.drop_duplicates(["player_id", "seq"])["latency"]
    result = {}
    result["latency_avg"] = lat.mean()
    result["latency_p95"] = lat.quantile(0.95)
    result["latency_max"] = lat.max()
    result["jitter"] = get_jitter(df)
    result["lost"] = lost
    result["loss_percent"] = loss_percent
    result["duplicates"] = df.duplicated(["player_id", "seq"]).sum()
    return result


if __name__ == "__main__":
    df = load(sys.argv[1])
    for key, value in summary(df).items():
        print(key, round(value, 3))
