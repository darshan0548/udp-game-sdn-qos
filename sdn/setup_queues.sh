#queue 1 is game traffic (guaranteed 6 Mbps)

#queue 2 = everything else (max 4 Mbps when game is busy)

IFACE=${1:-s1-eth5}

sudo ovs-vsctl clear port $IFACE qos
sudo ovs-vsctl --all destroy qos
sudo ovs-vsctl --all destroy queue

sudo ovs-vsctl set port $IFACE qos=@newqos -- \
--id=@newqos create qos type=linux-htb \
other-config:max-rate=10000000 \
queues:1=@q1 queues:2=@q2 -- \
--id=@q1 create queue other-config:min-rate=6000000 other-config:max-rate=10000000 -- \
--id=@q2 create queue other-config:min-rate=1000000 other-config:max-rate=10000000

echo "Queues created on $IFACE"
