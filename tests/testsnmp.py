import unittest
import os
from datetime import timedelta
from snimpy import basictypes, snmp, mib

"""Those tests need a local SNMP agent. They are not deterministic"""

class TestSnmpRetriesTimeout(unittest.TestCase):

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

class TestSnmp2(unittest.TestCase):
    version = 2

    def setUp(self):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')
        self.session = snmp.Session(host="localhost",
                                    community="public",
                                    version=self.version)

    def testGetString(self):
        """Get a string value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid, a = self.session.get(ooid)[0]
        self.assertEqual(oid, ooid)
        self.assertEqual(a, " ".join(os.uname()))
    
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
        self.assertEqual(a, " ".join(os.uname()))

    def testInexistant(self):
        """Get an inexistant value"""
        self.assertRaises(self.version == 1 and snmp.SNMPNoSuchName or snmp.SNMPNoSuchObject,
                          self.session.get,
                          (1,2,3))

    def testVariousSet(self):
        """Set value of many types. This test should be monitored with a traffic capture"""
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))
        for oid, value in [('snimpyIpAddress', '10.14.12.12'),
                           ('snimpyInteger', 1574512),
                           ('snimpyEnum', 'testing'),
                           ('snimpyObjectId', (1,2,3,4,5,6)),
                           ('snimpyCounter', 545424),
                           ('snimpyGauge', 4857544),
                           ('snimpyTimeticks', timedelta(3, 18)),
                           ('snimpyBits', ["third", "last"])]:
            self.assertRaises(self.version == 1 and snmp.SNMPNoSuchName or snmp.SNMPNoAccess,
                              self.session.set,
                              mib.get('SNIMPY-MIB', oid).oid + (0,),
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
        self.assertEqual(a1, " ".join(os.uname()))
        self.assert_(a2 > 1)
        b = basictypes.build('IF-MIB', 'ifType', a3)
        self.assertEqual(b, "softwareLoopback")

# Do the same tests with SNMPv1
class TestSnmp1(TestSnmp2):
    version = 1

# Do various session tests
class TestSnmpSession(unittest.TestCase):

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
