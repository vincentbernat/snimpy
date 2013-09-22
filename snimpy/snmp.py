##############################################################################
##                                                                          ##
## snimpy -- Interactive SNMP tool                                          ##
##                                                                          ##
## Copyright (C) Vincent Bernat <bernat@luffy.cx>                           ##
##                                                                          ##
## Permission to use, copy, modify, and distribute this software for any    ##
## purpose with or without fee is hereby granted, provided that the above   ##
## copyright notice and this permission notice appear in all copies.        ##
##                                                                          ##
## THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES ##
## WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         ##
## MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  ##
## ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   ##
## WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    ##
## ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  ##
## OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           ##
##                                                                          ##
##############################################################################

"""
simple interface to PySNMP
"""

from __future__ import print_function
from __future__ import unicode_literals

import re
import inspect
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902, rfc1905
from pysnmp.smi import error

class SNMPException(Exception):
    """SNMP related base exception"""

# v1 exceptions
class SNMPTooBig(SNMPException): pass
class SNMPNoSuchName(SNMPException): pass
class SNMPBadValue(SNMPException): pass
class SNMPReadOnly(SNMPException): pass

# Dynamically build exceptions
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
    """SNMP session"""

    def __init__(self, host,
                 community="public", version=2,
                 secname=None,
                 authprotocol=None,
                 authpassword=None,
                 privprotocol=None,
                 privpassword=None):
        self._host = host
        self._version = version
        self._cmdgen = cmdgen.CommandGenerator()

        # Put authentication stuff in self._auth
        if version in [1, 2]:
            self._auth = cmdgen.CommunityData(community, community, version - 1)
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
                raise ValueError("{0} is not an acceptable authentication protocol".format(
                    authprotocol))
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
                raise ValueError("{0} is not an acceptable privacy protocol".format(
                    privprotocol))
            self._auth = cmdgen.UsmUserData(secname,
                                            authpassword,
                                            privpassword,
                                            authprotocol,
                                            privprotocol)
        else:
            raise ValueError("unsupported SNMP version {0}".format(version))

        # Put transport stuff into self._transport
        host, port = host.partition(":")[::2]
        if not port:
            port = 161
        self._transport = cmdgen.UdpTransportTarget((host, int(port)))

        # Bulk stuff
        self.bulk = 40

    def _check_exception(self, value):
        """Check if the given ASN1 value is an exception"""
        if isinstance(value, rfc1905.NoSuchObject):
            raise SNMPNoSuchObject("No such object was found")
        if isinstance(value, rfc1905.NoSuchInstance):
            raise SNMPNoSuchInstance("No such instance exists")
        if isinstance(value, rfc1905.EndOfMibView):
            raise SNMPEndOfMibView("End of MIB was reached")

    def _convert(self, value):
        """Convert a PySNMP value to some native Python type"""
        for cl, fn in { rfc1902.Integer: int,
                        rfc1902.Integer32: int,
                        rfc1902.OctetString: str,
                        rfc1902.IpAddress: value.prettyOut,
                        rfc1902.Counter32: int,
                        rfc1902.Counter64: int,
                        rfc1902.Gauge32: int,
                        rfc1902.Unsigned32: int,
                        rfc1902.TimeTicks: int,
                        rfc1902.Bits: str,
                        rfc1902.univ.ObjectIdentifier: tuple }.iteritems():
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
        if cmd in [self._cmdgen.getCmd, self._cmdgen.setCmd] :
            results = [(tuple(name), val) for name, val in varBinds]
        else:
            results = [(tuple(name), val) for row in varBinds for name, val in row]
        if len(results) == 0:
            if cmd not in [self._cmdgen.nextCmd, self._cmdgen.bulkCmd]:
                raise SNMPException("empty answer")
            # This seems to be filtered
            raise SNMPEndOfMibView("no more stuff after this OID")
        return tuple([(oid, self._convert(val)) for oid, val in results])

    def get(self, *oids):
        """Retrieve an OID value using GET."""
        return self._op(self._cmdgen.getCmd, *oids)

    def walk(self, *oids):
        """Retrieve OIDs values using GETBULK or GETNEXT."""
        if self._version == 1 or not self.bulk:
            return self._op(self._cmdgen.nextCmd, *oids)
        args = [0, self.bulk] + list(oids)
        return self._op(self._cmdgen.bulkCmd, *args)

    def set(self, *args):
        """Set an OID value using SET."""
        if len(args) % 2 != 0:
            raise ValueError("expect an even number of arguments for SET")
        varbinds = zip(*[args[0::2], [v.pack() for v in args[1::2]]])
        return self._op(self._cmdgen.setCmd, *varbinds)

    def __repr__(self):
        return "{0}(host={1},version={2})".format(
            self.__class__.__name__,
            self.host,
            self.version)

    @property
    def timeout(self):
        """Get timeout value for the current session.

        @return: timeout value in microseconds
        """
        return self._transport.timeout * 1000000

    @timeout.setter
    def timeout(self, value):
        """Set timeout value for the current session."""
        value = int(value)
        if value <= 0:
            raise ValueError("timeout is a positive integer")
        self._transport.timeout = value / 1000000.

    @property
    def retries(self):
        """Get number of times a request is retried.

        @return: number of retries for each request
        """
        return self._transport.retries

    @retries.setter
    def retries(self, value):
        """Set number of times a request is retried."""
        value = int(value)
        if value < 0:
            raise ValueError("retries is a non-negative integer")
        self._transport.retries = value

    @property
    def bulk(self):
        """Get bulk settings.

        @return: C{False} if bulk is disabled or a non-negative integer
                 for the number of repetitions.
        """
        return self._bulk

    @bulk.setter
    def bulk(self, value):
        """Set bulk settings.

        @param value: C{False} to disable bulk or a non-negative
                      integer for the number of allowed repetitions.
        """
        if value is False:
            self._bulk = False
            return
        value = int(value)
        if value <= 0:
            raise ValueError("{0} is not an appropriate value for max repeater parameter".format(
                value))
        self._bulk = value
