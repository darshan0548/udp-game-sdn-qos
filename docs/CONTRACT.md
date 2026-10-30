# Shared Contract

Status: **PROPOSED**. Each owner confirms their section with a comment or approval on the PR.
Anything marked `TBD` must be filled in by the named owner.

## 1. Network and ports

| Item | Value |
|---|---|
| Game protocol | UDP, server port **5000** (this is how the SDN recognizes game traffic) |
| Background traffic | iperf UDP on port **5001** (never 5000) |
| Bottleneck | link s1–s2 limited to **10 Mbps** |
| Update rate | 30 state updates per second per player |
| Players | at least 3 |

## 2. Mininet host names (owner: B)

`p1`, `p2`, `p3` (players), `srv` (game server), `bg` (traffic generator), `sink` (iperf receiver).
IP addresses: `TBD (B)`.

B provides `sdn/topology.py` exposing `build_net()` that returns a started Mininet
object connected to a remote controller.

## 3. Controllers (owner: B)

- `sdn/controller_basic.py`: plain learning switch (QoS **off**)
- `sdn/controller_qos.py`: prioritizes UDP dst/src port 5000 (QoS **on**)

Both are run with `ryu-manager <file>`.

## 4. Packet format (owner: A)

Binary, big-endian, built with Python `struct`, defined once in `game/protocol.py`.

| Field | Size | Notes |
|---|---|---|
| type | 1 byte | JOIN, JOIN_ACK, STATE, WORLD, ACK |
| player_id | 2 bytes | assigned by the server on JOIN |
| seq | 4 bytes | per-sender, starts at 0, +1 per packet |
| send_timestamp | 8 bytes | `time.time()` as double, seconds |
| payload | variable | x, y, health, ... (A decides) |

## 5. Command-line options (owner: A)

```
python3 game/server.py --port 5000 --log <file.csv> --duration <seconds>
python3 game/client.py --server <ip> --port 5000 --id <n> --duration <seconds>
```

## 6. Log file (owner: A writes, C reads)

The **server** writes one CSV row for every game packet it receives:

```
player_id,seq,send_ts,recv_ts
```

- timestamps in seconds (`time.time()`), `recv_ts` taken the moment the packet arrives
- one header row, no extra columns
- duplicates are logged too (C counts them); lost packets simply do not appear

Latency is `recv_ts - send_ts`. This is a valid one-way delay because every Mininet
host shares the same machine clock.

## 7. Metric definitions (owner: C)

| Metric | Definition |
|---|---|
| Latency | `recv_ts - send_ts`, in ms |
| Jitter | mean of `|latency[i] - latency[i-1]|` per player, packets in seq order |
| Loss % | `(expected - received) / expected`, expected = `max_seq - min_seq + 1` per player |

RFC 3550 jitter is also reported as a secondary column.
