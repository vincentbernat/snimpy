#!/usr/bin/snimpy

"""
On Nortel switches, list vlan on all active ports
"""

import os
import sys

load("SNMPv2-MIB")
load("IF-MIB")
load(os.path.expanduser("~/.snmp/mibs/RAPID-CITY-MIB"))
load(os.path.expanduser("~/.snmp/mibs/RC-VLAN-MIB"))

s = M(host=sys.argv[1], community=sys.argv[2])

vlans = {}

for interface in s.ifIndex:
    if s.ifOperStatus[interface] == "up":
        vlans[int(interface)] = []

for vlan in s.rcVlanId:
    for interface in vlans:
        if s.rcVlanStaticMembers[vlan] & interface:
            vlans[interface].append("%s(%s)" % (vlan, s.rcVlanName[vlan]))

import pprint
pprint.pprint(vlans)

