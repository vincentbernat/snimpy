#!/usr/bin/snimpy

"""Enable LLDP.

Generic procedure but we restrict ourself to Nortel 55x0.
"""

import sys
import os

load("SNMPv2-MIB")
for l in ["LLDP", "LLDP-EXT-DOT3", "LLDP-EXT-DOT1"]:
    load(os.path.expanduser("~/.snmp/mibs/%s-MIB" % l))

s = M(host=sys.argv[1], community=sys.argv[2])

try:
    type = s.sysDescr
except snmp.SNMPException:
    print "Cannot process %s: bad community?" % sys.argv[1]
    sys.exit(1)
if not type.startswith("Ethernet Routing Switch 55") and \
        not type.startswith("Ethernet Switch 425"):
    print "Not a 55x0: %s" % type
    sys.exit(1)

print "Processing %s..." % sys.argv[1]
try:
    for oid in s.lldpConfigManAddrPortsTxEnable:
        
        if oid[0] == "ipV4":
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
    except snmp.SNMPException:
        print "No Dot3"
        dot3 = False
# Dot1
try:
    for port,vlan in s.lldpXdot1ConfigVlanNameTxEnable:
        s.lldpXdot1ConfigVlanNameTxEnable[port, vlan] = True
except snmp.SNMPException:
    print "No Dot1"
print "Success!"
