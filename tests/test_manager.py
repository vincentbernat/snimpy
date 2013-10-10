import unittest
import os
import time
from datetime import timedelta
from snimpy.manager import load, Manager, snmp
import agent


class TestManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load('IF-MIB')
        load('SNMPv2-MIB')
        load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "SNIMPY-MIB.mib"))
        cls.agent = agent.TestAgent()

    @classmethod
    def tearDownClass(cls):
        cls.agent.terminate()

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{0}".format(self.agent.port),
                               community="public",
                               version=2)
        self.session = self.manager._session


class TestManagerGet(TestManager):

    """Test getting stuff from manager"""

    def testGetScalar(self):
        """Retrieve some simple scalar values"""
        self.assertEqual(self.manager.sysDescr, "Snimpy Test Agent")
        self.assertEqual(self.manager.ifNumber, 3)

    def scalarGetAndCheck(self, name, value):
        self.assertEqual(getattr(self.manager, name),
                         value)

    def testScalar_IpAddress(self):
        """Retrieve IpAdress as a scalar"""
        self.scalarGetAndCheck("snimpyIpAddress", "65.65.65.65")

    def testScalar_String(self):
        """Retrieve a String as a scalar"""
        self.scalarGetAndCheck("snimpyString", "bye")

    def testScalar_Integer(self):
        """Retrieve an Integer as a scalar"""
        self.scalarGetAndCheck("snimpyInteger", 19)

    def testScalar_Enum(self):
        """Retrieve an Enum as a scalar"""
        self.scalarGetAndCheck("snimpyEnum", "down")

    def testScalar_ObjectId(self):
        """Retrieve an ObjectId as a scalar"""
        self.scalarGetAndCheck("snimpyObjectId", (1, 3, 6, 4454, 0, 0))

    def testScalar_Boolean(self):
        """Retrieve a Boolean as a scalar"""
        self.scalarGetAndCheck("snimpyBoolean", True)

    def testScalar_Counter(self):
        """Retrieve a Counter as a scalar"""
        self.scalarGetAndCheck("snimpyCounter", 47)
        self.scalarGetAndCheck("snimpyCounter64", 2 ** 48 + 3)

    def testScalar_Gauge(self):
        """Retrieve a Gauge as a scalar"""
        self.scalarGetAndCheck("snimpyGauge", 18)

    def testScalar_Timeticks(self):
        """Retrieve a TimeTicks as a scalar"""
        self.scalarGetAndCheck(
            "snimpyTimeticks",
            timedelta(days=1,
                      hours=9,
                      minutes=38,
                      seconds=31))

    def testScalar_Bits(self):
        """Retrieve Bits as a scalar"""
        self.scalarGetAndCheck("snimpyBits", ["first", "third"])

    def testScalar_MacAddress(self):
        """Retrieve MacAddress as a scalar"""
        self.scalarGetAndCheck("snimpyMacAddress", "11:12:13:14:15:16")

    def testWalkIfTable(self):
        """Test we can walk IF-MIB::ifTable"""
        results = [(idx, self.manager.ifDescr[idx], self.manager.ifType[idx])
                   for idx in self.manager.ifIndex]
        self.assertEqual(results,
                         [(1, "lo", 24),
                          (2, "eth0", 6),
                          (3, "eth1", 6)])

    def testWalkIfTableWithoutBulk(self):
        """Walk IF-MIB::ifTable without GETBULK"""
        self.session.bulk = False
        self.testWalkIfTable()

    def testWalkComplexIndexes(self):
        """Test if we can walk a table with complex indexes"""
        results = [(idx, self.manager.snimpyIndexInt[idx])
                   for idx in self.manager.snimpyIndexInt]
        self.assertEqual(results,
                         [(("row1", (1, 2, 3),
                            "alpha5", "end of row1"), 4571),
                          (("row2", (1, 0, 2, 3),
                            "beta32", "end of row2"), 78741),
                          (("row3", (120, 1, 2, 3),
                            "gamma7", "end of row3"), 4110)])

    def testGetInexistentStuff(self):
        """Try to access stuff that does not exist on the agent"""
        self.assertRaises(snmp.SNMPNoSuchObject,
                          getattr, self.manager, "snimpyNotImplemented")
        self.assertRaises(snmp.SNMPNoSuchObject,
                          self.manager.ifName.__getitem__, 47)
        self.assertRaises(snmp.SNMPNoSuchInstance,
                          self.manager.ifDescr.__getitem__, 47)

    def testAccessInexistentStuff(self):
        """Try to access stuff that don't exist in MIB"""
        self.assertRaises(AttributeError,
                          getattr, self.manager, "iDoNotExist")

    def testAccessIncorrectIndex(self):
        """Try to access with incorrect indexes"""
        self.assertRaises(ValueError,
                          self.manager.ifDescr.__getitem__, (47, 18))
        self.assertRaises(ValueError,
                          self.manager.ifDescr.__getitem__, "nothing")


class TestManagerSet(TestManager):

    """Test setting stuff from manager"""

    def testSetScalar(self):
        """Try to set a simple value"""
        self.manager.snimpyString = "hello"
        self.assertEqual(self.manager.snimpyString, "hello")

    def scalarSetAndCheck(self, name, value):
        setattr(self.manager, name, value)
        self.assertEqual(getattr(self.manager, name),
                         value)

    def testScalar_IpAddress(self):
        """Retrieve IpAdress as a scalar"""
        self.scalarSetAndCheck("snimpyIpAddress", "165.255.65.65")

    def testScalar_String(self):
        """Retrieve a String as a scalar"""
        self.scalarSetAndCheck("snimpyString", "awesome !!!")

    def testScalar_Integer(self):
        """Retrieve an Integer as a scalar"""
        self.scalarSetAndCheck("snimpyInteger", 1900)

    def testScalar_Enum(self):
        """Retrieve an Enum as a scalar"""
        self.scalarSetAndCheck("snimpyEnum", "up")

    def testScalar_ObjectId(self):
        """Retrieve an ObjectId as a scalar"""
        self.scalarSetAndCheck("snimpyObjectId", (1, 3, 6, 4454, 19, 47))

    def testScalar_Boolean(self):
        """Retrieve a Boolean as a scalar"""
        self.scalarSetAndCheck("snimpyBoolean", False)

    def testScalar_Counter(self):
        """Retrieve a Counter as a scalar"""
        self.scalarSetAndCheck("snimpyCounter", 4700)
        self.scalarSetAndCheck("snimpyCounter64", 2 ** 48 + 3 - 18)

    def testScalar_Gauge(self):
        """Retrieve a Gauge as a scalar"""
        self.scalarSetAndCheck("snimpyGauge", 180014)

    def testScalar_Timeticks(self):
        """Retrieve a TimeTicks as a scalar"""
        self.scalarSetAndCheck(
            "snimpyTimeticks",
            timedelta(days=1,
                      hours=17,
                      minutes=38,
                      seconds=31))

    def testScalar_Bits(self):
        """Retrieve Bits as a scalar"""
        self.scalarSetAndCheck("snimpyBits", ["first", "second"])

    def testScalar_MacAddress(self):
        """Retrieve MAC address as a scala"""
        self.scalarSetAndCheck("snimpyMacAddress", "a0:b0:c0:d0:e:ff")

    def testNonScalarSet(self):
        """Check we can set a non-scalar value"""
        idx = ("row2", (1, 0, 2, 3), "beta32", "end of row2")
        self.manager.snimpyIndexInt[idx] = 1041
        self.assertEqual(self.manager.snimpyIndexInt[idx], 1041)

    def testSetWithContext(self):
        """Set several values atomically (inside a context)"""
        with self.manager as m:
            m.snimpyString = "Noooooo!"
            m.snimpyInteger = 42
        self.assertEqual(m.snimpyString, "Noooooo!")
        self.assertEqual(m.snimpyInteger, 42)

    def testSetWithContextAndAbort(self):
        """Check if writing several values atomically can be aborted"""
        try:
            with self.manager as m:
                m.snimpyString = "Abort sir!"
                m.snimpyInteger = 37
                raise RuntimeError("Abort now!")
        except RuntimeError as e:
            self.assertEqual(str(e), "Abort now!")
        self.assertNotEqual(m.snimpyString, "Abort sir!")
        self.assertNotEqual(m.snimpyInteger, 37)

    def testSetInexistentStuff(self):
        """Try to access stuff that does not exist on the agent"""
        self.assertRaises(snmp.SNMPNotWritable,
                          setattr, self.manager, "snimpyNotImplemented",
                          "Hello")
        self.assertRaises(snmp.SNMPNotWritable,
                          self.manager.ifName.__setitem__, 47, "Wouh")
        self.assertRaises(snmp.SNMPNotWritable,
                          self.manager.ifDescr.__setitem__, 47, "Noooo")

    def testAccessInexistentStuff(self):
        """Try to access stuff that don't exist in MIB"""
        self.assertRaises(AttributeError,
                          setattr, self.manager, "iDoNotExist", 47)

    def testAccessIncorrectIndex(self):
        """Try to access with incorrect indexes"""
        self.assertRaises(ValueError,
                          self.manager.ifDescr.__setitem__, (47, 18), "Nooo")
        self.assertRaises(ValueError,
                          self.manager.ifDescr.__setitem__,
                          "nothing", "Neither")


class TestManagerWithNone(TestManagerGet):

    """Test a manager answering None for inexistent stuff"""

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{0}".format(self.agent.port),
                               community="public",
                               version=2, none=True)
        self.session = self.manager._session._session

    def testGetInexistentStuff(self):
        """Try to access stuff that does not exist on the agent"""
        self.assertEqual(self.manager.snimpyNotImplemented, None)
        self.assertEqual(self.manager.ifName[47], None)
        self.assertEqual(self.manager.ifDescr[47], None)


class TestCachingManager(TestManagerGet):

    """Test if caching manager works like regular manager"""

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{0}".format(self.agent.port),
                               community="public",
                               version=2, cache=1)
        self.session = self.manager._session._session


class TestCachingManagerWithModificatons(TestManager):

    """Test if caching manager works with modifications"""

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{0}".format(self.agent.port),
                               community="public",
                               version=2, cache=1)
        self.session = self.manager._session._session

    def testCacheScalar(self):
        """Check that a scalar value is kept in cache"""
        original = self.manager.snimpyString
        self.manager.snimpyString = "Nooooo"
        self.assertEqual(self.manager.snimpyString, original)

    def testCacheNonScalar(self):
        """Check we can cache a non-scalar value"""
        idx = ("row2", (1, 0, 2, 3), "beta32", "end of row2")
        original = self.manager.snimpyIndexInt[idx]
        self.manager.snimpyIndexInt[idx] = 1041
        self.assertEqual(self.manager.snimpyIndexInt[idx], original)

    def testCacheExpire(self):
        """Check the cache can expire"""
        self.manager.snimpyString = "Yeesss"
        time.sleep(1)
        self.assertEqual(self.manager.snimpyString, "Yeesss")
