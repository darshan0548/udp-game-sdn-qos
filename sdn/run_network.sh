#!/bin/bash
# Starts the project topology and sets up the bottleneck queues.
# Start the controller FIRST (./start_controller.sh basic|qos).
cd "$(dirname "$0")"

(
  until sudo ovs-vsctl list-ports s1 2>/dev/null | grep -q s1-eth5; do sleep 1; done
  sleep 1
  ./setup_queues.sh
) &

sudo python3 topology.py
