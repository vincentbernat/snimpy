#!/usr/bin/snimpy

"""Disable port ingress filtering on Nortel switch (also known as
filter-unregistered-frames)."""

import sys

load("Q-BRIDGE-MIB")

S.host=sys.argv[1]
S.community=sys.argv[2]

if "Ethernet Routing Switch 5510" not in get(M.SNMPv2_MIB.sysDescr(0)).value:
    print "Not a 5510"
    sys.exit(1)

for o in walk(M.Q_BRIDGE_MIB.dot1qPortIngressFiltering):
    if o.value != 2:
        print "Filtering on port %d of %s is not disabled, disable it." % (o.iid, S.host)
        set(o << "false")
