#!/bin/bash
runs=${1:-3}
duration=${2:-60}
cd "$(dirname "$0")"

run_scenario() {
  scenario=$1
  controller=$2
  for n in $(seq 1 $runs); do
    echo "== $scenario run $n =="
    sudo mn -c > /dev/null 2>&1
    ${RYU:-ryu-manager} $controller > /tmp/ryu_$scenario.txt 2>&1 &
    ryu_pid=$!
    sleep 5
    sudo python3 run_experiment.py $scenario $n $duration
    kill $ryu_pid
    wait $ryu_pid 2>/dev/null
  done
}

run_scenario baseline ryu.app.simple_switch_13
run_scenario noqos ryu.app.simple_switch_13
run_scenario qos ../sdn/controller_qos.py

python3 analyze.py
