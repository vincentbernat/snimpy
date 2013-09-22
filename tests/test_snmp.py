import unittest
import os
import time
from datetime import timedelta
from snimpy import basictypes, snmp, mib
import agent

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
                     secname="readonly",
                     authprotocol="MD5", authpassword="authpass",
                     privprotocol="AES", privpassword="privpass")

    def testSnmpV3Protocols(self):
        """Check accepted auth and privacy protocols"""
        for auth in ["MD5", "SHA"]:
            for priv in ["AES", "AES128", "DES"]:
                snmp.Session(host="localhost",
                             version=3,
                             secname="readonly",
                             authprotocol=auth, authpassword="authpass",
                             privprotocol=priv, privpassword="privpass")
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
                          secname="readonly",
                          authprotocol="NOEXIST", authpassword="authpass",
                          privprotocol="AES", privpassword="privpass")
        self.assertRaises(ValueError,
                          snmp.Session,
                          host="localhost",
                          version=3,
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
                     secname="readonly",
                     authprotocol=None,
                     privprotocol=None)
        snmp.Session(host="localhost",
                     version=3,
                     secname="readonly",
                     authprotocol=auth, authpassword="authpass",
                     privprotocol=None)


class TestSnmp1(unittest.TestCase):
    """
    Test communication with an agent with SNMPv1.
    """
    version = 1

    @classmethod
    def setUpClass(cls):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')
        cls.agent = agent.TestAgent()

    def setUp(self):
        self.session = snmp.Session(host="127.0.0.1:%d" % self.agent.port,
                                    community="public",
                                    version=self.version)

    @classmethod
    def tearDownClass(cls):
        cls.agent.terminate()

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

    def testBulk(self):
        """Try to set bulk to different values"""
        self.session.bulk = 32
        self.assertEqual(self.session.bulk, 32)
        self.assertRaises(ValueError,
                          setattr,
                          self.session,
                          "bulk",
                          0)
        self.assertRaises(ValueError,
                          setattr,
                          self.session,
                          "bulk",
                          -10)

    def testWalk(self):
        """Check if we can walk"""
        ooid = mib.get("IF-MIB", "ifDescr").oid
        results = self.session.walk(ooid)
        self.assertEqual(results,
                         ((ooid + (1,), "lo"),
                          (ooid + (2,), "eth0"),
                          (ooid + (3,), "eth1")))

class TestSnmp2(TestSnmp1):
    """Test communication with an agent with SNMPv2."""
    version = 2

    def testSetCounter64(self):
        """Set Counter64."""
        self.setAndCheck('snimpyCounter64',  2**47+1)

    def testWalk(self):
        """Check if we can walk"""
        ooid = mib.get("IF-MIB", "ifDescr").oid
        self.session.bulk = 4
        results = self.session.walk(ooid)
        self.assertEqual(results,
                         ((ooid + (1,), "lo"),
                          (ooid + (2,), "eth0"),
                          (ooid + (3,), "eth1"),
                          (mib.get("IF-MIB", "ifType").oid + (1,), 24)))
        self.session.bulk = 2
        results = self.session.walk(ooid)
        self.assertEqual(results[:2],
                         ((ooid + (1,), "lo"),
                          (ooid + (2,), "eth0")))

class TestSnmp3(TestSnmp2):
    """Test communicaton with an agent with SNMPv3."""
    version = 3

    def setUp(self):
        self.session = snmp.Session(host="127.0.0.1:%d" % self.agent.port,
                                    version=3,
                                    secname="read-write",
                                    authprotocol="MD5", authpassword="authpass",
                                    privprotocol="AES", privpassword="privpass")
