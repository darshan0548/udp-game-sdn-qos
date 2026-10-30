#!/bin/bash
# run_all.sh - run every scenario several times, then analyze.
# Usage:  sudo ./run_all.sh [RUNS] [DURATION]      e.g.  sudo ./run_all.sh 3 60
#
# Assumes Student B's controllers are at ../sdn/controller_basic.py and ../sdn/controller_qos.py
# (run with ryu-manager). Edit the two lines below if the names differ.

RUNS=${1:-3}
DURATION=${2:-60}
HERE="$(cd "$(dirname "$0")" && pwd)"
CTRL_BASIC="$HERE/../sdn/controller_basic.py"
CTRL_QOS="$HERE/../sdn/controller_qos.py"

run_scenario () {            # $1 = scenario name, $2 = controller file
  for n in $(seq 1 "$RUNS"); do
    echo "=== $1 run $n/$RUNS ==="
    mn -c > /dev/null 2>&1                          # clean leftovers from the last run
    ryu-manager "$2" > "/tmp/ryu_$1.log" 2>&1 &
    RYU_PID=$!
    sleep 4                                          # give the controller time to start
    python3 "$HERE/run_experiment.py" --scenario "$1" --run "$n" --duration "$DURATION"
    kill $RYU_PID 2>/dev/null; wait $RYU_PID 2>/dev/null
  done
}

run_scenario baseline         "$CTRL_BASIC"
run_scenario congested_noqos  "$CTRL_BASIC"
run_scenario congested_qos    "$CTRL_QOS"

cd "$HERE" && python3 analyze.py
echo "All done. Graphs in measurement/graphs, tables in measurement/results."
