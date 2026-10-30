# UDP Game Communication with SDN Traffic Prioritization

Computer Networks course project. A simplified multiplayer game where players exchange
real-time state over UDP, running on an emulated network (Mininet + Ryu/OpenFlow) that
prioritizes game traffic when the link is congested. We measure latency, jitter and
packet loss with and without prioritization.

## How it works

```
 p1 ─┐                                    ┌─ srv  (game server, UDP 5000)
 p2 ─┼─ s1 ══ 10 Mbps bottleneck ══ s2 ───┤
 p3 ─┤                                    └─ sink (iperf receiver)
 bg ─┘  (background traffic generator)
```

| Layer | What it does | Folder |
|---|---|---|
| Game | UDP server/clients, registration, sequence numbers, loss handling | `game/` |
| SDN | Mininet topology, Ryu controllers, QoS queues, `--qos on/off` | `sdn/` |
| Measurement | Latency, jitter, loss, congestion tests, experiments, graphs | `measurement/` |

## Team

| Member | Role | Folder |
|---|---|---|
| Student A | Game application | `game/` |
| Student B | SDN / network | `sdn/` |
| Student C | Measurement and testing | `measurement/` |

*(Replace with real names.)*

## Shared agreements

Everything the three parts must agree on (packet format, ports, log format, host names,
command-line options) lives in [`docs/CONTRACT.md`](docs/CONTRACT.md). Change it only
through a pull request that all three of us approve.

## Requirements

- Ubuntu (VM, WSL2 or lab machine) for Mininet, Open vSwitch, Ryu, iperf
- Python 3.9+ with `pandas`, `matplotlib`, `numpy` for analysis

## Quick start

```bash
# Analysis only (any OS, no network needed): uses fake data
cd measurement
python fake_data.py && python analyze.py

# Full experiment suite (Ubuntu, root): 3 runs of 60 s per scenario
cd measurement
sudo ./run_all.sh 3 60
```

Experiment scenarios: `baseline` (no load), `congested_noqos` (heavy load, QoS off),
`congested_qos` (heavy load, QoS on). Results appear in `measurement/graphs/` and
`measurement/results/`.

## Repository layout

```
game/          Student A: server.py, client.py, protocol.py
sdn/           Student B: topology.py, controller_basic.py, controller_qos.py, queue setup
measurement/   Student C: metrics, congestion, experiment runner, analysis
report/        Final report and figures
docs/          Shared contract and notes
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the Git workflow.
