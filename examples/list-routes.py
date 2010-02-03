#!/usr/bin/snimpy

from socket import inet_ntoa

load("IP-FORWARD-MIB")
m=M()

print "Using IP-FORWARD-MIB::ipCidrRouteTable..."
routes = m.ipCidrRouteNextHop
for x in routes:
    net, netmask, tos, src = x
    print "%15s/%-15s via %-15s src %-15s" % (net, netmask, routes[x], src)

print

print "Using IP-FORWARD-MIB::inetCidrRouteTable..."
routes = m.inetCidrRouteIfIndex
for x in routes:
    dsttype, dst, prefix, oid, nhtype, nh = x
    if dsttype != "ipv4" or nhtype != "ipv4":
        print "Non-IPv4 route"
        continue
    print "%15s/%-2d via %-15s" % (inet_ntoa(dst), prefix, inet_ntoa(nh))
