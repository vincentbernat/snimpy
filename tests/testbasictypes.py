import unittest
import os
from datetime import timedelta
from snimpy import mib, basictypes, snmp

class TestBasicTypes(unittest.TestCase):

    def setUp(self):
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))

    def tearDown(self):
        mib.reset()

    def testInteger(self):
        """Test integer basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyInteger", 18)
        self.assert_(isinstance(a, basictypes.Integer))
        self.assertEqual(a, 18)
        self.assertEqual(a+10, 28)
        a.set(4)
        self.assertEqual(a, 4)
        self.assertEqual(a*4, 16)
        a.set("5")
        self.assertEqual(a, 5)
        self.assert_(a < 6)
        # self.assert_(a > 4.6) # type coercion does not work
        self.assert_(a > 4)
        self.assertRaises(TypeError, a.set, [1,3,4])

    def testString(self):
        """Test string basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", "hello")
        self.assert_(isinstance(a, basictypes.String))
        self.assertEqual(a, "hello")
        self.assertEqual(a + " john", "hello john")
        self.assertEqual(a*2, "hellohello")
        a.set(45)
        self.assertEqual(a, "45")
        self.assert_('4' in a)
        a.set("hello john")
        self.assert_("john" in a)
        self.assert_("steve" not in a)
        self.assertEqual(a[1], 'e')
        self.assertEqual(a[1:4], 'ell')
        self.assertEqual(len(a), 10)
        self.assertEqual([i for i in a],
                         [i for i in "hello john"])

    def testIpAddress(self):
        """Test IP address basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", "10.0.4.5")
        self.assertRaises(ValueError, a.set, "999.5.6.4")
        self.assertEqual(a, "10.0.4.5")
        self.assertEqual(a, "10.00.4.05")
        self.assertEqual(a, [10,0,4,5])
        self.assertEqual(a[2], 4)
        self.assert_(a < "10.1.2.4")
        self.assert_(a > "10.0.0.1")
        a.set([1,2,3,5])
        self.assertEqual(a, "1.2.3.5")

    def testEnum(self):
        """Test enum basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyEnum", 1)
        self.assertEqual(a, 1)
        self.assertEqual(a, "up")
        a.set("down")
        self.assertEqual(a, "down")
        self.assertEqual(a, 2)
        self.assertEqual(str(a), "down(2)")
        self.assertRaises(ValueError, a.set, "unknown")
        self.assertRaises(ValueError, a.set, 54)
        self.assertEqual(str(a), "down(2)")

    def testOid(self):
        """Test OID basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyObjectId",
                             mib.get("SNIMPY-MIB", "snimpyInteger"))
        self.assertEqual(a, mib.get("SNIMPY-MIB", "snimpyInteger"))
        self.assertEqual(a, mib.get("SNIMPY-MIB", "snimpyInteger").oid)
        # Suboid
        self.assert_((list(mib.get("SNIMPY-MIB",
                                   "snimpyInteger").oid) + [2,3]) in a)
        self.assert_((list(mib.get("SNIMPY-MIB",
                                   "snimpyInteger").oid)[:-1] + [29,3]) not in a)
        # Also accepts list
        a.set((1,2,3,4))
        self.assertEqual(a, (1,2,3,4))
        self.assert_((1,2,3,4,5) in a)
        self.assert_((3,4,5,6) not in a)

    def testBoolean(self):
        """Test boolean basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyBoolean", True)
        self.assertEqual(a, True)
        self.assert_(a)
        self.assert_(not(not(a)))
        self.assertEqual(not(a), False)
        a.set("false")
        self.assertEqual(a, False)
        b = basictypes.build("SNIMPY-MIB", "snimpyBoolean", True)
        self.assertEqual(a or b, True)
        self.assertEqual(a and b, False)

    def testTimeticks(self):
        """Test timeticks basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyTimeticks", 676544)
        # We can compare to int but otherwise, this is a timedelta
        self.assertEqual(a, 676544)
        self.assertEqual(str(a), '1:52:45.440000')
        self.assertEqual(a, timedelta(0, 6765, 440000))
        a.set(timedelta(1, 3))
        self.assertEqual(str(a), '1 day, 0:00:03')
        self.assertEqual(a, (3+3600*24)*100)
        self.assert_(a < timedelta(1,4))
        self.assert_(a > timedelta(1,1))
        self.assert_(a > 654)
        self.assert_(a >= 654)
        self.assert_(a < (3+3600*24)*100 + 2)

    def testBits(self):
        """Test bit basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyBits", [1, 2])
        self.assertEqual(a, [2,1])
        self.assertEqual(a, (1,2))
        self.assertEqual(a, ["second", "third"])
        self.assertEqual(a, ["second", 2])
        a |= "last"
        a |= ["last", "second"]
        self.assertEqual(a, ["second", "last", "third"])
        self.assertEqual(str(a), "second(1), third(2), last(7)")
        a -= 1
        a -= 1
        self.assertEqual(a, ["last", "third"])
        self.assertEqual(a & "last", True)
        self.assertEqual(a & "second", False)
        self.assertEqual(a & ["last", 2], True)
        self.assertEqual(a & ["last", 0], False)
        a.set(["first", "second"])
        self.assertEqual(a, [0,1])
        a.set([])
        self.assertEqual(a, [])
        self.assertEqual(str(a), "")

    def testStringAsBits(self):
        """Test using bit specific operator with string"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", "\x17\x00\x01")
        b = [7, 6, 5, 3, 23]
        for i in range(30):
            if i in b:
                self.assert_(a & i)
            else:
                self.assert_(not(a & i))
        self.assert_(a & [5, 7])
        self.assert_(not(a & [5, 9]))
        a |= [2, 10]
        a -= 22
        a -= [23, 22]
        self.assert_(a & [2, 10])
        self.assert_(not(a & 23))
        self.assertEqual(a, "\x37\x20\x00")
        a |= 31
        self.assertEqual(a, "\x37\x20\x00\x01")

    def testPacking(self):
        """Test pack() function"""
        import struct
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyString",
                                          "Hello world").pack(),
                         (snmp.ASN_OCTET_STR, "Hello world"))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          18).pack(),
                         (snmp.ASN_INTEGER, struct.pack("l", 18)))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          1804).pack(),
                         (snmp.ASN_INTEGER, struct.pack("l", 1804)))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyEnum",
                                          "testing").pack(),
                         (snmp.ASN_INTEGER, struct.pack("l", 3)))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyIpAddress",
                                          "10.11.12.13").pack(),
                         (snmp.ASN_IPADDRESS, "\x0a\x0b\x0c\x0d"))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyObjectId",
                                          (1,2,3,4)).pack(),
                         (snmp.ASN_OBJECT_ID, ("%s"*4) % (struct.pack("l", 1),
                                                        struct.pack("l", 2),
                                                        struct.pack("l", 3),
                                                        struct.pack("l", 4))))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyTimeticks",
                                          timedelta(3, 2)).pack(),
                         (snmp.ASN_INTEGER, struct.pack("l", 3*3600*24*100 + 2*100)))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyBits",
                                          [1,7]).pack(),
                         (snmp.ASN_OCTET_STR, "\x41"))

    def testOid(self):
        """Test conversion to/from OID."""
        tt = { ("snimpySimpleIndex", 47): (47,),
               ("snimpyComplexFirstIP", "10.14.15.4"): (10, 14, 15, 4),
               ("snimpyComplexSecondIP", (14,15,16,17)): (14, 15, 16, 17),
               ("snimpyIndexVarLen", "hello1"): tuple([len("hello1")] + [ord(a) for a in "hello1"]),
               ("snimpyIndexFixedLen", "hello2"): tuple(ord(a) for a in "hello2"),
               ("snimpyIndexImplied", "hello3"): tuple(ord(a) for a in "hello3"),
               }
        for t,v in tt:
            oid = basictypes.build("SNIMPY-MIB",
                                   t,
                                   v).toOid()
            self.assertEqual(oid,
                             tt[t,v])
            # Test double conversion
            self.assertEqual(mib.get("SNIMPY-MIB", t).type.fromOid(
                    mib.get("SNIMPY-MIB", t), oid),
                             (len(tt[t,v]), v))

    def testOidGreedy(self):
        """Test greediness of fromOid."""
        tt = {
            "snimpyIndexVarLen": ((5, 104, 101, 108, 108, 111, 111, 111, 111), (6, "hello")),
            "snimpyIndexFixedLen": ((104, 101, 108, 108, 111, 49, 49, 111), (6, "hello1")),
            "snimpyIndexImplied": ((104, 101, 108, 108, 111, 50), (6, "hello2")),
            "snimpyComplexFirstIP": ((15, 15, 16, 100, 23, 74, 87), (4, "15.15.16.100")),
            "snimpySimpleIndex": ((17, 19, 20), (1, 17)),
            }
        for t in tt:
            self.assertEqual(mib.get("SNIMPY-MIB", t).type.fromOid(
                    mib.get("SNIMPY-MIB", t), tt[t][0]),
                             tt[t][1])
        # Test if too short
        tt = {"snimpyComplexFirstIP": (17, 19, 20),
              "snimpyIndexFixedLen": (104, 101, 108),
              "snimpyIndexVarLen": (6, 102, 103, 104, 105),
              }
        for t in tt:
            self.assertRaises(ValueError,
                              mib.get("SNIMPY-MIB", t).type.fromOid,
                              mib.get("SNIMPY-MIB", t), tt[t])

    def testDisplay(self):
        """Test string transformation"""
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          18).display(), "0.18")
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          8).display(), "0.08")
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          288).display(), "2.88")
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          28801).display(), "288.01")
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyString",
                                          "test").display(), "test")
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyString",
                                          "tes\x05").display(), "0x74 65 73 05")
        a = basictypes.build("SNIMPY-MIB",
                             "snimpyString",
                             "test")
        self.assertEqual(a._display("255a"), "test")
        self.assertEqual(a._display("1x:"), "74:65:73:74")
        self.assertEqual(a._display("2a:"), "te:st")
        self.assertEqual(a._display("3a:"), "tes:t")
        self.assertEqual(a._display("4a"), "test")
        self.assertEqual(a._display("2o+1a"), "072145+st")
        a.set("\x03testtest...")
        self.assertEqual(a._display("*2a:+255a"), "te:st:te+st...")

    def testRepr(self):
        """Test representation"""
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyInteger",
                                               18)), "<Integer: 0.18>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyObjectId",
                                               (1, 3, 6, 1, 4, 1, 45, 3, 52, 1))),
                              "<Oid: 1.3.6.1.4.1.45.3.52.1>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyIpAddress",
                                               "124.24.14.3")),
                              "<IpAddress: 124.24.14.3>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyString",
                                               "45754dfgf")),
                              "<String: 45754dfgf>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyEnum",
                                               2)),
                              "<Enum: down(2)>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyBoolean",
                                               False)),
                              "<Boolean: false(2)>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyCounter",
                                               4547)),
                              "<Integer: 4547>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyBits",
                                               ["first", "second"])),
                              "<Bits: first(0), second(1)>")
