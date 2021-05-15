import unittest
import os
import threading
import multiprocessing
import platform
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

    def testRepresentation(self):
        """Test session representation"""
        s = snmp.Session(host="localhost",
                         community="public",
                         version=1)
        self.assertEqual(repr(s), "Session(host=localhost,version=1)")

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
    def addAgent(cls, community, auth, priv):
        a = agent.TestAgent(community=community,
                            authpass=auth,
                            privpass=priv)
        cls.agents.append(a)
        return a

    @classmethod
    def setUpClass(cls):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')
        cls.agents = []
        cls.agent = cls.addAgent('public',
                                 'public-authpass', 'public-privpass')

    def setUp(self):
        params = self.setUpSession(self.agent, 'public')
        self.session = snmp.Session(**params)

    def setUpSession(self, agent, password):
        return dict(host="127.0.0.1:{}".format(agent.port),
                    community=password,
                    version=self.version)

    @classmethod
    def tearDownClass(cls):
        for a in cls.agents:
            a.terminate()

    def testGetString(self):
        """Get a string value"""
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid, a = self.session.get(ooid)[0]
        self.assertEqual(oid, ooid)
        self.assertEqual(a, b"Snimpy Test Agent public")

    def testGetInteger(self):
        """Get an integer value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifNumber').oid + (0,))[0]
        self.assertTrue(a > 1)     # At least lo and another interface

    def testGetEnum(self):
        """Get an enum value"""
        oid, a = self.session.get(mib.get('IF-MIB', 'ifType').oid + (1,))[0]
        self.assertEqual(a, 24)  # This is software loopback
        b = basictypes.build('IF-MIB', 'ifType', a)
        self.assertEqual(b, "softwareLoopback")

    def testGetMacAddress(self):
        """Get a MAC address"""
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))
        oid, a = self.session.get((1, 3, 6, 1, 2, 1, 45121, 1, 15, 0))[0]
        self.assertEqual(a, b"\x11\x12\x13\x14\x15\x16")
        b = basictypes.build('SNIMPY-MIB', 'snimpyMacAddress', a)
        self.assertEqual(b, "11:12:13:14:15:16")

    def testGetObjectId(self):
        """Get ObjectId."""
        ooid = mib.get('SNMPv2-MIB', 'sysObjectID').oid + (0,)
        oid, a = self.session.get(ooid)[0]
        self.assertEqual(oid, ooid)
        self.assertEqual(a, (1, 3, 6, 1, 4, 1, 9, 1, 1208))

    def testInexistant(self):
        """Get an inexistant value"""
        try:
            self.session.get((1, 2, 3))
            self.assertFalse("we should have got an exception")
        except snmp.SNMPException as ex:
            self.assertTrue(isinstance(ex, snmp.SNMPNoSuchName) or
                            isinstance(ex, snmp.SNMPNoSuchObject))

    def testSetIpAddress(self):
        """Set IpAddress."""
        self.setAndCheck('snimpyIpAddress', '10.14.12.12')

    def testSetString(self):
        """Set String."""
        self.setAndCheck('snimpyString', 'hello')

    def testSetInteger(self):
        """Set Integer."""
        self.setAndCheck('snimpyInteger', 1574512)

    def testSetEnum(self):
        """Set Enum."""
        self.setAndCheck('snimpyEnum', 'testing')

    def testSetObjectId(self):
        """Set ObjectId."""
        self.setAndCheck('snimpyObjectId', (1, 2, 3, 4, 5, 6))

    def testSetCounter(self):
        """Set Counter."""
        self.setAndCheck('snimpyCounter', 545424)

    def testSetGauge(self):
        """Set Gauge."""
        self.setAndCheck('snimpyGauge', 4857544)

    def testSetBoolean(self):
        """Set Boolean."""
        self.setAndCheck('snimpyBoolean', True)

    def testSetTimeticks(self):
        """Set Timeticks."""
        self.setAndCheck('snimpyTimeticks', timedelta(3, 18))

    def testSetBits(self):
        """Set Bits."""
        self.setAndCheck('snimpyBits', ["third", "last"])

    def testSetMacAddress(self):
        """Set a MAC address."""
        self.setAndCheck('snimpyMacAddress', "a0:b0:c0:d0:e:ff")
        oid, a = self.session.get((1, 3, 6, 1, 2, 1, 45121, 1, 15, 0))[0]
        # This is software loopback
        self.assertEqual(a, b"\xa0\xb0\xc0\xd0\x0e\xff")

    def setAndCheck(self, oid, value):
        """Set and check a value"""
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))
        ooid = mib.get('SNIMPY-MIB', oid).oid + (0,)
        self.session.set(ooid,
                         basictypes.build('SNIMPY-MIB', oid, value))
        self.assertEqual(
            basictypes.build('SNIMPY-MIB', oid, self.session.get(ooid)[0][1]),
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
        self.assertEqual(a1, b"Snimpy Test Agent public")
        self.assertTrue(a2 > 1)
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
        self.assertEqual(tuple(results),
                         ((ooid + (1,), b"lo"),
                          (ooid + (2,), b"eth0"),
                          (ooid + (3,), b"eth1")))

    def testSeveralSessions(self):
        """Test with two sessions"""
        agent2 = self.addAgent('private',
                               'private-authpass', 'private-privpass')
        params = self.setUpSession(agent2, 'private')
        session2 = snmp.Session(**params)

        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
        oid1, a1 = self.session.get(ooid)[0]
        oid2, a2 = session2.get(ooid)[0]
        self.assertEqual(oid1, ooid)
        self.assertEqual(oid2, ooid)
        self.assertEqual(a1, b"Snimpy Test Agent public")
        self.assertEqual(a2, b"Snimpy Test Agent private")

    @unittest.skipIf(platform.python_implementation() == "PyPy",
                     "unreliable test with Pypy")
    def testMultipleThreads(self):
        """Test with multiple sessions in different threads."""
        count = 20
        agents = []
        for i in range(count):
            agents.append(self.addAgent('community{}'.format(i),
                                        'community{}-authpass'.format(i),
                                        'community{}-privpass'.format(i)))
        ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)

        threads = []
        successes = []
        failures = []
        lock = multiprocessing.Lock()

        # Start one thread
        def run(i):
            params = self.setUpSession(agents[i], 'community{}'.format(i))
            session = snmp.Session(**params)
            session.timeout = 10 * 1000 * 1000
            oid, a = session.get(ooid)[0]
            exp = ("Snimpy Test Agent community{}".format(i)).encode('ascii')
            with lock:
                if oid == ooid and \
                   a == exp:
                    successes.append("community{}".format(i))
                else:
                    failures.append("community{}".format(i))
        for i in range(count):
            threads.append(threading.Thread(target=run, args=(i,)))
        for i in range(count):
            threads[i].start()
        for i in range(count):
            threads[i].join()
        self.assertEqual(failures, [])
        self.assertEqual(sorted(successes),
                         sorted(["community{}".format(i)
                                 for i in range(count)]))


class TestSnmp2(TestSnmp1):

    """Test communication with an agent with SNMPv2."""
    version = 2

    def testInexistantNone(self):
        """Get an inexistant value but request none"""
        params = self.setUpSession(self.agent, 'public')
        params['none'] = True
        session = snmp.Session(**params)
        oid, a = session.get((1, 2, 3))[0]
        self.assertEqual(a, None)

    def testSetCounter64(self):
        """Set Counter64."""
        self.setAndCheck('snimpyCounter64', 2 ** 47 + 1)

    def testWalk(self):
        """Check if we can walk"""
        ooid = mib.get("IF-MIB", "ifDescr").oid
        self.session.bulk = 4
        results = self.session.walk(ooid)
        self.assertEqual(tuple(results),
                         ((ooid + (1,), b"lo"),
                          (ooid + (2,), b"eth0"),
                          (ooid + (3,), b"eth1")))
        self.session.bulk = 2
        results = self.session.walk(ooid)
        self.assertEqual(tuple(results),
                         ((ooid + (1,), b"lo"),
                          (ooid + (2,), b"eth0"),
                          (ooid + (3,), b"eth1")))


class TestSnmp3(TestSnmp2):

    """Test communicaton with an agent with SNMPv3."""
    version = 3

    def setUpSession(self, agent, password):
        return dict(host="127.0.0.1:{}".format(agent.port),
                    version=3,
                    secname="read-write",
                    authprotocol="MD5",
                    authpassword="{}-authpass".format(password),
                    privprotocol="AES",
                    privpassword="{}-privpass".format(password))


class TestSnmpTransports(unittest.TestCase):

    """Test communication using IPv6."""
    ipv6 = True

    @classmethod
    def setUpClass(cls):
        mib.load('IF-MIB')
        mib.load('SNMPv2-MIB')

    def _test(self, ipv6, host):
        m = agent.TestAgent(ipv6)
        session = snmp.Session(
            host="{}:{}".format(host, m.port),
            community="public",
            version=2)
        try:
            ooid = mib.get('SNMPv2-MIB', 'sysDescr').oid + (0,)
            oid, a = session.get(ooid)[0]
            self.assertEqual(a, b"Snimpy Test Agent public")
        finally:
            m.terminate()

    def testIpv4(self):
        """Test IPv4 transport"""
        self._test(False, "127.0.0.1")

    def testIpv4WithDNS(self):
        """Test IPv4 transport with name resolution"""
        self._test(False, "localhost")

    def testIpv6(self):
        """Test IPv6 transport"""
        self._test(True, "[::1]")
