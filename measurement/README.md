# measurement (Student C)

| File | What it does |
|---|---|
| game_runner.py | runs the game (server or client) and writes the log file |
| run_experiment.py | runs one scenario once inside Mininet |
| run_all.sh | runs all scenarios, several times, then analyze.py |
| metrics.py | latency, jitter and loss from one log file |
| analyze.py | graphs and summary table from all logs |

Scenarios: baseline (no load), noqos (load, QoS off), qos (load, QoS on).

Run everything (Ubuntu, needs Mininet, Open vSwitch, Ryu, iperf):

    sudo ./run_all.sh 3 60

Check one log:

    python3 metrics.py logs/noqos_1.csv

Log columns: player_id, seq, send_ts, recv_ts
