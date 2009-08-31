#!/usr/bin/snimpy

"""
Set NTP server on various switches
"""

import os
import sys

load("SNMPv2-MIB")

try:
    s = M(host=sys.argv[1], community=sys.argv[2])
    ntp = sys.argv[3:]
    sid = str(s.sysObjectID)
except snmp.SNMPException, e:
    print "%s: %s" % (sys.argv[1], str(e))
    sys.exit(1)

if sid.startswith("1.3.6.1.4.1.45.3."):
    # Nortel
    print "%s is Nortel 55xx" % sys.argv[1]
    load(os.path.expanduser("~/.snmp/mibs/SYNOPTICS-ROOT-MIB"))
    load(os.path.expanduser("~/.snmp/mibs/S5-ROOT-MIB"))
    load(os.path.expanduser("~/.snmp/mibs/S5-AGENT-MIB"))
    s.s5AgSntpPrimaryServerAddress = ntp[0]
    if len(ntp) > 1:
        s.s5AgSntpSecondaryServerAddress = ntp[1]
    else:
        s.s5AgSntpSecondaryServerAddress = "0.0.0.0"
    s.s5AgSntpState = "unicast"
    s.s5AgSntpManualSyncRequest = "requestSync"
elif sid.startswith("1.3.6.1.4.1.1872.") or sid.startswith("1.3.6.1.4.1.26543."):
    print "%s is Alteon" % sys.argv[1]
    if sid.startswith("1.3.6.1.4.1.1872."):
        load(os.path.expanduser("~/.snmp/mibs/Alteon/ALTEON-ROOT-MIB"))
    else:
        load(os.path.expanduser("~/.snmp/mibs/AlteonNew/ALTEON-ROOT-MIB"))
    s.agNewCfgNTPServer = ntp[0]
    if len(ntp) > 1:
        s.agNewCfgNTPSecServer = ntp[1]
    else:
        s.agNewCfgNTPSecServer = "0.0.0.0"
    s.agNewCfgNTPService = "enabled"
    if s.agApplyPending == "applyNeeded":
        if s.agApplyConfig == "complete":
            s.agApplyConfig = "idle"
        s.agApplyConfig = "apply"
else:
    print "%s is unknown (%s)" % (sys.argv[1], s.sysDescr)
    sys.exit(1)
