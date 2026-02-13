from multiprocessing import Process, Queue
import random
import sys

from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncio.dgram import udp, udp6
from pysnmp.proto.api import v2c
from pysnmp.smi import error as smi_error


# Workaround for pysnmp v7 bug: SetCommandResponder.handle_management_operation
# calls release_state_information before re-raising errors, so process_pdu
# cannot send the error response (KeyError on stateReference). See
# https://github.com/lextudio/pysnmp/issues/230
def _fixed_set_handle_management_operation(self, snmpEngine, stateReference,
                                           contextName, PDU):
    mgmtFun = self.snmpContext.get_mib_instrum(contextName).write_variables
    varBinds = v2c.apiPDU.get_varbinds(PDU)
    context = dict(
        snmpEngine=snmpEngine, acFun=self.verify_access, cbCtx=self.cbCtx)
    try:
        rspVarBinds = mgmtFun(*varBinds, **context)
    except (smi_error.NoSuchObjectError, smi_error.NoSuchInstanceError):
        instrumError = smi_error.NotWritableError()
        instrumError.update(sys.exc_info()[1])
        raise instrumError
    self.send_varbinds(snmpEngine, stateReference, 0, 0, rspVarBinds)
    self.release_state_information(stateReference)


cmdrsp.SetCommandResponder.handle_management_operation = (
    _fixed_set_handle_management_operation)


class TestAgent:

    next_port = [random.randint(22000, 32000)]

    """Agent for testing purpose"""

    def __init__(self, ipv6=False, community='public',
                 authpass='authpass', privpass='privpass',
                 emptyTable=True):
        q = Queue()
        self.ipv6 = ipv6
        self.emptyTable = emptyTable
        self.community = community
        self.authpass = authpass
        self.privpass = privpass
        self.next_port[0] += 1
        self._process = Process(target=self._setup,
                                args=(q, self.next_port[0]))
        self._process.start()
        self.port = q.get()

    def terminate(self):
        self._process.terminate()

    def _setup(self, q, port):
        """Setup a new agent in a separate process.

        The port the agent is listening too will be returned using the
        provided queue.
        """
        snmpEngine = engine.SnmpEngine()
        if self.ipv6:
            config.add_transport(
                snmpEngine,
                udp6.DOMAIN_NAME,
                udp6.Udp6Transport().open_server_mode(('::1', port)))
        else:
            config.add_transport(
                snmpEngine,
                udp.DOMAIN_NAME,
                udp.UdpTransport().open_server_mode(('127.0.0.1', port)))
        # Community is public and MIB is writable
        config.add_v1_system(snmpEngine, 'read-write', self.community)
        config.add_vacm_user(snmpEngine, 1, 'read-write', 'noAuthNoPriv',
                             (1, 3, 6), (1, 3, 6))
        config.add_vacm_user(snmpEngine, 2, 'read-write', 'noAuthNoPriv',
                             (1, 3, 6), (1, 3, 6))
        config.add_v3_user(
            snmpEngine, 'read-write',
            config.USM_AUTH_HMAC96_MD5, self.authpass,
            config.USM_PRIV_CFB128_AES, self.privpass)
        config.add_vacm_user(snmpEngine, 3, 'read-write', 'authPriv',
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
        mibBuilder = snmpContext.get_mib_instrum().get_mib_builder()
        (MibTable, MibTableRow, MibTableColumn,
         MibScalar, MibScalarInstance) = mibBuilder.import_symbols(
            'SNMPv2-SMI',
            'MibTable', 'MibTableRow', 'MibTableColumn',
            'MibScalar', 'MibScalarInstance')

        class RandomMibScalarInstance(MibScalarInstance):
            previous_value = 0

            def getValue(self, name, idx, **kwargs):
                self.previous_value += random.randint(1, 2000)
                return self.getSyntax().clone(self.previous_value)

        mibBuilder.export_symbols(
            '__MY_SNMPv2_MIB',
            # SNMPv2-MIB::sysDescr
            MibScalar((1, 3, 6, 1, 2, 1, 1, 1), v2c.OctetString()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 1, 1), (0,),
                              v2c.OctetString(
                                  "Snimpy Test Agent {}".format(
                                      self.community))),
            # SNMPv2-MIB::sysObjectID
            MibScalar((1, 3, 6, 1, 2, 1, 1, 2), v2c.ObjectIdentifier()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 1, 2), (0,),
                              v2c.ObjectIdentifier((1, 3, 6, 1, 4,
                                                    1, 9, 1, 1208))))
        mibBuilder.export_symbols(
            '__MY_IF_MIB',
            # IF-MIB::ifNumber
            MibScalar((1, 3, 6, 1, 2, 1, 2, 1), v2c.Integer()),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 2, 1), (0,), v2c.Integer(3)),
            # IF-MIB::ifTable
            MibTable((1, 3, 6, 1, 2, 1, 2, 2)),
            MibTableRow((1, 3, 6, 1, 2, 1, 2, 2, 1)).set_index_names(
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
            # IF-MIB::ifInOctets
            MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 10), v2c.Integer()),
            RandomMibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 10), (1,), v2c.Gauge32()),
            RandomMibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 10), (2,), v2c.Gauge32()),
            RandomMibScalarInstance(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 10), (3,), v2c.Gauge32()),

            # IF-MIB::ifRcvAddressTable
            MibTable((1, 3, 6, 1, 2, 1, 31, 1, 4)),
            MibTableRow((1, 3, 6, 1, 2, 1, 31, 1, 4, 1)).set_index_names(
                (0, '__MY_IF_MIB', 'ifIndex'),
                (1, '__MY_IF_MIB', 'ifRcvAddressAddress')),
            # IF-MIB::ifRcvAddressStatus
            MibTableColumn((1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 2), v2c.Integer()),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 2),
                flatten(2, 6, stringToOid("abcdef")), v2c.Integer(1)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 2),
                flatten(2, 6, stringToOid("ghijkl")), v2c.Integer(1)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 2),
                flatten(3, 6, stringToOid("mnopqr")), v2c.Integer(1)),
            # IF-MIB::ifRcvAddressType
            MibTableColumn((1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 3), v2c.Integer()),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 3),
                flatten(2, 6, stringToOid("abcdef")), v2c.Integer(1)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 3),
                flatten(2, 6, stringToOid("ghijkl")), v2c.Integer(1)),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 31, 1, 4, 1, 3),
                flatten(3, 6, stringToOid("mnopqr")), v2c.Integer(1)),

            # IF-MIB::ifIndex
            ifIndex=MibTableColumn((1, 3, 6, 1, 2, 1, 2, 2, 1, 1),
                                   v2c.Integer()),
            # IF-MIB::ifRcvAddressAddress
            ifRcvAddressAddress=MibTableColumn((1, 3, 6, 1, 2, 1, 31,
                                                1, 4, 1, 1),
                                               v2c.OctetString()))

        args = (
            '__MY_SNIMPY-MIB',
            # SNIMPY-MIB::snimpyIpAddress
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 1),
                      v2c.OctetString()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 1), (0,),
                v2c.OctetString("AAAA")),
            # SNIMPY-MIB::snimpyString
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 2),
                      v2c.OctetString()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 2), (0,), v2c.OctetString("bye")),
            # SNIMPY-MIB::snimpyInteger
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 3),
                      v2c.Integer()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 3), (0,), v2c.Integer(19)),
            # SNIMPY-MIB::snimpyEnum
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 4),
                      v2c.Integer()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 4), (0,), v2c.Integer(2)),
            # SNIMPY-MIB::snimpyObjectId
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 5),
                      v2c.ObjectIdentifier()).set_max_access("read-write"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 5), (
                0,), v2c.ObjectIdentifier((1, 3, 6, 4454, 0, 0))),
            # SNIMPY-MIB::snimpyBoolean
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 6),
                      v2c.Integer()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 6), (0,), v2c.Integer(1)),
            # SNIMPY-MIB::snimpyCounter
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 7),
                      v2c.Counter32()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 7), (0,), v2c.Counter32(47)),
            # SNIMPY-MIB::snimpyGauge
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 8),
                      v2c.Gauge32()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 8), (0,), v2c.Gauge32(18)),
            # SNIMPY-MIB::snimpyTimeticks
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 9),
                      v2c.TimeTicks()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 9), (0,),
                v2c.TimeTicks(12111100)),
            # SNIMPY-MIB::snimpyCounter64
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 10),
                      v2c.Counter64()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 10), (0,),
                v2c.Counter64(2 ** 48 + 3)),
            # SNIMPY-MIB::snimpyBits
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 11),
                      v2c.OctetString()).set_max_access("read-write"),
            MibScalarInstance(
                (1, 3, 6, 1, 2, 1, 45121, 1, 11), (0,),
                v2c.OctetString(b"\xa0\x80")),
            # SNIMPY-MIB::snimpyMacAddress
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 15),
                      v2c.OctetString()).set_max_access("read-write"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 15), (
                0,), v2c.OctetString(b"\x11\x12\x13\x14\x15\x16")),
            # SNIMPY-MIB::snimpyMacAddressInvalid
            MibScalar((1, 3, 6, 1, 2, 1, 45121, 1, 16),
                      v2c.OctetString()).set_max_access("read-write"),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 1, 16), (
                0,), v2c.OctetString(b"\xf1\x12\x13\x14\x15\x16")),

            # SNIMPY-MIB::snimpyIndexTable
            MibTable((1, 3, 6, 1, 2, 1, 45121, 2, 3)),
            MibTableRow(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1)).set_index_names(
                (0, "__MY_SNIMPY-MIB", "snimpyIndexVarLen"),
                (0, "__MY_SNIMPY-MIB", "snimpyIndexOidVarLen"),
                (0, "__MY_SNIMPY-MIB", "snimpyIndexFixedLen"),
                (1, "__MY_SNIMPY-MIB", "snimpyIndexImplied")),
            # SNIMPY-MIB::snimpyIndexVarLen
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 1),
                              flatten(4, stringToOid('row1'),
                                      3, 1, 2, 3,
                                      stringToOid('alpha5'),
                                      stringToOid('end of row1')),
                              v2c.OctetString(b"row1")),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 1),
                              flatten(4, stringToOid('row2'),
                                      4, 1, 0, 2, 3,
                                      stringToOid('beta32'),
                                      stringToOid('end of row2')),
                              v2c.OctetString(b"row2")),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 1),
                              flatten(4, stringToOid('row3'),
                                      4, 120, 1, 2, 3,
                                      stringToOid('gamma7'),
                                      stringToOid('end of row3')),
                              v2c.OctetString(b"row3")),
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

            # SNIMPY-MIB::snimpyReuseIndexTable
            MibTable((1, 3, 6, 1, 2, 1, 45121, 2, 7)),
            MibTableRow(
                (1, 3, 6, 1, 2, 1, 45121, 2, 7, 1)).set_index_names(
                (0, "__MY_SNIMPY-MIB", "snimpyIndexImplied"),
                (0, "__MY_SNIMPY-MIB", "snimpySimpleIndex")),
            # SNIMPY-MIB::snimpyReuseIndexValue
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 7, 1, 1),
                              flatten(11, stringToOid('end of row1'),
                                      4),
                              v2c.Integer(1785)),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 7, 1, 1),
                              flatten(11, stringToOid('end of row1'),
                                      5),
                              v2c.Integer(2458)),

            # SNIMPY-MIB::snimpyInvalidTable
            MibTable((1, 3, 6, 1, 2, 1, 45121, 2, 5)),
            MibTableRow(
                (1, 3, 6, 1, 2, 1, 45121, 2, 5, 1)).set_index_names(
                (0, "__MY_SNIMPY-MIB", "snimpyInvalidIndex")),
            # SNIMPY-MIB::snimpyInvalidDescr
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 5, 1, 2),
                              (1,),
                              v2c.OctetString(b"Hello")),
            MibScalarInstance((1, 3, 6, 1, 2, 1, 45121, 2, 5, 1, 2),
                              (2,),
                              v2c.OctetString(b"\xf1\x12\x13\x14\x15\x16")))

        if self.emptyTable:
            args += (
                # SNIMPY-MIB::snimpyEmptyTable
                MibTable((1, 3, 6, 1, 2, 1, 45121, 2, 6)),
                MibTableRow(
                    (1, 3, 6, 1, 2, 1, 45121, 2, 6, 1)).set_index_names(
                        (0, "__MY_SNIMPY-MIB", "snimpyEmptyIndex")))

        kwargs = dict(
            # Indexes
            snimpyIndexVarLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 1),
                v2c.OctetString(
                )),
            snimpyIndexIntIndex=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 2),
                v2c.Integer(
                )).set_max_access(
                "noaccess"),
            snimpyIndexOidVarLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 3),
                v2c.ObjectIdentifier(
                )).set_max_access(
                "noaccess"),
            snimpyIndexFixedLen=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 4),
                v2c.OctetString(
                ).set_fixed_length(
                    6)).set_max_access(
                "noaccess"),
            snimpyIndexImplied=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 5),
                v2c.OctetString(
                )).set_max_access("not-accessible"),
            snimpyIndexInt=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 3, 1, 6),
                v2c.Integer()).set_max_access("read-write"),
            snimpyInvalidIndex=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 5, 1, 1),
                v2c.Integer()).set_max_access("not-accessible"),
            snimpyInvalidDescr=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 5, 1, 2),
                v2c.OctetString()).set_max_access("read-write"),
            snimpyReuseIndexValue=MibTableColumn(
                (1, 3, 6, 1, 2, 1, 45121, 2, 7, 1, 1),
                v2c.Integer()).set_max_access("read-write")
        )

        if self.emptyTable:
            kwargs.update(dict(
                snimpyEmptyIndex=MibTableColumn(
                    (1, 3, 6, 1, 2, 1, 45121, 2, 6, 1, 1),
                    v2c.Integer()).set_max_access("not-accessible"),
                snimpyEmptyDescr=MibTableColumn(
                    (1, 3, 6, 1, 2, 1, 45121, 2, 6, 1, 2),
                    v2c.OctetString()).set_max_access("read-write")))

        mibBuilder.export_symbols(*args, **kwargs)

        # Start agent
        cmdrsp.GetCommandResponder(snmpEngine, snmpContext)
        cmdrsp.SetCommandResponder(snmpEngine, snmpContext)
        cmdrsp.NextCommandResponder(snmpEngine, snmpContext)
        cmdrsp.BulkCommandResponder(snmpEngine, snmpContext)
        q.put(port)
        snmpEngine.transport_dispatcher.job_started(1)
        snmpEngine.transport_dispatcher.run_dispatcher()
