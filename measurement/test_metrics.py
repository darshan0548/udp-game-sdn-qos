"""Hand-checkable test: run  python test_metrics.py"""
import pandas as pd
from metrics import *

# 1 player, seq 0..5 sent; seq 3 lost; seq 2 duplicated; latencies 10,20,15,(lost),25,30 ms
rows = [(1,0,0.00,0.010),(1,1,0.03,0.050),(1,2,0.06,0.075),(1,2,0.06,0.076),
        (1,4,0.12,0.145),(1,5,0.15,0.180)]
df = pd.DataFrame(rows, columns=["player_id","seq","send_ts","recv_ts"])
df["latency_ms"] = (df.recv_ts - df.send_ts)*1000
# seq order latencies: 10,20,15,25,30 -> diffs 10,5,10,5 -> mean 7.5
assert abs(jitter_simple(df) - 7.5) < 1e-6, jitter_simple(df)
assert loss_stats(df) == (6, 5, 1, 100/6), loss_stats(df)
assert count_duplicates(df) == 1
assert count_out_of_order(df) == 0
print("all tests passed")
