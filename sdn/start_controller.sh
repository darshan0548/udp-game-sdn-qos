#!/bin/bash
# Usage: ./start_controller.sh basic   (QoS off)
#        ./start_controller.sh qos     (QoS on)
cd "$(dirname "$0")"
source ~/ryu-env/bin/activate

case "$1" in
  basic) ryu-manager ryu.app.simple_switch_13 ;;
  qos)   ryu-manager controller_qos.py ;;
  *)     echo "Usage: $0 basic|qos"; exit 1 ;;
esac
