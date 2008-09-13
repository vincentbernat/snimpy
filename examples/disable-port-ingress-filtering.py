#!/usr/bin/snimpy

"""Disable port ingress filtering on Nortel switch (also known as
filter-unregistered-frames)."""

import sys

load("Q-BRIDGE-MIB")

s = S(host=sys.argv[1], community=sys.argv[2])

if "Ethernet Routing Switch 5510" not in s.sysDescr:
    print "Not a 5510"
    sys.exit(1)

for id in s.dot1qPortIngressFiltering:
    if s.dot1qPortIngressFiltering[id] != "false":
        print "Filtering on port %d of %s is not disabled, disable it." % (id, sys.argv[1])
        s.dot1qPortIngressFiltering[id] = "false"
