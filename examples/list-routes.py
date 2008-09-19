#!/usr/bin/snimpy

load("IP-FORWARD-MIB")
m=M()

routes = m.ipCidrRouteNextHop
for x in routes:
    net, netmask, tos, src = x
    print "%15s/%-15s via %-15s src %-15s" % (net, netmask, routes[x], src)
