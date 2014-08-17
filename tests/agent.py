from multiprocessing import Process, Queue
import random

from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pysnmp.proto.api import v2c


class TestAgent(object):

    """Agent for testing purpose"""

    def __init__(self, ipv6=False):
        q = Queue()
        self.ipv6 = ipv6
        self._process = Process(target=self._setup, args=(q,))
        self._process.start()
        self.port = q.get()

    def terminate(self):
        self._process.terminate()

    def _setup(self, q):
        """Setup a new agent in a separate process.

        The port the agent is listening too will be returned using the
        provided queue.
        """
        port = random.randrange(22000, 22989)
        snmpEngine = engine.SnmpEngine()
        if self.ipv6:
            config.addSocketTransport(
                snmpEngine,
                udp6.domainName,
                udp6.Udp6Transport().openServerMode(('::1', port)))
        else:
            config.addSocketTransport(
                snmpEngine,
                udp.domainName,
                udp.UdpTransport().openServerMode(('127.0.0.1', port)))
        # Community is public and MIB is writable
        config.addV1System(snmpEngine, 'read-write', 'public')
        config.addVacmUser(snmpEngine, 1, 'read-write', 'noAuthNoPriv',
                           (1, 3, 6), (1, 3, 6))
        config.addVacmUser(snmpEngine, 2, 'read-write', 'noAuthNoPriv',
                           (1, 3, 6), (1, 3, 6))
        config.addV3User(
            snmpEngine, 'read-write',
            config.usmHMACMD5AuthProtocol, 'authpass',
            config.usmAesCfb128Protocol, 'privpass'
        )
        config.addVacmUser(snmpEngine, 3, 'read-write', 'authPriv',
                           (1, 3, 6), (1, 3, 6))

        # Build MIB
        def stringToOid(string):
            return [ord(x) for x in string]

        def flatten(*args):
            result = []
            for el in args:
                if isinstance(el, (list, tuple)):
                    for sub in el:
                        result.append(sub)
                else:
                    result.append(el)
            return tuple(result)
        snmpContext = context.SnmpContext(snmpEngine)
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
            MibScalarInstance((1, 3, 6, 1, 2, 1, 1, 1), (0,),
                              v2c.OctetString("Snimpy Test Agent")))
        mibBuilder.exportSymbols(
            '__MY_IF_MIB',
            # IF-MIB::ifNumber
            MibScalar((1, 3, 6, 1, 2, 1, 2, 1), v2c.Integer()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 1), (0,), v2c.Integer(3)),
            # IF-MIB::ifTable
            MibTable((1, 3, 6, 1, 2, 1, 2, 2)),
            MibTableRow((1, 3, 6, 1, 2, 1, 2, 2, 1)).setIndexNames(
                (0, '__MY_IF_MIB', 'ifIndex')),
            # IF-MIB::ifIndex
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (1,), v2c.Integer(1)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (2,), v2c.Integer(2)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 1), (3,), v2c.Integer(3)),
            # IF-MIB::ifDescr
            MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 2), v2c.OctetString()),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (1,), v2c.OctetString("lo")),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (2,), v2c.OctetString("eth0")),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 2), (3,), v2c.OctetString("eth1")),
            # IF-MIB::ifType
            MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 3), v2c.Integer()),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (1,), v2c.Integer(24)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (2,), v2c.Integer(6)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 3), (3,), v2c.Integer(6)),
            # IF-MIB::ifIndex
            ifIndex=MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 1),
                                   v2c.Integer()))
        mibBuilder.exportSymbols(
            '__MY_SNIMPY-MIB',
            # SNIMPY-MIB::snimpyIpAddress
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 1),
                      v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 1), (0,),
                v2c.OctetString("AAAA")),
            # SNIMPY-MIB::snimpyString
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 2),
                      v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 2), (0,), v2c.OctetString("bye")),
            # SNIMPY-MIB::snimpyInteger
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 3),
                      v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 3), (0,), v2c.Integer(19)),
            # SNIMPY-MIB::snimpyEnum
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 4),
                      v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 4), (0,), v2c.Integer(2)),
            # SNIMPY-MIB::snimpyObjectId
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 5),
                      v2c.ObjectIdentifier()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 5), (
                0,), v2c.ObjectIdentifier((1, 3, 6, 4454, 0, 0))),
            # SNIMPY-MIB::snimpyBoolean
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 6),
                      v2c.Integer()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 6), (0,), v2c.Integer(1)),
            # SNIMPY-MIB::snimpyCounter
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 7),
                      v2c.Counter32()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 7), (0,), v2c.Counter32(47)),
            # SNIMPY-MIB::snimpyGauge
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 8),
                      v2c.Gauge32()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 8), (0,), v2c.Gauge32(18)),
            # SNIMPY-MIB::snimpyTimeticks
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 9),
                      v2c.TimeTicks()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 9), (0,),
                v2c.TimeTicks(12111100)),
            # SNIMPY-MIB::snimpyCounter64
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 10),
                      v2c.Counter64()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 10), (0,),
                v2c.Counter64(2 ** 48 + 3)),
            # SNIMPY-MIB::snimpyBits
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 11),
                      v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 11), (0,),
                v2c.OctetString(b"\xa0")),
            # SNIMPY-MIB::snimpyMacAddress
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 15),
                      v2c.OctetString()).setMaxAccess("readwrite"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 15), (
                0,), v2c.OctetString(b"\x11\x12\x13\x14\x15\x16")),

            # SNIMPY-MIB::snimpyIndexTable
            MibTable((1, 3, 6, 1, 2, 1, 45121, 2, 3)),
            MibTableRow(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1)).setIndexNames(
                (0, "__MY_SNIMPY-MIB", "snimpyIndexVarLen"),
                (0, "__MY_SNIMPY-MIB", "snimpyIndexOidVarLen"),
                (0, "__MY_SNIMPY-MIB", "snimpyIndexFixedLen"),
                (1, "__MY_SNIMPY-MIB", "snimpyIndexImplied")),
            # SNIMPY-MIB::snimpyIndexInt
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 6),
                              flatten(4, stringToOid('row1'),
                                      3, 1, 2, 3,
                                      stringToOid('alpha5'),
                                      stringToOid('end of row1')),
                              v2c.Integer(4571)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 6),
                              flatten(4, stringToOid('row2'),
                                      4, 1, 0, 2, 3,
                                      stringToOid('beta32'),
                                      stringToOid('end of row2')),
                              v2c.Integer(78741)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 6),
                              flatten(4, stringToOid('row3'),
                                      4, 120, 1, 2, 3,
                                      stringToOid('gamma7'),
                                      stringToOid('end of row3')),
                              v2c.Integer(4110)),
            # Indexes
            snimpyIndexVarLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 1),
                v2c.OctetString(
                )).setMaxAccess("noaccess"),
            snimpyIndexIntIndex=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 2),
                v2c.Integer(
                )).setMaxAccess(
                "noaccess"),
            snimpyIndexOidVarLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 3),
                v2c.ObjectIdentifier(
                )).setMaxAccess(
                "noaccess"),
            snimpyIndexFixedLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 4),
                v2c.OctetString(
                ).setFixedLength(
                    6)).setMaxAccess(
                "noaccess"),
            snimpyIndexImplied=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 5),
                v2c.OctetString(
                )).setMaxAccess("noaccess"),
            snimpyIndexInt=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 6),
                v2c.Integer()).setMaxAccess("readwrite")
        )
        # Start agent
        cmdrsp.GetCommandResponder(snmpEngine, snmpContext)
        cmdrsp.SetCommandResponder(snmpEngine, snmpContext)
        cmdrsp.NextCommandResponder(snmpEngine, snmpContext)
        cmdrsp.BulkCommandResponder(snmpEngine, snmpContext)
        q.put(port)
        snmpEngine.transportDispatcher.jobStarted(1)
        snmpEngine.transportDispatcher.runDispatcher()
