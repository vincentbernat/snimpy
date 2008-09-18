import unittest
import os
from snimpy import basictypes, snmp, mib

"""Those tests need a local SNMP agent. They are not deterministic"""

class TestSnmp2(unittest.TestCase):
    version = 2

    def setUp(self):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')
        self.session = snmp.Session(host="localhost",
                                    community="private",
                                    version=self.version)

    def testGetString(self):
        """Get a string value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid, a = self.session.get(ooid)
        self.assertEqual(oid, ooid)
        self.assertEqual(a, " ".join(os.uname()))
    
    def testGetInteger(self):
        """Get an integer value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifNumber').oid + (0,))
        self.assert_(a > 1)     # At least lo and another interface

    def testGetEnum(self):
        """Get an enum value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifType').oid + (1,))
        self.assertEqual(a, 24) # This is software loopback
        b = basictypes.build('IF-MIB', 'ifType', a)
        self.assertEqual(b, "softwareLoopback")
    
    def testGetNext(self):
        """Get next value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid
        oid, a = self.session.getnext(ooid)
        self.assertEqual(oid, ooid + (0,))
        self.assertEqual(a, " ".join(os.uname()))

    def testSet(self):
        """Set a value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid, orig = self.session.get(ooid)
        oid, a = self.session.set(ooid, basictypes.build('SNMPv2-MIB', 'sysDescr',
                                                         "new hostname"))
        self.assertEqual(oid, ooid)
        self.assertEqual(a, "new hostname")
        oid, a = self.session.set(ooid, basictypes.build('SNMPv2-MIB', 'sysDescr',
                                                         orig))
        self.assertEqual(a, orig)

    def testInexistant(self):
        """Get an inexistant value"""
        self.assertRaises(snmp.SNMPNoSuchObject, self.session.get,
                          (1,2,3))

# Do the same tests with SNMPv1
class TestSnmp1(unittest.TestCase):
    version = 1
