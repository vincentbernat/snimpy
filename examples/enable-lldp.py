#!/usr/bin/snimpy

"""Enable LLDP.

Generic procedure but we restrict ourself to Nortel 55x0.
"""

import sys

S.host=sys.argv[1]
S.community=sys.argv[2]

M.load("~/.snmp/mibs/LLDP-MIB")
M.load("~/.snmp/mibs/LLDP-EXT-DOT3-MIB")
M.load("~/.snmp/mibs/LLDP-EXT-DOT1-MIB")

try:
    type = get(M.SNMPv2_MIB.sysDescr(0))
except snmp.SNMPGenericError:
    print "Cannot process %s: bad community?" % S.host
    sys.exit(1)
if not type.value.startswith("Ethernet Routing Switch 55") and \
        not type.value.startswith("Ethernet Switch 425"):
    print "Not a 55x0: %s" % type.value
    sys.exit(1)

print "Processing %s..." % S.host
try:
    for oid in walk(M.LLDP_MIB.lldpConfigManAddrPortsTxEnable(1,4)):
        set(oid << "\xff"*10)
except snmp.SNMPNoSuchObject:
    print "No LLDP for this switch"
    sys.exit(2)
dot3 = True
for oid in walk(M.LLDP_MIB.lldpPortConfigAdminStatus):
    port = oid.iid
    # Standard
    set([M.LLDP_MIB.lldpPortConfigAdminStatus(port) << "txAndRx",
         M.LLDP_MIB.lldpPortConfigTLVsTxEnable(port) << ["portDesc",
                                                         "sysName",
                                                         "sysDesc",
                                                         "sysCap" ]])
    # Dot3
    try:
        if dot3:
            set(M.LLDP_EXT_DOT3_MIB.lldpXdot3PortConfigTLVsTxEnable(port) << ["macPhyConfigStatus",
                                                                              "powerViaMDI",
                                                                              "linkAggregation",
                                                                              "maxFrameSize"])
    except snmp.SNMPPacketError:
        print "No Dot3"
        dot3 = False
# Dot1
try:
    for oid in walk(M.LLDP_EXT_DOT1_MIB.lldpXdot1LocVlanNameTable):
        (port, vlan) = oid.iid
        set(M.LLDP_EXT_DOT1_MIB.lldpXdot1ConfigVlanNameTxEnable(port, vlan) << "true")
except snmp.SNMPNoSuchObject:
    print "No Dot1"
print "Success!"
