# SDN part (Student B)

## Start order (always this order)
0. Terminal 2: `sudo mn -c`
   (cleanup. ALWAYS do this BEFORE starting the controller)
1. Terminal 1: `./start_controller.sh qos`   (QoS ON)
   or          `./start_controller.sh basic` (QoS OFF)
   Wait until it prints `loading app ...` and sits there.
2. Terminal 2: `./run_network.sh`  -> opens the `mininet>` prompt
   (queues are created automatically a few seconds after it starts;
   press Enter if the prompt looks buried by the text)
3. Run everything else at the `mininet>` prompt.

To switch mode: type `exit` at `mininet>`, run `sudo mn -c`, Ctrl+C the
controller, then repeat from step 1.

## Hosts and IPs
| Host   | IP         | Role                         |
|--------|------------|------------------------------|
| p1     | 10.0.0.1   | player 1                     |
| p2     | 10.0.0.2   | player 2                     |
| p3     | 10.0.0.3   | player 3                     |
| server | 10.0.0.10  | game server                  |
| bgsrc  | 10.0.0.20  | background traffic sender    |
| bgsink | 10.0.0.21  | background traffic receiver  |

## Topology
p1, p2, p3, bgsrc -- s1 ==== s2 -- server, bgsink

The s1-s2 link (s1-eth5) is the 10 Mbps bottleneck with two queues.

## Rules for the game
- Game traffic MUST be UDP with destination port 5000. The QoS
  controller matches on that port to put it in the fast queue (queue 1).
- Run game programs inside Mininet, e.g. `server python3 server.py`
  and `p1 python3 client.py 10.0.0.10`.

## Background traffic (Student C)
    bgsink iperf -s -u > /dev/null &
    bgsrc iperf -c 10.0.0.21 -u -b 20M -t 60 > /dev/null &

## My results so far (iperf test, 1 Mbps game stream + 20 Mbps flood)
| Mode    | Jitter    | Loss |
|---------|-----------|------|
| QoS off | 16.021 ms | 0%   |
| QoS on  | 0.022 ms  | 0%   |

## Troubleshooting
- Never run `sudo mn -c` while the controller is running. It kills Ryu.
- Rule missing / `priority=100` not found: the controller was not
  `qos` when the topology started.
- "Unable to contact the remote controller": start the controller first.
- Dirty state: `sudo mn -c`, then restart in the order above.
- Check rules: `sudo ovs-ofctl -O OpenFlow13 dump-flows s1`
- Check queues are attached: `sudo ovs-vsctl get port s1-eth5 qos`
  (should print a UUID, not `[]`)
