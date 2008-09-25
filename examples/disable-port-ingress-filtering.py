#!/usr/bin/snimpy

"""Disable port ingress filtering on Nortel switch (also known as
filter-unregistered-frames)."""

import sys

load("SNMPv2-MIB")
load("Q-BRIDGE-MIB")

s = M(host=sys.argv[1], community=sys.argv[2])

if "Ethernet Routing Switch 55" not in s.sysDescr:
    print "Not a 5510"
    sys.exit(1)

for id in s.dot1qPortIngressFiltering:
    if s.dot1qPortIngressFiltering[id]:
        print "Filtering on port %d of %s is not disabled, disable it." % (id, sys.argv[1])
        s.dot1qPortIngressFiltering[id] = False
