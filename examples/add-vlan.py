#!/usr/bin/snimpy

"""
On Nortel switches, create a new VLAN and tag it on "TagAll" ports.
"""

from __future__ import with_statement

import os
import sys

load("SNMPv2-MIB")
load(os.path.expanduser("~/.snmp/mibs/RAPID-CITY-MIB"))
load(os.path.expanduser("~/.snmp/mibs/RC-VLAN-MIB"))

vlanNumber = int(sys.argv[3])
vlanName = sys.argv[4]
s = M(host=sys.argv[1], community=sys.argv[2])

# Create the VLAN
if vlanNumber not in s.rcVlanId:
    print "VLAN %d will be created with name %s on %s" % (vlanNumber, vlanName, sys.argv[1])
    with s:
        s.rcVlanRowStatus[vlanNumber] = "createAndGo"
        s.rcVlanName[vlanNumber] = vlanName
        s.rcVlanType[vlanNumber] = "byPort"
else:
    print "VLAN %d already exists on %s" % (vlanNumber, sys.argv[1])
    # Just set the name
    if s.rcVlanName[vlanNumber] != vlanName:
        s.rcVlanName[vlanNumber] = vlanName

# Which ports are tagall ?
tagged = [port for port in s.rcVlanPortPerformTagging
          if s.rcVlanPortPerformTagging[port] ]
if len(tagged) != 2 and len(tagged) != 3:
    print "%s does not have exactly two or three tagged ports (%r)" % (sys.argv[1], tagged)
    sys.exit(1)
print "VLAN %d will be tagged on ports %s" % (vlanNumber, tagged)
s.rcVlanStaticMembers[vlanNumber] |= tagged
