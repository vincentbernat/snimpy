#!/usr/bin/snimpy

import os
import sys

load("SNMPv2-MIB")
load(os.path.expanduser("~/.snmp/mibs/RAPID-CITY-MIB"))
load(os.path.expanduser("~/.snmp/mibs/RC-VLAN-MIB"))

vlanNumber = int(sys.argv[3])
newName = sys.argv[4]
s = M(host=sys.argv[1], community=sys.argv[2])


try:
    cur = s.rcVlanName[vlanNumber]
except snmp.SNMPException:
    print "%s is not a Nortel switch or does not have VLAN %d" % (sys.argv[1], vlanNumber)
    sys.exit(1)
if cur != newName:
    s.rcVlanName[vlanNumber] = newName
print "Setting VLAN %d of %s as %s: done." % (vlanNumber, sys.argv[1], newName)
