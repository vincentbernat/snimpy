import unittest
import os
import random
import threading
from datetime import timedelta
from snimpy import basictypes, snmp, mib

from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.proto.api import v2c

class TestSnmpRetriesTimeout(unittest.TestCase):
    """Live modification of retry and timeout values for a session"""

    def setUp(self):
        self.session = snmp.Session(host="localhost",
                                    community="public",
                                    version=2)
    def testGetRetries(self):
        """Get default retries value"""
        self.assertEqual(self.session.retries, 5)

    def testGetTimeout(self):
        """Get default timeout value"""
        self.assertEqual(self.session.timeout, 1000000)

    def testSetRetries(self):
        """Try to set a new retry value"""
        self.session.retries = 2
        self.assertEqual(self.session.retries, 2)
        self.session.retries = 0
        self.assertEqual(self.session.retries, 0)

    def testSetTimeout(self):
        """Try to set a new timeout value"""
        self.session.timeout = 500000
        self.assertEqual(self.session.timeout, 500000)

    def testErrors(self):
        """Try invalid values for timeout and retries"""
        self.assertRaises(ValueError, setattr, self.session, "timeout", 0)
        self.assertRaises(ValueError, setattr, self.session, "timeout", -30)
        self.assertRaises(ValueError, setattr, self.session, "retries", -5)

class TestSnmpSession(unittest.TestCase):
    """Test for session creation using SNMPv1/v2c/v3"""

    def testSnmpV1(self):
        """Check initialization of SNMPv1 session"""
        snmp.Session(host="localhost",
                     community="public",
                     version=1)

    def testSnmpV2(self):
        """Check initialization of SNMPv2 session"""
        snmp.Session(host="localhost",
                     community="public",
                     version=2)

    def testSnmpV3(self):
        """Check initialization of SNMPv3 session"""
        snmp.Session(host="localhost",
                     version=3,
                     seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                     secname="readonly",
                     authprotocol="MD5", authpassword="authpass",
                     privprotocol="AES", privpassword="privpass")

    def testSnmpV3TooShortPassword(self):
        """Try to use a password too short with SNMPv3"""
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
                          seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                          secname="readonly",
                          authprotocol="MD5", authpassword="au",
                          privprotocol="AES", privpassword="privpass")
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
                          seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                          secname="readonly",
                          authprotocol="MD5", authpassword="authpass",
                          privprotocol="AES", privpassword="pr")

    def testSnmpV3Protocols(self):
        """Check accepted auth and privacy protocols"""
        for auth in ["MD5", "SHA"]:
            for priv in ["AES", "AES128", "DES"]:
                snmp.Session(host="localhost",
                             version=3,
                             seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                             secname="readonly",
                             authprotocol=auth, authpassword="authpass",
                             privprotocol=priv, privpassword="privpass")
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
                          seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                          secname="readonly",
                          authprotocol="NOEXIST", authpassword="authpass",
                          privprotocol="AES", privpassword="privpass")
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
                          seclevel=snmp.SNMP_SEC_LEVEL_AUTHPRIV,
                          secname="readonly",
                          authprotocol="MD5", authpassword="authpass",
                          privprotocol="NOEXIST", privpassword="privpass")

    def testSnmpV3SecLevels(self):
        """Check accepted security levels"""
        auth = "MD5"
        priv = "DES"
        snmp.Session(host="localhost",
                     version=3,
                     secname="readonly",
                     authprotocol=auth, authpassword="authpass",
                     privprotocol=priv, privpassword="privpass")
        snmp.Session(host="localhost",
                     version=3,
                     seclevel=snmp.SNMP_SEC_LEVEL_NOAUTH,
                     secname="readonly",
                     authprotocol=auth, authpassword="authpass",
                     privprotocol=priv, privpassword="privpass")
        snmp.Session(host="localhost",
                     version=3,
                     seclevel=snmp.SNMP_SEC_LEVEL_AUTHNOPRIV,
                     secname="readonly",
                     authprotocol=auth, authpassword="authpass",
                     privprotocol=priv, privpassword="privpass")

class TestSnmp2(unittest.TestCase):
    """
    Test communication with an agent with SNMPv2.

    An agent should run on localhost for those tests to work.
    """
    version = 2

    def setUp(self):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')
        # Create a real agent with PySNMP
        self.snmpEngine = engine.SnmpEngine()
        self.port = random.randrange(20000, 23000)
        config.addSocketTransport(
            self.snmpEngine,
            udp.domainName,
            udp.UdpTransport().openServerMode(('127.0.0.1', self.port)))
        # Community is public and MIB is writable
        config.addV1System(self.snmpEngine, 'read-write', 'public')
        config.addVacmUser(self.snmpEngine, self.version, 'read-write', 'noAuthNoPriv',
                           (1, 3, 6), (1, 3, 6))
        # Build MIB
        snmpContext = context.SnmpContext(self.snmpEngine)
        mibBuilder = snmpContext.getMibInstrum().getMibBuilder()
        (MibTable, MibTableRow, MibTableColumn,
         MibScalar, MibScalarInstance) = mibBuilder.importSymbols(
             'SNMPv2-SMI',
             'MibTable', 'MibTableRow', 'MibTableColumn',
             'MibScalar', 'MibScalarInstance')
        mibBuilder.exportSymbols(
            '__MY_SNMPv2_MIB',
            # SNMPv2-MIB::sysDescr
            MibScalar((1, 3, 6, 1, 2, 1, 1, 1), v2c.OctetString()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 1, 1), (0,), v2c.OctetString("Snimpy Test Agent")))
        mibBuilder.exportSymbols(
            '__MY_IF_MIB',
            # IF-MIB::ifNumber
            MibScalar((1, 3, 6, 1, 2, 1, 2, 1), v2c.Integer()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 1), (0,), v2c.Integer(3)),
            # IF-MIB::ifTable
            # IF-MIB::ifDescr
            MibTable((1, 3, 6, 1, 2, 1, 2, 2)),
            MibTableRow((1, 3, 6, 1, 2, 1, 2, 2, 1)).setIndexNames((0, '__IF_MIB', 'ifIndex')),
            # IF-MIB::ifIndex
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (1,), v2c.Integer(1)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (2,), v2c.Integer(2)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (3,), v2c.Integer(3)),
            # IF-MIB::ifDescr
            MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 2), v2c.OctetString()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (1,), v2c.OctetString("lo")),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (2,), v2c.OctetString("eth0")),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (3,), v2c.OctetString("eth1")),
            # IF-MIB::ifType
            MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 3), v2c.Integer()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (1,), v2c.Integer(24)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (2,), v2c.Integer(6)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (3,), v2c.Integer(6)),
            # IF-MIB::ifIndex
            ifIndex=MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 1), v2c.Integer()))
        mibBuilder.exportSymbols(
            '__MY_SNIMPY-MIB',
            # SNIMPY-MIB::snimpyIpAddress
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 1), v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 1), (0,), v2c.OctetString("AAAA")),
            # SNIMPY-MIB::snimpyString
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 2), v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 2), (0,), v2c.OctetString("bye")),
            # SNIMPY-MIB::snimpyInteger
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 3), v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 3), (0,), v2c.Integer(19)),
            # SNIMPY-MIB::snimpyEnum
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 4), v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 4), (0,), v2c.Integer(19)),
            # SNIMPY-MIB::snimpyObjectId
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 5), v2c.ObjectIdentifier()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 5), (0,), v2c.ObjectIdentifier((0,0))),
            # SNIMPY-MIB::snimpyBoolean
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 6), v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 6), (0,), v2c.Integer(1)),
            # SNIMPY-MIB::snimpyCounter
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 7), v2c.Counter32()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 7), (0,), v2c.Counter32(47)),
            # SNIMPY-MIB::snimpyGauge
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 8), v2c.Gauge32()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 8), (0,), v2c.Gauge32(18)),
            # SNIMPY-MIB::snimpyTimeticks
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 9), v2c.TimeTicks()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 9), (0,), v2c.TimeTicks(12111100)),
            # SNIMPY-MIB::snimpyCounter64
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 10), v2c.Counter64()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 10), (0,), v2c.Counter64(47)),
            # SNIMPY-MIB::snimpyBits
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 11), v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 11), (0,), v2c.OctetString("\x00")),
        )
        # Start agent
        cmdrsp.GetCommandResponder(self.snmpEngine, snmpContext)
        cmdrsp.SetCommandResponder(self.snmpEngine, snmpContext)
        cmdrsp.NextCommandResponder(self.snmpEngine, snmpContext)
        cmdrsp.BulkCommandResponder(self.snmpEngine, snmpContext)
        self.snmpEngine.transportDispatcher.jobStarted(1)
        def runDispatcher():
            try:
                self.snmpEngine.transportDispatcher.runDispatcher()
            except:
                pass
        threading.Thread(target=runDispatcher,).start()
        # Open session
        self.session = snmp.Session(host="localhost:%d" % self.port,
                                    community="public",
                                    version=self.version)

    def tearDown(self):
        self.snmpEngine.transportDispatcher.jobFinished(1)
        self.snmpEngine.transportDispatcher.closeDispatcher()

    def testGetString(self):
        """Get a string value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid, a = self.session.get(ooid)[0]
        self.assertEqual(oid, ooid)
        self.assertEqual(a, "Snimpy Test Agent")

    def testGetInteger(self):
        """Get an integer value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifNumber').oid + (0,))[0]
        self.assert_(a > 1)     # At least lo and another interface

    def testGetEnum(self):
        """Get an enum value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifType').oid + (1,))[0]
        self.assertEqual(a, 24) # This is software loopback
        b = basictypes.build('IF-MIB', 'ifType', a)
        self.assertEqual(b, "softwareLoopback")

    def testGetNext(self):
        """Get next value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid
        oid, a = self.session.getnext(ooid)[0]
        self.assertEqual(oid, ooid + (0,))
        self.assertEqual(a, "Snimpy Test Agent")

    def testInexistant(self):
        """Get an inexistant value"""
        self.assertRaises(self.version == 1 and snmp.SNMPNoSuchName or snmp.SNMPNoSuchObject,
                          self.session.get,
                          (1,2,3))

    def testSetIpAddress(self):
        """Set IpAddress."""
        self.setAndCheck('snimpyIpAddress',  '10.14.12.12')

    def testSetString(self):
        """Set String."""
        self.setAndCheck('snimpyString',  'hello')

    def testSetInteger(self):
        """Set Integer."""
        self.setAndCheck('snimpyInteger',  1574512)

    def testSetEnum(self):
        """Set Enum."""
        self.setAndCheck('snimpyEnum',  'testing')

    def testSetObjectId(self):
        """Set ObjectId."""
        self.setAndCheck('snimpyObjectId',  (1,2,3,4,5,6))

    def testSetCounter(self):
        """Set Counter."""
        self.setAndCheck('snimpyCounter',  545424)

    def testSetCounter64(self):
        """Set Counter64."""
        self.setAndCheck('snimpyCounter64',  2**47+1)

    def testSetGauge(self):
        """Set Gauge."""
        self.setAndCheck('snimpyGauge',  4857544)

    def testSetBoolean(self):
        """Set Boolean."""
        self.setAndCheck('snimpyBoolean',  True)

    def testSetTimeticks(self):
        """Set Timeticks."""
        self.setAndCheck('snimpyTimeticks',  timedelta(3, 18))

    def testSetBits(self):
        """Set Bits."""
        self.setAndCheck('snimpyBits',  ["third", "last"])

    def setAndCheck(self, oid, value):
        """Set and check a value"""
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))
        ooid = mib.get('SNIMPY-MIB', oid).oid + (0,)
        self.session.set(ooid,
                         basictypes.build('SNIMPY-MIB', oid, value))
        self.assertEqual(basictypes.build('SNIMPY-MIB', oid, self.session.get(ooid)[0][1]),
                         basictypes.build('SNIMPY-MIB', oid, value))

    def testMultipleGet(self):
        """Get multiple values at once"""
        ooid1 = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        ooid2 = mib.get('IF-MIB', 'ifNumber').oid + (0,)
        ooid3 = mib.get('IF-MIB', 'ifType').oid + (1,)
        (oid1, a1), (oid2, a2), (oid3, a3) = self.session.get(
            ooid1, ooid2, ooid3)
        self.assertEqual(oid1, ooid1)
        self.assertEqual(oid2, ooid2)
        self.assertEqual(oid3, ooid3)
        self.assertEqual(a1, "Snimpy Test Agent")
        self.assert_(a2 > 1)
        b = basictypes.build('IF-MIB', 'ifType', a3)
        self.assertEqual(b, "softwareLoopback")

class TestSnmp1(TestSnmp2):
    """Test communication with an agent with SNMPv1."""
    version = 1

    @unittest.skip("no counter64 for SNMPv1")
    def testSetCounter64(self):
        pass
