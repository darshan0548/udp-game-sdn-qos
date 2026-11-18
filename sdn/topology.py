#!/usr/bin/env python3
"""Project topology: 3 players + banckground sender on s1, game server + background sink on s2, s1-s2 is the future bottleneck."""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def build():
	net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, autoSetMacs=True)
	net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

	s1 = net.addSwitch('s1', protocols='OpenFlow13')
	s2 = net.addSwitch('s2', protocols='OpenFlow13')

	p1 = net.addHost('p1', ip='10.0.0.1/24')
	p2 = net.addHost('p2', ip='10.0.0.2/24')
	p3 = net.addHost('p3', ip='10.0.0.3/24')
	bgsrc = net.addHost('bgsrc', ip='10.0.0.20/24')
	server = net.addHost('server', ip='10.0.0.10/24')
	bgsink = net.addHost('bgsink', ip='10.0.0.21/24')

	# s1 side
	net.addLink(p1,s1)
	net.addLink(p2,s1)
	net.addLink(p3,s1)
	net.addLink(bgsrc,s1)

	# s2 side
	net.addLink(server,s2)
	net.addLink(bgsink,s2)

	# future bottleneck link
	net.addLink(s1,s2)

	return net

if __name__ == '__main__':
	setLogLevel('info')
	net = build()
	net.start()
	CLI(net)
	net.stop()
