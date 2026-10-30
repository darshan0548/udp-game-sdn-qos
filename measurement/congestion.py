"""
congestion.py - start iperf background traffic inside Mininet.

Used by run_experiment.py, but can also be tested alone from the Mininet CLI:
    mininet> py import congestion; congestion.start(net.get('bg'), net.get('sink'), 'heavy', 60)

Intensity is a fraction of the 10 Mbps bottleneck link.
"""
import time

BOTTLENECK_MBPS = 10
INTENSITY_MBPS = {"none": 0, "light": 3, "medium": 6, "heavy": 9}
IPERF_PORT = 5001          # must NOT be 5000 (that is the game port, which QoS prioritizes)


def start(bg_host, sink_host, intensity, duration):
    """Start an iperf UDP flood bg -> sink. Returns immediately; traffic runs for `duration` s."""
    mbps = INTENSITY_MBPS[intensity]
    if mbps == 0:
        return
    sink_host.cmd(f"iperf -u -s -p {IPERF_PORT} > /tmp/iperf_server.log 2>&1 &")
    time.sleep(1)
    bg_host.cmd(f"iperf -u -c {sink_host.IP()} -p {IPERF_PORT} -b {mbps}M -t {duration} "
                f"> /tmp/iperf_client.log 2>&1 &")


def stop(bg_host, sink_host):
    bg_host.cmd("pkill -f 'iperf' ; true")
    sink_host.cmd("pkill -f 'iperf' ; true")
