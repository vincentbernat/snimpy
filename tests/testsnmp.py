import unittest
import os
from datetime import timedelta
from snimpy import basictypes, snmp, mib

"""Those tests need a local SNMP agent. They are not deterministic"""

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

    def testInexistant(self):
        """Get an inexistant value"""
        self.assertRaises(snmp.SNMPNoSuchObject, self.session.get,
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
            self.assertRaises(snmp.SNMPNoAccess, self.session.set,
                              mib.get('SNIMPY-MIB', oid).oid + (0,),
                              basictypes.build('SNIMPY-MIB', oid, value))

# Do the same tests with SNMPv1
class TestSnmp1(unittest.TestCase):
    version = 1
