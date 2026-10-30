# measurement/ (Student C)

| File | What it does |
|---|---|
| metrics.py | latency, jitter, loss from a log CSV |
| analyze.py | all logs -> graphs/ + results/summary_table.csv |
| fake_data.py | fake logs to test without A and B |
| congestion.py | iperf background traffic (light/medium/heavy) |
| run_experiment.py | one scenario, one run, inside Mininet |
| run_all.sh | every scenario x N runs, then analyze |
| test_metrics.py | hand-checked test of the maths |

Quick start (no network needed): `python fake_data.py && python analyze.py`
Real experiments: `sudo ./run_all.sh 3 60`

Log format A must write: `player_id,seq,send_ts,recv_ts` (seconds, one row per packet received).
Delete fake logs in logs/ before real runs!
