#!/usr/bin/snimpy

"""
Get serial number of a given equipment using ENTITY-MIB
"""

import sys

load("ENTITY-MIB")

host=sys.argv[1]
s = M(host=host, community=sys.argv[2])

# Locate parent of all other elements
print("[-] %s: Search for parent element" % host)
parent = None
for i in s.entPhysicalContainedIn:
    if s.entPhysicalContainedIn[i] == 0:
        parent = i
        break
if parent is None:
    print("[!] %s: Unable to find parent" % host)
    sys.exit(1)
print("[+] {}: {}".format(host, s.entPhysicalDescr[parent]))
print("[+] {}: HW {}, FW {}, SW {}".format(host,
                                           s.entPhysicalHardwareRev[parent],
                                           s.entPhysicalFirmwareRev[parent],
                                           s.entPhysicalSoftwareRev[parent]))
print("[+] {}: SN {}".format(host,
                             s.entPhysicalSerialNum[parent]))
