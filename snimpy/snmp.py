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
from pysnmp.entity.rfc3413.oneliner import cmdgen
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
        name = str("SNMP{0}".format(name[:-5]))
        globals()[name] = type(name, (SNMPException,), {})
del name
del obj


class Session(object):

    """SNMP session. An instance of this object will represent an SNMP
    session. From such an instance, one can get information from the
    associated agent."""

    def __init__(self, host,
                 community="public", version=2,
                 secname=None,
                 authprotocol=None,
                 authpassword=None,
                 privprotocol=None,
                 privpassword=None):
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
            SNMPv3. This can be `None` or either the string `SHA` or
            `MD5`.
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
        :type privpassword: str
        """
        self._host = host
        self._version = version
        self._cmdgen = cmdgen.CommandGenerator()

        # Put authentication stuff in self._auth
        if version in [1, 2]:
            self._auth = cmdgen.CommunityData(
                community, community, version - 1)
        elif version == 3:
            if secname is None:
                secname = community
            try:
                authprotocol = {
                    None: cmdgen.usmNoAuthProtocol,
                    "MD5": cmdgen.usmHMACMD5AuthProtocol,
                    "SHA": cmdgen.usmHMACSHAAuthProtocol,
                    "SHA1": cmdgen.usmHMACSHAAuthProtocol
                }[authprotocol]
            except KeyError:
                raise ValueError("{0} is not an acceptable authentication "
                                 "protocol".format(authprotocol))
            try:
                privprotocol = {
                    None: cmdgen.usmNoPrivProtocol,
                    "DES": cmdgen.usmDESPrivProtocol,
                    "3DES": cmdgen.usm3DESEDEPrivProtocol,
                    "AES": cmdgen.usmAesCfb128Protocol,
                    "AES128": cmdgen.usmAesCfb128Protocol,
                    "AES192": cmdgen.usmAesCfb192Protocol,
                    "AES256": cmdgen.usmAesCfb256Protocol,
                }[privprotocol]
            except KeyError:
                raise ValueError("{0} is not an acceptable privacy "
                                 "protocol".format(privprotocol))
            self._auth = cmdgen.UsmUserData(secname,
                                            authpassword,
                                            privpassword,
                                            authprotocol,
                                            privprotocol)
        else:
            raise ValueError("unsupported SNMP version {0}".format(version))

        # Put transport stuff into self._transport
        mo = re.match(r'^(?:'
                      r'\[(?P<ipv6>[\d:]+)\]|'
                      r'(?P<ipv4>[\d\.]+)|'
                      r'(?P<any>.*?))'
                      r'(?::(?P<port>\d+))?$',
                      host)
        if mo.group("port"):
            port = int(mo.group("port"))
        else:
            port = 161
        if mo.group("ipv6"):
            self._transport = cmdgen.Udp6TransportTarget((mo.group("ipv6"),
                                                          port))
        elif mo.group("ipv4"):
            self._transport = cmdgen.UdpTransportTarget((mo.group("ipv4"),
                                                         port))
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
                self._transport = cmdgen.UdpTransportTarget((mo.group("any"),
                                                             port))
            else:
                self._transport = cmdgen.Udp6TransportTarget((mo.group("any"),
                                                              port))

        # Bulk stuff
        self.bulk = 40

    def _check_exception(self, value):
        """Check if the given ASN1 value is an exception"""
        if isinstance(value, rfc1905.NoSuchObject):
            raise SNMPNoSuchObject("No such object was found")  # nopep8
        if isinstance(value, rfc1905.NoSuchInstance):
            raise SNMPNoSuchInstance("No such instance exists")  # nopep8
        if isinstance(value, rfc1905.EndOfMibView):
            raise SNMPEndOfMibView("End of MIB was reached")  # nopep8

    def _convert(self, value):
        """Convert a PySNMP value to some native Python type"""
        for cl, fn in {rfc1902.Integer: int,
                       rfc1902.Integer32: int,
                       rfc1902.OctetString: bytes,
                       rfc1902.IpAddress: value.prettyOut,
                       rfc1902.Counter32: int,
                       rfc1902.Counter64: int,
                       rfc1902.Gauge32: int,
                       rfc1902.Unsigned32: int,
                       rfc1902.TimeTicks: int,
                       rfc1902.Bits: str,
                       rfc1902.univ.ObjectIdentifier: tuple}.items():
            if isinstance(value, cl):
                return fn(value)
        self._check_exception(value)
        raise NotImplementedError("unable to convert {0}".format(repr(value)))

    def _op(self, cmd, *oids):
        """Apply an SNMP operation"""
        errorIndication, errorStatus, errorIndex, varBinds = cmd(
            self._auth, self._transport, *oids)
        if errorIndication:
            self._check_exception(errorIndication)
            raise SNMPException(str(errorIndication))
        if errorStatus:
            # We try to find a builtin exception with the same message
            exc = str(errorStatus.prettyPrint())
            exc = re.sub(r'\W+', '', exc)
            exc = "SNMP{0}".format(exc[0].upper() + exc[1:])
            if str(exc) in globals():
                raise globals()[exc]
            raise SNMPException(errorStatus.prettyPrint())
        if cmd in [self._cmdgen.getCmd, self._cmdgen.setCmd]:
            results = [(tuple(name), val) for name, val in varBinds]
        else:
            results = [(tuple(name), val)
                       for row in varBinds for name, val in row]
        if len(results) == 0:
            if cmd not in [self._cmdgen.nextCmd, self._cmdgen.bulkCmd]:
                raise SNMPException("empty answer")
            # This seems to be filtered
            raise SNMPEndOfMibView("no more stuff after this OID")  # nopep8
        return tuple([(oid, self._convert(val)) for oid, val in results])

    def get(self, *oids):
        """Retrieve an OID value using GET.

        :param oids: a list of OID to retrieve. An OID is a tuple.
        :return: a list of tuples with the retrieved OID and the raw value.
        """
        return self._op(self._cmdgen.getCmd, *oids)

    def walk(self, *oids):
        """Retrieve OIDs values using GETBULK or GETNEXT. The method is called
        "walk" but this is either a GETBULK or a GETNEXT. The later is
        only used for SNMPv1 or if bulk has been disabled using
        :meth:`bulk` property.

        :param oids: a list of OID to retrieve. An OID is a tuple.
        :return: a list of tuples with the retrieved OID and the raw value.

        """
        if self._version == 1 or not self.bulk:
            return self._op(self._cmdgen.nextCmd, *oids)
        args = [0, self.bulk] + list(oids)
        return self._op(self._cmdgen.bulkCmd, *args)

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
        varbinds = zip(*[args[0::2], [v.pack() for v in args[1::2]]])
        return self._op(self._cmdgen.setCmd, *varbinds)

    def __repr__(self):
        return "{0}(host={1},version={2})".format(
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
            raise ValueError("{0} is not an appropriate value "
                             "for max repeater parameter".format(
                                 value))
        self._bulk = value
