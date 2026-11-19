import argparse
import os
import subprocess
import sys
import time

here = os.path.dirname(os.path.abspath(__file__))
sdn_folder = os.path.join(here, "..", "sdn")
sys.path.insert(0, sdn_folder)
from topology import build

parser = argparse.ArgumentParser()
parser.add_argument("scenario", choices=["baseline", "noqos", "qos"])
parser.add_argument("run", type=int)
parser.add_argument("duration", type=int)
args = parser.parse_args()

runner = os.path.join(here, "game_runner.py")
name = args.scenario + "_" + str(args.run)
log_file = os.path.join(here, "logs", name + ".csv")
flows_file = os.path.join(here, "results", "flows_" + name + ".txt")
os.makedirs(os.path.join(here, "logs"), exist_ok=True)
os.makedirs(os.path.join(here, "results"), exist_ok=True)

net = build()
net.start()
if not net.waitConnected(timeout=20):
    print("switches did not connect to the controller")
    net.stop()
    sys.exit(1)

subprocess.run(["bash", os.path.join(sdn_folder, "setup_queues.sh"), "s1-eth5"])
time.sleep(2)

server = net.get("server")
players = [net.get("p1"), net.get("p2"), net.get("p3")]
bgsrc = net.get("bgsrc")
bgsink = net.get("bgsink")

net.pingAll()

server.cmd("cd /tmp && python3 %s server --port 5000 --log %s --duration %d > /tmp/server_out.txt 2>&1 &"
           % (runner, log_file, args.duration + 10))
time.sleep(1)

number = 1
for p in players:
    p.cmd("cd /tmp && python3 %s client --server 10.0.0.10 --name P%d --duration %d > /tmp/client%d_out.txt 2>&1 &"
          % (runner, number, args.duration + 5, number))
    number = number + 1
time.sleep(3)

if args.scenario != "baseline":
    bgsink.cmd("iperf -s -u > /dev/null 2>&1 &")
    bgsrc.cmd("iperf -c 10.0.0.21 -u -b 20M -t %d > /dev/null 2>&1 &" % args.duration)

time.sleep(args.duration + 8)

flows = subprocess.run(["ovs-ofctl", "-O", "OpenFlow13", "dump-flows", "s1"], capture_output=True, text=True)
open(flows_file, "w").write(flows.stdout)

subprocess.run(["pkill", "-f", "iperf"])
subprocess.run(["pkill", "-f", "game_runner.py"])
net.stop()
print("saved", log_file)
