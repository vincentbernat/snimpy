#!/usr/bin/snimpy

"""Enable LLDP.

Generic procedure but we restrict ourself to Nortel 55x0.
"""

import sys

load("~/.snmp/mibs/LLDP-MIB")
load("~/.snmp/mibs/LLDP-EXT-DOT3-MIB")
load("~/.snmp/mibs/LLDP-EXT-DOT1-MIB")

s = S(host=sys.argv[1], community=sys.argv[2])

try:
    type = s.sysDescr
except snmp.SNMPGenericError:
    print "Cannot process %s: bad community?" % sys.argv[1]
    sys.exit(1)
if not type.value.startswith("Ethernet Routing Switch 55") and \
        not type.value.startswith("Ethernet Switch 425"):
    print "Not a 55x0: %s" % type.value
    sys.exit(1)

print "Processing %s..." % sys.argv[1]
try:
    for oid in s.lldpConfigManAddrPortsTxEnable:
        if oid[:2] == (1,4):
            s.lldpConfigManAddrPortsTxEnable[oid] = "\xff"*10
except snmp.SNMPNoSuchObject:
    print "No LLDP for this switch"
    sys.exit(2)
dot3 = True
for port in s.lldpPortConfigAdminStatus:
    s.lldpPortConfigAdminStatus[port] = "txAndRx"
    s.lldpPortConfigTLVsTxEnable[port] = ["portDesc",
                                          "sysName",
                                          "sysDesc",
                                          "sysCap" ]
    # Dot3
    try:
        if dot3:
            s.lldpXdot3PortConfigTLVsTxEnable[port] = ["macPhyConfigStatus",
                                                       "powerViaMDI",
                                                       "linkAggregation",
                                                       "maxFrameSize"]
    except snmp.SNMPPacketError:
        print "No Dot3"
        dot3 = False
# Dot1
try:
    for (port,vlan) in s.lldpXdot1LocVlanNameTable:
        s.lldpXdot1ConfigVlanNameTxEnable[port, vlan] = "true"
except snmp.SNMPNoSuchObject:
    print "No Dot1"
print "Success!"
