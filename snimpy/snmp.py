#
# snimpy -- Interactive SNMP tool
#
# Copyright (C) Vincent Bernat <bernat@luffy.cx>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

"""
This module is a low-level interface to build SNMP requests, send
them and receive answers. It is built on top of pysnmp_ but the
exposed interface is far simpler. It is also far less complete and
there is an important dependency to the :mod:`basictypes` module for
type coercing.

.. _pysnmp: http://pysnmp.sourceforge.net/
"""

import re
import socket
import inspect
import threading
import asyncio
import ipaddress
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UsmUserData,
    UdpTransportTarget, Udp6TransportTarget, ContextData,
    ObjectType, ObjectIdentity,
    get_cmd, set_cmd, walk_cmd, bulk_walk_cmd,
    usmNoAuthProtocol, usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
    usmHMAC128SHA224AuthProtocol, usmHMAC192SHA256AuthProtocol,
    usmHMAC256SHA384AuthProtocol, usmHMAC384SHA512AuthProtocol,
    usmNoPrivProtocol, usmDESPrivProtocol, usm3DESEDEPrivProtocol,
    usmAesCfb128Protocol, usmAesCfb192Protocol, usmAesCfb256Protocol,
)
from pysnmp.proto import rfc1902, rfc1905
from pysnmp.smi import error


class SNMPException(Exception):
    """SNMP related base exception. All SNMP exceptions are inherited from
    this one. The inherited exceptions are named after the name of the
    corresponding SNMP error.
    """


class SNMPTooBig(SNMPException):
    pass


class SNMPNoSuchName(SNMPException):
    pass


class SNMPBadValue(SNMPException):
    pass


class SNMPReadOnly(SNMPException):
    pass


# Dynamically build remaining (v2) exceptions
for name, obj in inspect.getmembers(error):
    if name.endswith("Error") and \
       inspect.isclass(obj) and \
       issubclass(obj, error.MibOperationError) and \
       obj != error.MibOperationError:
        name = str("SNMP{}".format(name[:-5]))
        globals()[name] = type(name, (SNMPException,), {})
del name
del obj


class Session:

    """SNMP session. An instance of this object will represent an SNMP
    session. From such an instance, one can get information from the
    associated agent."""

    _tls = threading.local()

    def _run(self, coro):
        """Run an async coroutine synchronously using a thread-local loop."""
        if not hasattr(self._tls, "loop"):
            self._tls.loop = asyncio.new_event_loop()
        return self._tls.loop.run_until_complete(coro)

    def __init__(self, host,
                 community="public", version=2,
                 secname=None,
                 authprotocol=None,
                 authpassword=None,
                 privprotocol=None,
                 privpassword=None,
                 contextname=None,
                 bulk=40,
                 none=False):
        """Create a new SNMP session.

        :param host: The hostname or IP address of the agent to
            connect to. Optionally, the port can be specified
            separated with a double colon.
        :type host: str
        :param community: The community to transmit to the agent for
            authorization purpose. This parameter is ignored if the
            specified version is 3.
        :type community: str
        :param version: The SNMP version to use to talk with the
            agent. Possible values are `1`, `2` (community-based) or
            `3`.
        :type version: int
        :param secname: Security name to use for SNMPv3 only.
        :type secname: str
        :param authprotocol: Authorization protocol to use for
            SNMPv3. This can be `None` or one of the strings `SHA`,
            `MD5`, `SHA224`, `SHA256`, `SHA384` or `SHA512`.
        :type authprotocol: None or str
        :param authpassword: Authorization password if authorization
            protocol is not `None`.
        :type authpassword: str
        :param privprotocol: Privacy protocol to use for SNMPv3. This
            can be `None` or either the string `AES`, `AES128`,
            `AES192`, `AES256` or `3DES`.
        :type privprotocol: None or str
        :param privpassword: Privacy password if privacy protocol is
            not `None`.
        :type contextname: str
        :param contextname: Context name for SNMPv3 messages.
        :type privpassword: str
        :param bulk: Max repetition value for `GETBULK` requests. Set
            to `0` to disable.
        :type bulk: int
        :param none: When enabled, will return None for not found
            values (instead of raising an exception)
        :type none: bool
        """
        self._host = host
        self._version = version
        self._none = none
        if version == 3:
            self._engine = SnmpEngine()
            self._contextname = contextname
        else:
            if not hasattr(self._tls, "engine"):
                self._tls.engine = SnmpEngine()
            self._engine = self._tls.engine
            self._contextname = None
        if version == 1 and none:
            raise ValueError("None-GET requests not compatible with SNMPv1")

        # Put authentication stuff in self._auth
        if version in [1, 2]:
            self._auth = CommunityData(
                community[0:30], community, version - 1)
        elif version == 3:
            if secname is None:
                secname = community
            try:
                authprotocol = {
                    None: usmNoAuthProtocol,
                    "MD5": usmHMACMD5AuthProtocol,
                    "SHA": usmHMACSHAAuthProtocol,
                    "SHA1": usmHMACSHAAuthProtocol,
                    "SHA224": usmHMAC128SHA224AuthProtocol,
                    "SHA256": usmHMAC192SHA256AuthProtocol,
                    "SHA384": usmHMAC256SHA384AuthProtocol,
                    "SHA512": usmHMAC384SHA512AuthProtocol,
                }[authprotocol]
            except KeyError:
                raise ValueError("{} is not an acceptable authentication "
                                 "protocol".format(authprotocol))
            try:
                privprotocol = {
                    None: usmNoPrivProtocol,
                    "DES": usmDESPrivProtocol,
                    "3DES": usm3DESEDEPrivProtocol,
                    "AES": usmAesCfb128Protocol,
                    "AES128": usmAesCfb128Protocol,
                    "AES192": usmAesCfb192Protocol,
                    "AES256": usmAesCfb256Protocol,
                }[privprotocol]
            except KeyError:
                raise ValueError("{} is not an acceptable privacy "
                                 "protocol".format(privprotocol))
            self._auth = UsmUserData(secname,
                                     authpassword,
                                     privpassword,
                                     authprotocol,
                                     privprotocol)
        else:
            raise ValueError("unsupported SNMP version {}".format(version))

        # Put transport stuff into self._transport
        mo = re.match(r'^(?:'
                      r'\[(?P<ipv6>[\d:A-Fa-f]+)\]|'
                      r'(?P<ipv4>[\d\.]+)|'
                      r'(?P<any>.*?))'
                      r'(?::(?P<port>\d+))?$',
                      host)
        if mo.group("port"):
            port = int(mo.group("port"))
        else:
            port = 161
        if mo.group("ipv6"):
            self._transport = self._run(
                Udp6TransportTarget.create((mo.group("ipv6"), port)))
        elif mo.group("ipv4"):
            self._transport = self._run(
                UdpTransportTarget.create((mo.group("ipv4"), port)))
        else:
            results = socket.getaddrinfo(mo.group("any"),
                                         port,
                                         0,
                                         socket.SOCK_DGRAM,
                                         socket.IPPROTO_UDP)
            # We should try to connect to each result to determine if
            # the given family is available. However, we cannot do
            # that over UDP. Let's implement a safe choice. If we have
            # an IPv4 address, use that. If not, use IPv6. If we want
            # to add an option to force IPv6, it is a good place.
            if [x for x in results if x[0] == socket.AF_INET]:
                self._transport = self._run(
                    UdpTransportTarget.create((mo.group("any"), port)))
            else:
                self._transport = self._run(
                    Udp6TransportTarget.create((mo.group("any"), port)))

        # Context data
        if self._contextname:
            self._contextdata = ContextData(
                contextName=rfc1902.OctetString(self._contextname))
        else:
            self._contextdata = ContextData()

        # Bulk stuff
        self.bulk = bulk

    def _check_exception(self, value):
        """Check if the given ASN1 value is an exception"""
        if isinstance(value, rfc1905.NoSuchObject):
            raise SNMPNoSuchObject("No such object was found")  # noqa: F821
        if isinstance(value, rfc1905.NoSuchInstance):
            raise SNMPNoSuchInstance("No such instance exists")  # noqa: F821
        if isinstance(value, rfc1905.EndOfMibView):
            raise SNMPEndOfMibView("End of MIB was reached")  # noqa: F821

    def _check_error(self, errorIndication, errorStatus):
        """Check for SNMP protocol errors in response"""
        if errorIndication:
            self._check_exception(errorIndication)
            raise SNMPException(str(errorIndication))
        if errorStatus:
            exc = str(errorStatus.prettyPrint())
            exc = re.sub(r'\W+', '', exc)
            exc = "SNMP{}".format(exc[0].upper() + exc[1:])
            if str(exc) in globals():
                raise globals()[exc]
            raise SNMPException(errorStatus.prettyPrint())

    def _convert(self, value):
        """Convert a PySNMP value to some native Python type"""
        try:
            # With PySNMP 4.3+, an OID is a ObjectIdentity. We try to
            # extract it while being compatible with earlier releases.
            value = value.getOid()
        except AttributeError:
            pass
        convertors = {rfc1902.Integer: int,
                      rfc1902.Integer32: int,
                      rfc1902.OctetString: bytes,
                      rfc1902.IpAddress: ipaddress.IPv4Address,
                      rfc1902.Counter32: int,
                      rfc1902.Counter64: int,
                      rfc1902.Gauge32: int,
                      rfc1902.Unsigned32: int,
                      rfc1902.TimeTicks: int,
                      rfc1902.Bits: str,
                      rfc1902.Opaque: str,
                      rfc1902.univ.ObjectIdentifier: tuple}
        if self._none:
            convertors[rfc1905.NoSuchObject] = lambda x: None
            convertors[rfc1905.NoSuchInstance] = lambda x: None
        for cl, fn in convertors.items():
            if isinstance(value, cl):
                return fn(value)
        self._check_exception(value)
        raise NotImplementedError("unable to convert {}".format(repr(value)))

    def get(self, *oids):
        """Retrieve an OID value using GET.

        :param oids: a list of OID to retrieve. An OID is a tuple.
        :return: a list of tuples with the retrieved OID and the raw value.
        """
        objecttypes = [ObjectType(ObjectIdentity(oid)) for oid in oids]
        errorIndication, errorStatus, errorIndex, varBinds = self._run(
            get_cmd(self._engine, self._auth, self._transport,
                    self._contextdata, *objecttypes, lookupMib=False))
        self._check_error(errorIndication, errorStatus)
        results = [(tuple(name), self._convert(val))
                   for name, val in varBinds]
        if not results:
            raise SNMPException("empty answer")
        return tuple(results)

    async def _walk_async(self, *oids):
        """Collect results from GETNEXT-based walk."""
        results = []
        for oid in oids:
            walker = walk_cmd(
                self._engine, self._auth, self._transport,
                self._contextdata,
                ObjectType(ObjectIdentity(oid)), lookupMib=False)
            async for result in walker:
                errorIndication, errorStatus, errorIndex, varBinds = result
                self._check_error(errorIndication, errorStatus)
                for name, val in varBinds:
                    results.append((tuple(name), val))
        return results

    async def _bulkwalk_async(self, bulk, *oids):
        """Collect results from GETBULK-based walk."""
        results = []
        for oid in oids:
            walker = bulk_walk_cmd(
                self._engine, self._auth, self._transport,
                self._contextdata, 0, bulk,
                ObjectType(ObjectIdentity(oid)), lookupMib=False)
            async for result in walker:
                errorIndication, errorStatus, errorIndex, varBinds = result
                self._check_error(errorIndication, errorStatus)
                for name, val in varBinds:
                    results.append((tuple(name), val))
        return results

    def walkmore(self, *oids):
        """Retrieve OIDs values using GETBULK or GETNEXT. The method is called
        "walk" but this is either a GETBULK or a GETNEXT. The later is
        only used for SNMPv1 or if bulk has been disabled using
        :meth:`bulk` property.

        :param oids: a list of OID to retrieve. An OID is a tuple.
        :return: a list of tuples with the retrieved OID and the raw value.

        """
        if self._version == 1 or not self.bulk:
            results = self._run(self._walk_async(*oids))
        else:
            try:
                results = self._run(self._bulkwalk_async(self.bulk, *oids))
            except SNMPTooBig:
                # Let's try to ask for less values. We will never increase
                # bulk again. We cannot increase it just after the walk
                # because we may end up requesting everything twice (or
                # more).
                nbulk = self.bulk / 2 or False
                if nbulk != self.bulk:
                    self.bulk = nbulk
                    return self.walk(*oids)
                raise
        return tuple([(oid, self._convert(val)) for oid, val in results])

    def walk(self, *oids):
        """Walk from given OIDs but don't return any "extra" results. Only
        results in the subtree will be returned.

        :param oid: OIDs used as a start point
        :return: a list of tuples with the retrieved OID and the raw value.
        """
        return ((noid, result)
                for oid in oids
                for noid, result in self.walkmore(oid)
                if (len(noid) >= len(oid) and
                    noid[:len(oid)] == oid[:len(oid)]))

    def set(self, *args):

        """Set an OID value using SET. This function takes an odd number of
        arguments. They are working by pair. The first member is an
        OID and the second one is :class:`basictypes.Type` instace
        whose `pack()` method will be used to transform into the
        appropriate form.

        :return: a list of tuples with the retrieved OID and the raw value.
        """
        if len(args) % 2 != 0:
            raise ValueError("expect an even number of arguments for SET")
        objecttypes = [ObjectType(ObjectIdentity(oid), val.pack())
                       for oid, val in zip(args[0::2], args[1::2])]
        errorIndication, errorStatus, errorIndex, varBinds = self._run(
            set_cmd(self._engine, self._auth, self._transport,
                    self._contextdata, *objecttypes, lookupMib=False))
        self._check_error(errorIndication, errorStatus)
        results = [(tuple(name), self._convert(val))
                   for name, val in varBinds]
        if not results:
            raise SNMPException("empty answer")
        return tuple(results)

    def __repr__(self):
        return "{}(host={},version={})".format(
            self.__class__.__name__,
            self._host,
            self._version)

    @property
    def timeout(self):
        """Get timeout value for the current session.

        :return: Timeout value in microseconds.
        """
        return self._transport.timeout * 1000000

    @timeout.setter
    def timeout(self, value):
        """Set timeout value for the current session.

        :param value: Timeout value in microseconds.
        """
        value = int(value)
        if value <= 0:
            raise ValueError("timeout is a positive integer")
        self._transport.timeout = value / 1000000.

    @property
    def retries(self):
        """Get number of times a request is retried.

        :return: Number of retries for each request.
        """
        return self._transport.retries

    @retries.setter
    def retries(self, value):
        """Set number of times a request is retried.

        :param value: Number of retries for each request.
        """
        value = int(value)
        if value < 0:
            raise ValueError("retries is a non-negative integer")
        self._transport.retries = value

    @property
    def bulk(self):
        """Get bulk settings.

        :return: `False` if bulk is disabled or a non-negative integer
            for the number of repetitions.
        """
        return self._bulk

    @bulk.setter
    def bulk(self, value):
        """Set bulk settings.

        :param value: `False` to disable bulk or a non-negative
            integer for the number of allowed repetitions.
        """
        if value is False:
            self._bulk = False
            return
        value = int(value)
        if value <= 0:
            raise ValueError("{} is not an appropriate value "
                             "for max repeater parameter".format(
                                 value))
        self._bulk = value
