#!/usr/bin/snimpy

"""
Set NTP or syslog server on various switches

Usage:
 ./set-syslog-ntp.py [syslog|ntp] host community first [...]
"""

import os
import sys

load("SNMPv2-MIB")

host = sys.argv[2]
targets = sys.argv[4:]
operation = sys.argv[1]

try:
    s = M(host=host, community=sys.argv[3])
    sid = str(s.sysObjectID)
except snmp.SNMPException, e:
    print "%s: %s" % (host, e)
    sys.exit(1)

if sid.startswith("1.3.6.1.4.1.45.3."):
    # Nortel
    print "%s is Nortel 55xx" % host
    load(os.path.expanduser("~/.snmp/mibs/SYNOPTICS-ROOT-MIB"))
    load(os.path.expanduser("~/.snmp/mibs/S5-ROOT-MIB"))
    if operation == "ntp":
        load(os.path.expanduser("~/.snmp/mibs/S5-AGENT-MIB"))
        s.s5AgSntpPrimaryServerAddress = targets[0]
        if len(targets) > 1:
            s.s5AgSntpSecondaryServerAddress = targets[1]
        else:
            s.s5AgSntpSecondaryServerAddress = "0.0.0.0"
        s.s5AgSntpState = "unicast"
        s.s5AgSntpManualSyncRequest = "requestSync"
    elif operation == "syslog":
        load(os.path.expanduser("~/.snmp/mibs/BN-LOG-MESSAGE-MIB"))
        s.bnLogMsgRemoteSyslogAddress = targets[0]
        s.bnLogMsgRemoteSyslogSaveTargets = "msgTypeInformational"
        s.bnLogMsgRemoteSyslogEnabled = True
elif sid.startswith("1.3.6.1.4.1.1872."):
    print "%s is Alteon" % host
    load(os.path.expanduser("~/.snmp/mibs/ALTEON-ROOT-MIB"))
    if operation == "ntp":
        s.agNewCfgNTPServer = targets[0]
        if len(targets) > 1:
            s.agNewCfgNTPSecServer = targets[1]
        else:
            s.agNewCfgNTPSecServer = "0.0.0.0"
        s.agNewCfgNTPService = "enabled"
    elif operation == "syslog":
        s.agNewCfgSyslogHost = targets[0]
        s.agNewCfgSyslogFac = "local2"
        if len(targets) > 1:
            s.agNewCfgSyslog2Host = targets[1]
            s.agNewCfgSyslog2Fac = "local2"
        else:
            s.agNewCfgSyslog2Host = "0.0.0.0"
    if s.agApplyPending == "applyNeeded":
        if s.agApplyConfig == "complete":
            s.agApplyConfig = "idle"
        s.agApplyConfig = "apply"
else:
    print "%s is unknown (%s)" % (host, s.sysDescr)
    sys.exit(1)
