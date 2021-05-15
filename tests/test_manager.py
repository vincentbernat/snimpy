import os
import time
from datetime import timedelta
from snimpy.manager import load, Manager, snmp
import agent
import unittest


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
        self.manager = Manager(host="127.0.0.1:{}".format(self.agent.port),
                               community="public",
                               version=2)
        self.session = self.manager._session


class TestManagerGet(TestManager):

    """Test getting stuff from manager"""

    def testGetScalar(self):
        """Retrieve some simple scalar values"""
        self.assertEqual(self.manager.sysDescr, "Snimpy Test Agent public")
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
        self.scalarGetAndCheck("snimpyBits", ["first", "third", "secondByte"])

    def testScalar_MacAddress(self):
        """Retrieve MacAddress as a scalar"""
        self.scalarGetAndCheck("snimpyMacAddress", "11:12:13:14:15:16")

    def testContains_IfDescr(self):
        """Test proxy column membership checking code"""
        self.assertEqual(2 in self.manager.ifDescr,
                         True)
        # FIXME: this currently fails under TestManagerWithNone
        # self.assertEqual(10 in self.manager.ifDescr,
        #                 False)

    def testWalkIfDescr(self):
        """Test we can walk IF-MIB::ifDescr and IF-MIB::ifTpe"""
        results = [(idx, self.manager.ifDescr[idx], self.manager.ifType[idx])
                   for idx in self.manager.ifIndex]
        self.assertEqual(results,
                         [(1, "lo", 24),
                          (2, "eth0", 6),
                          (3, "eth1", 6)])

    def testWalkIfTable(self):
        """Test we can walk IF-MIB::ifTable"""
        results = [(idx, self.manager.ifDescr[idx], self.manager.ifType[idx])
                   for idx in self.manager.ifTable]
        self.assertEqual(results,
                         [(1, "lo", 24),
                          (2, "eth0", 6),
                          (3, "eth1", 6)])

    def testWalkNotAccessible(self):
        """Test we can walk a table with the first entry not accessible."""
        list(self.manager.ifRcvAddressTable)

    def testWalkIfDescrWithoutBulk(self):
        """Walk IF-MIB::ifDescr without GETBULK"""
        self.session.bulk = False
        self.testWalkIfDescr()

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

    def testWalkTableWithComplexIndexes(self):
        """Test if we can walk a table with complex indexes"""
        results = [(idx, self.manager.snimpyIndexInt[idx])
                   for idx in self.manager.snimpyIndexTable]
        self.assertEqual(results,
                         [(("row1", (1, 2, 3),
                            "alpha5", "end of row1"), 4571),
                          (("row2", (1, 0, 2, 3),
                            "beta32", "end of row2"), 78741),
                          (("row3", (120, 1, 2, 3),
                            "gamma7", "end of row3"), 4110)])

    def testWalkReuseIndexes(self):
        """Test if we can walk a table with re-used indexes"""
        results = [(idx, self.manager.snimpyReuseIndexValue[idx])
                   for idx in self.manager.snimpyReuseIndexValue]
        self.assertEqual(results,
                         [(("end of row1", 4), 1785),
                          (("end of row1", 5), 2458)])

    def testWalkTableWithReuseIndexes(self):
        """Test if we can walk a table with re-used indexes"""
        results = [(idx, self.manager.snimpyReuseIndexValue[idx])
                   for idx in self.manager.snimpyReuseIndexTable]
        self.assertEqual(results,
                         [(("end of row1", 4), 1785),
                          (("end of row1", 5), 2458)])

    def testWalkPartialIndexes(self):
        """Test if we can walk a slice of a table given a partial index"""
        results = [(idx, self.manager.ifRcvAddressType[idx])
                   for idx in self.manager.ifRcvAddressStatus[2]]
        self.assertEqual(results,
                         [((2, "61:62:63:64:65:66"), 1),
                          ((2, "67:68:69:6a:6b:6c"), 1)])
        results = [(idx, self.manager.ifRcvAddressType[idx])
                   for idx in self.manager.ifRcvAddressStatus[(3,)]]
        self.assertEqual(results,
                         [((3, "6d:6e:6f:70:71:72"), 1)])
        results = list(self.manager.ifRcvAddressType.iteritems(3))
        self.assertEqual(results,
                         [((3, "6d:6e:6f:70:71:72"), 1)])
        results = list(self.manager.ifRcvAddressType.items(3))
        self.assertEqual(results,
                         [((3, "6d:6e:6f:70:71:72"), 1)])

    def testWalkInvalidPartialIndexes(self):
        """Try to get a table slice with an incorrect index filter"""
        self.assertRaises(ValueError,
                          lambda: list(
                              self.manager.ifRcvAddressStatus.iteritems(
                                  (3, "6d:6e:6f:70:71:72"))))

    def testContains_Partial(self):
        """Test proxy column membership checking code with partial indexes"""
        self.assertEqual(
                "61:62:63:64:65:66" in self.manager.ifRcvAddressStatus[2],
                True)
        # FIXME: this currently fails under TestManagerWithNone
        # self.assertEqual(
        #        "6d:6e:6f:70:71:72" in self.manager.ifRcvAddressStatus[2],
        #        False)

    def testScalar_MultipleSubscripts(self):
        """Retrieve a scalar value using multiple subscript syntax
        (attr[x][y])"""
        self.assertEqual(self.manager.ifRcvAddressType[2]["67:68:69:6a:6b:6c"],
                         1)

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

    def testAccessEmptyTable(self):
        """Try to walk an empty table"""
        results = [(idx,) for idx in self.manager.snimpyEmptyDescr]
        self.assertEqual(results, [])

    def testAccessNotExistentTable(self):
        """Try to walk a non-existent table"""
        agent2 = agent.TestAgent(emptyTable=False)
        try:
            manager = Manager(host="127.0.0.1:{}".format(agent2.port),
                              community="public",
                              version=2)
            [(idx,) for idx in manager.snimpyEmptyDescr]
        except snmp.SNMPNoSuchObject:
            pass                # That's OK
        else:
            self.assertFalse("should raise SNMPNoSuchObject exception")
        finally:
            agent2.terminate()

    def testGetChangingStuff(self):
        """Get stuff with varying values"""
        initial = self.manager.ifInOctets[2]
        current = self.manager.ifInOctets[2]
        self.assertGreater(current, initial)


class TestManagerRestrictModule(TestManager):

    """Test when we restrict modules to be used by a manager"""

    def testGetSpecificModule(self):
        """Get a scalar from a specific module only"""
        self.assertEqual(self.manager['IF-MIB'].ifNumber, 3)
        self.assertEqual(self.manager['SNMPv2-MIB'].sysDescr,
                         "Snimpy Test Agent public")

    def testGetInexistentModule(self):
        """Get a scalar from a non loaded module"""
        self.assertRaises(KeyError, lambda: self.manager['IF-MIB2'])

    def testGetInexistentScalarFromModule(self):
        """Get a non-existent scalar from a specific module"""
        self.assertRaises(AttributeError,
                          lambda: self.manager['IF-MIB'].sysDescr)


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
        self.scalarSetAndCheck("snimpyBits", ["first", "second", "secondByte"])

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
        self.manager = Manager(host="127.0.0.1:{}".format(self.agent.port),
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
        self.manager = Manager(host="127.0.0.1:{}".format(self.agent.port),
                               community="public",
                               version=2, cache=1)
        self.session = self.manager._session._session

    def testGetChangingStuff(self):
        """Get stuff with varying values"""
        initial = self.manager.ifInOctets[2]
        current = self.manager.ifInOctets[2]
        self.assertEqual(current, initial)

    def testCacheFlush(self):
        """Test cache timeout is working as expected"""
        first1 = self.manager.ifInOctets[1]
        second1 = self.manager.ifInOctets[2]
        third1 = self.manager.ifInOctets[3]
        time.sleep(0.5)
        second2 = self.manager.ifInOctets[2]
        third2 = self.manager.ifInOctets[3]
        self.assertEqual(second1, second2)  # timeout not reached
        self.assertEqual(third1, third2)  # timeout not reached
        time.sleep(1)
        first2 = self.manager.ifInOctets[1]
        self.assertGreater(first2, first1)  # timeout was reached


class TestCachingManagerWithModificatons(TestManager):

    """Test if caching manager works with modifications"""

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{}".format(self.agent.port),
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


class TestManagerInvalidValues(TestManager):

    """Test when the agent is returning invalid values"""

    def testInvalidValue(self):
        """Check if an invalid value raises an exception"""
        self.assertRaises(ValueError,
                          getattr, self.manager,
                          "snimpyMacAddressInvalid")

    def testInvalidValueInTable(self):
        """Check if an invalid value in a table raises an exception"""
        self.assertRaises(ValueError,
                          self.manager.snimpyInvalidDescr.__getitem__,
                          2)

    def testInvalidValueWhileIterating(self):
        """Check if an invalid value while walking raises an exception"""
        self.assertRaises(ValueError,
                          list,
                          self.manager.snimpyInvalidDescr.iteritems())


class TestManagerLoose(TestManager):

    """Test when the agent is returning invalid values with loose mode"""

    def setUp(self):
        self.manager = Manager(host="127.0.0.1:{}".format(self.agent.port),
                               community="public",
                               version=2, loose=True)
        self.session = self.manager._session

    def testInvalidValue(self):
        """Check if an invalid value is correctly returned"""
        self.assertEqual(self.manager.snimpyMacAddressInvalid,
                         b"\xf1\x12\x13\x14\x15\x16")

    def testInvalidValueInTable(self):
        """Check if an invalid value in a table is correctly returned"""
        self.assertEqual(self.manager.snimpyInvalidDescr[1],
                         "Hello")
        self.assertEqual(self.manager.snimpyInvalidDescr[2],
                         b"\xf1\x12\x13\x14\x15\x16")

    def testInvalidValueWhileIterating(self):
        """Check if an invalid value while walking works"""
        self.assertEqual(list(self.manager.snimpyInvalidDescr.iteritems()),
                         [(1, "Hello"),
                          (2, b"\xf1\x12\x13\x14\x15\x16")])
