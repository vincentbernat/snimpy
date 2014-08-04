import unittest
import os
import re
import socket
import mock
from datetime import timedelta
from snimpy import mib, basictypes
from pysnmp.proto import rfc1902


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
        self.assertEqual(a + 10, 28)
        a = basictypes.build("SNIMPY-MIB", "snimpyInteger", 4)
        self.assertEqual(a, 4)
        self.assertEqual(a * 4, 16)
        a = basictypes.build("SNIMPY-MIB", "snimpyInteger", 5)
        self.assertEqual(a, 5)
        self.assert_(a < 6)
        # self.assert_(a > 4.6) # type coercion does not work
        self.assert_(a > 4)
        self.assertRaises(TypeError,
                          basictypes.build, ("SNIMPY-MIB",
                                             "snimpyInteger", [1, 2, 3]))

    def testString(self):
        """Test string basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", b"hello")
        self.assert_(isinstance(a, basictypes.String))
        self.assertEqual(a, "hello")
        self.assertEqual(a + " john", "hello john")
        self.assertEqual(a * 2, "hellohello")
        a = basictypes.build("SNIMPY-MIB", "snimpyString", b"hello john")
        self.assert_("john" in a)
        self.assert_("steve" not in a)
        self.assertEqual(a[1], 'e')
        self.assertEqual(a[1:4], 'ell')
        self.assertEqual(len(a), 10)

    def testStringFromBytes(self):
        """Test string basic type when built from bytes"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", b"hello")
        self.assert_(isinstance(a, basictypes.String))
        self.assertEqual(a, "hello")
        self.assertEqual(a + " john", "hello john")
        self.assertEqual(a * 2, "hellohello")

    def testStringEncoding(self):
        """Test we can create an UTF-8 encoded string"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", u"hello")
        self.assertEqual(a, u"hello")
        self.assertEqual(a, "hello")
        a = basictypes.build(
            "SNIMPY-MIB",
            "snimpyUnicodeString",
            u"\U0001F60E Hello")
        self.assertEqual(a, u"\U0001F60E Hello")
        a = basictypes.build(
            "SNIMPY-MIB",
            "snimpyUnicodeString",
            b'\xf0\x9f\x98\x8e Hello')
        self.assertEqual(a, u"\U0001F60E Hello")
        self.assertRaises(UnicodeError,
                          basictypes.build, "SNIMPY-MIB", "snimpyString",
                          b'\xf0\x9f\x98\x8e Hello')

    def testOctetString(self):
        """Test octet string basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyOctetString", b"hello\x41")
        self.assert_(isinstance(a, basictypes.OctetString))
        self.assertEqual(a, b"hello\x41")
        self.assertEqual(len(a), 6)

    def testIpAddress(self):
        """Test IP address basic type"""
        a = basictypes.build(
            "SNIMPY-MIB",
            "snimpyIpAddress",
            socket.inet_aton("10.0.4.5"))
        self.assert_(isinstance(a, basictypes.IpAddress))
        self.assertEqual(a, "10.0.4.5")
        self.assertEqual(a, "10.00.4.05")
        self.assertEqual(a, [10, 0, 4, 5])
        self.assertEqual(a[2], 4)
        self.assert_(a < "10.1.2.4")
        self.assert_(a > "10.0.0.1")
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", [1, 2, 3, 5])
        self.assertEqual(a, "1.2.3.5")
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", "10.0.4.5")
        self.assertEqual(a, "10.0.4.5")
        self.assertEqual(a, [10, 0, 4, 5])
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", b"1001")
        self.assertEqual(a, [49, 48, 48, 49])
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", b"0101")
        self.assertEqual(a, [48, 49, 48, 49])
        a = basictypes.build("SNIMPY-MIB", "snimpyIpAddress", "100")
        self.assertEqual(a, [0, 0, 0, 100])

    def testIncorrectIpAddress(self):
        """Test inappropriate IP addresses"""
        self.assertRaises(ValueError,
                          basictypes.build,
                          "SNIMPY-MIB", "snimpyIpAddress", "999.5.6.4")
        self.assertRaises(ValueError,
                          basictypes.build,
                          "SNIMPY-MIB", "snimpyIpAddress", "AAA")
        self.assertRaises(ValueError,
                          basictypes.build,
                          "SNIMPY-MIB", "snimpyIpAddress", "AAACC")

    def testEnum(self):
        """Test enum basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyEnum", 1)
        self.assert_(isinstance(a, basictypes.Enum))
        self.assertEqual(a, 1)
        self.assertEqual(a, "up")
        a = basictypes.build("SNIMPY-MIB", "snimpyEnum", "down")
        self.assertEqual(a, "down")
        self.assert_(a != "up")
        self.assertEqual(a, 2)
        self.assertEqual(str(a), "down(2)")
        self.assertRaises(ValueError,
                          basictypes.build,
                          "SNIMPY-MIB", "snimpyEnum", "unknown")
        self.assertEqual(str(a), "down(2)")
        a = basictypes.build("SNIMPY-MIB", "snimpyEnum", 54)
        self.assertEqual(a, 54)

    def testOid(self):
        """Test OID basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyObjectId",
                             mib.get("SNIMPY-MIB", "snimpyInteger"))
        self.assert_(isinstance(a, basictypes.Oid))
        self.assertEqual(a, mib.get("SNIMPY-MIB", "snimpyInteger"))
        self.assertEqual(a, mib.get("SNIMPY-MIB", "snimpyInteger").oid)
        # Suboid
        self.assert_((list(mib.get("SNIMPY-MIB",
                                   "snimpyInteger").oid) + [2, 3]) in a)
        self.assert_((list(mib.get("SNIMPY-MIB",
                                   "snimpyInteger").oid)[:-1] +
                      [29, 3]) not in a)
        # Also accepts list
        a = basictypes.build("SNIMPY-MIB", "snimpyObjectId",
                             (1, 2, 3, 4))
        self.assertEqual(a, (1, 2, 3, 4))
        self.assert_((1, 2, 3, 4, 5) in a)
        self.assert_((3, 4, 5, 6) not in a)

    def testBoolean(self):
        """Test boolean basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyBoolean", True)
        self.assert_(isinstance(a, basictypes.Boolean))
        self.assertEqual(a, True)
        self.assert_(a)
        self.assert_(not(not(a)))
        self.assertEqual(not(a), False)
        a = basictypes.build("SNIMPY-MIB", "snimpyBoolean", "false")
        self.assertEqual(a, False)
        b = basictypes.build("SNIMPY-MIB", "snimpyBoolean", True)
        self.assertEqual(a or b, True)
        self.assertEqual(a and b, False)

    def testTimeticks(self):
        """Test timeticks basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyTimeticks", 676544)
        self.assert_(isinstance(a, basictypes.Timeticks))
        # We can compare to int but otherwise, this is a timedelta
        self.assertEqual(a, 676544)
        self.assertEqual(str(a), '1:52:45.440000')
        self.assertEqual(a, timedelta(0, 6765, 440000))
        a = basictypes.build("SNIMPY-MIB", "snimpyTimeticks",
                             timedelta(1, 3))
        self.assertEqual(str(a), '1 day, 0:00:03')
        self.assertEqual(a, (3 + 3600 * 24) * 100)
        self.assert_(a != (3 + 3600 * 24) * 100 + 1)
        self.assert_(a < timedelta(1, 4))
        self.assert_(a > timedelta(1, 1))
        self.assert_(a > 654)
        self.assert_(a >= 654)
        self.assert_(a < (3 + 3600 * 24) * 100 + 2)
        self.assertEqual(a,
                         basictypes.build("SNIMPY-MIB", "snimpyTimeticks",
                                          timedelta(1, 3)))
        self.assert_(a < basictypes.build("SNIMPY-MIB", "snimpyTimeticks",
                                          timedelta(100, 30)))

    def testBits(self):
        """Test bit basic type"""
        a = basictypes.build("SNIMPY-MIB", "snimpyBits", [1, 2])
        self.assert_(isinstance(a, basictypes.Bits))
        self.assertEqual(a, [2, 1])
        self.assertEqual(a, (1, 2))
        self.assertEqual(a, set([1, 2]))
        self.assertEqual(a, ["second", "third"])
        self.assertEqual(a, set(["second", "third"]))
        self.assertEqual(a, ["second", 2])
        self.assert_(a != ["second"])
        self.assertFalse(a == ["second"])
        self.assertFalse(a != ["second", 2])
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
        self.assertEqual(a & set(["last", 2]), True)
        self.assertEqual(a & ["last", 0], True)
        self.assertEqual(a & ["second", 0], False)
        a = basictypes.build("SNIMPY-MIB", "snimpyBits",
                             set(["first", "second"]))
        self.assertEqual(a, [0, 1])
        a = basictypes.build("SNIMPY-MIB", "snimpyBits", [])
        self.assertEqual(a, [])
        self.assertEqual(str(a), "")

    def testInexistentBits(self):
        """Check we cannot set inexistent bits"""
        a = basictypes.build("SNIMPY-MIB", "snimpyBits", [1, 2])
        self.assert_(a & 1)

        def nope(a):
            a |= 3
        self.assertRaises(ValueError, nope, a)

    def testStringAsBits(self):
        """Test using bit specific operator with string"""
        a = basictypes.build(
            "SNIMPY-MIB",
            "snimpyOctetString",
            b"\x17\x00\x01")
        self.assert_(isinstance(a, basictypes.OctetString))
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
        self.assertEqual(a, b"\x37\x20\x00")
        a |= 31
        self.assertEqual(a, b"\x37\x20\x00\x01")

    def testPacking(self):
        """Test pack() function"""
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyString",
                                          "Hello world").pack(),
                         rfc1902.OctetString("Hello world"))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          18).pack(),
                         rfc1902.Integer(18))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyInteger",
                                          1804).pack(),
                         rfc1902.Integer(1804))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyEnum",
                                          "testing").pack(),
                         rfc1902.Integer(3))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyIpAddress",
                                          "10.11.12.13").pack(),
                         rfc1902.IpAddress("10.11.12.13"))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyObjectId",
                                          (1, 2, 3, 4)).pack(),
                         rfc1902.univ.ObjectIdentifier((1, 2, 3, 4)))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyTimeticks",
                                          timedelta(3, 2)).pack(),
                         rfc1902.TimeTicks(3 * 3600 * 24 * 100 + 2 * 100))
        self.assertEqual(basictypes.build("SNIMPY-MIB",
                                          "snimpyBits",
                                          [1, 7]).pack(),
                         rfc1902.Bits(b"\x41"))

    def testOidConversion(self):
        """Test conversion to/from OID."""
        tt = {("snimpySimpleIndex", 47): (47,),
              ("snimpyComplexFirstIP", "10.14.15.4"): (10, 14, 15, 4),
              ("snimpyComplexSecondIP", (14, 15, 16, 17)): (14, 15, 16, 17),
              ("snimpyIndexOidVarLen", (47, 48, 49)): (3, 47, 48, 49),
              ("snimpyIndexVarLen", "hello1"): tuple([len("hello1")] +
                                                     [ord(a)
                                                      for a in "hello1"]),
              ("snimpyIndexFixedLen", "hello2"): tuple(ord(a)
                                                       for a in "hello2"),
              ("snimpyIndexImplied", "hello3"): tuple(ord(a)
                                                      for a in "hello3"),
              }
        for t, v in tt:
            oid = basictypes.build("SNIMPY-MIB",
                                   t,
                                   v).toOid()
            self.assertEqual(oid,
                             tt[t, v])
            # Test double conversion
            self.assertEqual(mib.get("SNIMPY-MIB", t).type.fromOid(
                mib.get("SNIMPY-MIB", t), oid),
                (len(tt[t, v]), v))

    def testTooLargeOid(self):
        """Handle the special case of octet string as OID with too large octets.

        See: https://github.com/vincentbernat/snimpy/pull/14
        """
        self.assertEqual(mib.get("SNIMPY-MIB",
                                 "snimpyIndexImplied").type.fromOid(
                                     mib.get("SNIMPY-MIB",
                                             "snimpyIndexImplied"),
                                     (104, 0xff00 | 101, 108, 108, 111)),
                         (5, basictypes.build("SNIMPY-MIB",
                                              "snimpyIndexImplied",
                                              "hello")))

    def testOidGreedy(self):
        """Test greediness of fromOid."""
        tt = {
            "snimpyIndexVarLen":
            ((5, 104, 101, 108, 108, 111, 111, 111, 111), (6, "hello")),
            "snimpyIndexFixedLen":
            ((104, 101, 108, 108, 111, 49, 49, 111), (6, "hello1")),
            "snimpyIndexImplied":
            ((104, 101, 108, 108, 111, 50), (6, "hello2")),
            "snimpyComplexFirstIP":
            ((15, 15, 16, 100, 23, 74, 87), (4, "15.15.16.100")),
            "snimpySimpleIndex": ((17, 19, 20), (1, 17)),
            "snimpyIndexOidVarLen": ((3, 247, 145, 475568, 475, 263),
                                     (4, (247, 145, 475568))),
        }
        for t in tt:
            self.assertEqual(mib.get("SNIMPY-MIB", t).type.fromOid(
                mib.get("SNIMPY-MIB", t), tt[t][0]),
                tt[t][1])
        # Test if too short
        tt = {"snimpyComplexFirstIP": (17, 19, 20),
              "snimpyIndexFixedLen": (104, 101, 108),
              "snimpyIndexVarLen": (6, 102, 103, 104, 105),
              "snimpyIndexOidVarLen": (3, 247, 145),
              }
        for t in tt:
            self.assertRaises(ValueError,
                              mib.get("SNIMPY-MIB", t).type.fromOid,
                              mib.get("SNIMPY-MIB", t), tt[t])

    def testDisplay(self):
        """Test string transformation"""
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyInteger",
                                              18)), "0.18")
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyInteger",
                                              8)), "0.08")
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyInteger",
                                              288)), "2.88")
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyInteger",
                                              28801)), "288.01")
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyString",
                                              "test")), "test")
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyOctetString",
                                              b"test")), str(b"test"))
        self.assertEqual(str(basictypes.build("SNIMPY-MIB",
                                              "snimpyOctetString",
                                              b"tes\x05")), str(b"tes\x05"))

    def testDisplayFormat(self):
        """Test display some with some formats"""
        with mock.patch("snimpy.mib.Node.fmt",
                        new_callable=mock.PropertyMock) as e:
            e.return_value = "255a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "test")
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"")
            self.assertEqual(str(a), "")
            e.return_value = "1x:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "74:65:73:74")
            e.return_value = "2a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "te:st")
            e.return_value = "3a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "tes:t")
            e.return_value = "4a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "test")
            e.return_value = "2o+1a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(str(a), "072145+st")

            e.return_value = "*2a:+255a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString",
                                 b"\x03testtest...")
            self.assertEqual(str(a), "te:st:te+st...")

            e.return_value = "2a1x:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString",
                                 b"aatest")
            self.assertEqual(str(a), "aa74:65:73:74")

            e.return_value = "*2a+1a:-*3a?="
            a = basictypes.build("SNIMPY-MIB", "snimpyString",
                                 b"\x04testtestZ\x02testes\x03testestes")
            self.assertEqual(str(a), "te+st+te+st+Z-tes?tes=tes?tes?tes")

    def testInputFormat(self):
        """Test we can input a string with a given format"""
        with mock.patch("snimpy.mib.Node.fmt",
                        new_callable=mock.PropertyMock) as e:
            e.return_value = "255a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"test")
            self.assertEqual(a.pack(), b"test")
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"")
            self.assertEqual(a.pack(), b"")
            e.return_value = "1x:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"74:65:73:74")
            self.assertEqual(a.pack(), b"test")
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"74:6:73:4")
            self.assertEqual(a.pack(), b"t\x06s\x04")
            e.return_value = "2a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"te:st")
            self.assertEqual(a.pack(), b"test")
            e.return_value = "3a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"tes:t")
            self.assertEqual(a.pack(), b"test")
            e.return_value = "4a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"test")
            self.assertEqual(a.pack(), b"test")
            e.return_value = "2o+1a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", u"072145+st")
            self.assertEqual(a.pack(), b"test")

            e.return_value = "*2a:+255a"
            a = basictypes.build(
                "SNIMPY-MIB",
                "snimpyString",
                u"te:st:te+st...")
            self.assertEqual(a.pack(), b"\x03testtest...")

            e.return_value = "2a1x:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString",
                                 u"aa74:65:73:74")
            self.assertEqual(a.pack(), b"aatest")

            e.return_value = "*2a+@1a:-*3a?="
            a = basictypes.build("SNIMPY-MIB", "snimpyString",
                                 u"te+st+te+st@Z-tes?tes=tes?tes?tes")
            self.assertEqual(a.pack(), b"\x04testtestZ\x02testes\x03testestes")

    def testRepr(self):
        """Test representation"""
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyInteger",
                                               18)), "<Integer: 0.18>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyObjectId",
                                               (1, 3, 6, 1, 4, 1,
                                                45, 3, 52, 1))),
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
                         "<Unsigned32: 4547>")
        self.assertEqual(repr(basictypes.build("SNIMPY-MIB",
                                               "snimpyBits",
                                               ["first", "second"])),
                         "<Bits: first(0), second(1)>")

    def testEqualityWithDisplay(self):
        """Test we can check for equality with displayed form"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", "test")
        self.assertEqual(a, "test")

        with mock.patch("snimpy.mib.Node.fmt",
                        new_callable=mock.PropertyMock) as e:
            e.return_value = "255a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "test")

            e.return_value = "1x:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "74:65:73:74")

            e.return_value = "2a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "te:st")

            e.return_value = "3a:"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "tes:t")

            e.return_value = "4a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "test")

            e.return_value = "2o+1a"
            a = basictypes.build("SNIMPY-MIB", "snimpyString", b"test")
            self.assertEqual(a, "072145+st")
            self.assertNotEqual(a, "072145+sta")
            self.assertFalse(a != "072145+st")

            e.return_value = "*2a:+255a"
            a = basictypes.build("SNIMPY-MIB",
                                 "snimpyString",
                                 b"\x03testtest...")
            self.assertEqual(a, "te:st:te+st...")

    def testEqualityUnicode(self):
        """Test that equality works for both unicode and bytes"""
        a = basictypes.build("SNIMPY-MIB", "snimpyString", "test")
        self.assertEqual(a, "test")
        a = basictypes.build("SNIMPY-MIB", "snimpyString", "test")
        self.assertEqual(a, u"test")

    def testLikeAString(self):
        """Test String is like str"""
        a = basictypes.build("SNIMPY-MIB",
                             "snimpyString",
                             "4521dgf")
        self.assert_(a.startswith("4521"))
        self.assertEqual(a.upper(), "4521DGF")
        self.assert_(re.match("[0-9]+[defg]+", a))
