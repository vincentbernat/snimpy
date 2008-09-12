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

"""MIB handling.

This module is aimed at handling MIBs with a simple Pythonic
interface. It needs libsmi2. Here is the full interface.

First import mib:

    >>> from snimpy.mib import ms

Then, you can load any MIB you want using C{load()}. You can either
specify a list of module names, a single module name, a path to a file
or use wildcards:

    >>> ms.load("IF-MIB")
    'IF-MIB'
    >>> ms.load(["UDP-MIB", "IP-MIB", "Inexistant-MIB"])
    ['UDP-MIB', 'IP-MIB']
    >>> ms.load('/usr/share/mibs/ietf/BRIDGE-MIB')
    'BRIDGE-MIB'
    >>> m=ms.load('/usr/share/mibs/ietf/IPV6-*')
    >>> 'IPV6-MIB' in m
    True
    >>> ms.load("Inexistant-MIB")
    Traceback (most recent call last):
    ...
    SMIModuleLoadError: unable to load module Inexistant-MIB

Then, you can access a module using "m" function:

    >>> ms.m("BRIDGE-MIB") # doctest: +ELLIPSIS
    <Module BRIDGE-MIB loaded from ...>

Or you can just access modules using attributes:

    >>> ms.BRIDGE_MIB # doctest: +ELLIPSIS
    <Module BRIDGE-MIB loaded from ...>
    >>> ms.IF_MIB # doctest: +ELLIPSIS
    <Module IF-MIB loaded from ...>
    >>> 'UDP_MIB' in dir(ms)
    True

Then, you can access nodes:

    >>> ms.IF_MIB.ifAdminStatus
    <Node "ifAdminStatus" of module IF-MIB>

To get OID, just call it as a function:

    >>> ms.IF_MIB.ifAdminStatus()
    <OID IF-MIB::ifAdminStatus>
    >>> ms.IF_MIB.ifAdminStatus(15)
    <OID IF-MIB::ifAdminStatus.15>
    >>> ms.IF_MIB.ifAdminStatus(15,16)
    <OID IF-MIB::ifAdminStatus.15.16>
    >>> ms.IF_MIB.ifAdminStatus([15,16])
    <OID IF-MIB::ifAdminStatus.15.16>
    >>> ms.IF_MIB.ifPhysAddress(15)
    <OID IF-MIB::ifPhysAddress.15 (SNMPv2-TC::PhysAddress)>

We can access documentation:

    >>> print ms.IF_MIB.__doc__
    The MIB module to describe generic objects for network
    interface sub-layers.  This MIB is an updated version of
    MIB-II's ifTable, and incorporates the extensions defined in
    RFC 1229.
    
    >>> print ms.IF_MIB.ifAdminStatus.__doc__
    The desired state of the interface.  The testing(3) state
    indicates that no operational packets can be passed.  When a
    managed system initializes, all interfaces start with
    ifAdminStatus in the down(2) state.  As a result of either
    explicit management action or per configuration information
    retained by the managed system, ifAdminStatus is then
    changed to either the up(1) or testing(3) states (or remains
    in the down(2) state).

From an OID object, you can get a list containing the numeric parts of
the OID, get the index part or get a pretty print of the OID
representation:

    >>> print ms.IF_MIB.ifAdminStatus(15)
    IF-MIB::ifAdminStatus.15
    >>> ms.IF_MIB.ifAdminStatus(15).oid
    [1, 3, 6, 1, 2, 1, 2, 2, 1, 7, 15]
    >>> ms.IF_MIB.ifAdminStatus(15).iid
    15
    >>> ms.IF_MIB.ifAdminStatus(15,16).iid
    [15, 16]

There is some operation on OID you can do:

    >>> [1,2,3,4] in OID(".1.2.3")
    True
    >>> OID(1,2,3) < OID(1,2,4)
    True
    >>> OID(1,2,3,4) < OID(1,2,4)
    True
    >>> OID("1.2.3.4")[3]
    4

You can bind values to an OID:

    >>> OID("1.2.3.4", value=18)
    <OID ::iso.2.3.4 = 18>
    >>> OID("1.2.3.4").set(18)
    <OID ::iso.2.3.4 = 18>
    >>> OID("1.2.3.4") << 18
    <OID ::iso.2.3.4 = 18>
    >>> a = OID("1.2.3.4")
    >>> a.set(18)
    <OID ::iso.2.3.4 = 18>
    >>> a.value
    18
    >>> a.value = 17
    >>> a.value
    17
    >>> a
    <OID ::iso.2.3.4 = 17>

With the help of the MIB, you get some smart setter for value:

    >>> ms.SNMPv2_MIB.sysDescr(0) << "Linux"
    <OID SNMPv2-MIB::sysDescr.0 = Linux>
    >>> ms.IF_MIB.ifInOctets(5) << 1457
    <OID IF-MIB::ifInOctets.5 (SNMPv2-SMI::Counter32) = 1457>
    >>> ms.IF_MIB.ifAdminStatus(15) << "up"
    <OID IF-MIB::ifAdminStatus.15 = up(1)>
    >>> ms.IF_MIB.ifAdminStatus(15) << "down"
    <OID IF-MIB::ifAdminStatus.15 = down(2)>
    >>> ms.IF_MIB.ifAdminStatus(15) << "testing"
    <OID IF-MIB::ifAdminStatus.15 = testing(3)>
    >>> ms.IF_MIB.ifAdminStatus(15) << "inexistent"
    Traceback (most recent call last):
    ...
    NotImplementedError: 'inexistent' does not exist in possible values for this OID
    >>> ms.IF_MIB.ifAdminStatus(15) << 2
    <OID IF-MIB::ifAdminStatus.15 = down(2)>
    >>> a = ms.IF_MIB.ifAdminStatus(15)
    >>> a.value = 3
    >>> a
    <OID IF-MIB::ifAdminStatus.15 = testing(3)>

With BITS, you have also some smart methods:

    >>> ms.load("P-BRIDGE-MIB")
    'P-BRIDGE-MIB'
    >>> ms.P_BRIDGE_MIB.dot1dDeviceCapabilities(0) << []
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = (empty)>
    >>> ms.P_BRIDGE_MIB.dot1dDeviceCapabilities(0) << 0
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1dExtendedFilteringServices(0)>
    >>> ms.P_BRIDGE_MIB.dot1dDeviceCapabilities(0) << [1, "dot1qSVLCapable"]
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1dTrafficClasses(1) dot1qSVLCapable(4)>
    >>> a = ms.P_BRIDGE_MIB.dot1dDeviceCapabilities(0) << ["dot1qIVLCapable", "dot1dLocalVlanCapable"]
    >>> a
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1qIVLCapable(3) dot1dLocalVlanCapable(7)>
    >>> a & 3
    True
    >>> a & 4
    False
    >>> a & "dot1dLocalVlanCapable"
    True
    >>> a & "dot1dTrafficClasses"
    False
    >>> a & ["dot1qIVLCapable", 7]
    True
    >>> a & ["dot1qIVLCapable", 7, 10]
    False
    >>> a -= 3
    >>> a
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1dLocalVlanCapable(7)>
    >>> a += [1, "dot1qSVLCapable"]
    >>> a
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1dTrafficClasses(1) dot1qSVLCapable(4) dot1dLocalVlanCapable(7)>
    >>> a.value
    [1, 4, 7]
    >>> a -= [4, 7, 9]
    >>> a
    <OID P-BRIDGE-MIB::dot1dDeviceCapabilities.0 = dot1dTrafficClasses(1)>

We handle timeticks as integers or as dates:

    >>> a = ms.SNMPv2_MIB.sysUpTime(0)
    >>> a << 77453614
    <OID SNMPv2-MIB::sysUpTime.0 (SNMPv2-SMI::TimeTicks) = 8 days, 23:08:56.14>
    >>> a.value
    datetime.timedelta(8, 83336, 140000)
    >>> from datetime import timedelta
    >>> a << timedelta(days=1, hours=23, seconds=78)
    <OID SNMPv2-MIB::sysUpTime.0 (SNMPv2-SMI::TimeTicks) = 1 day, 23:01:18.00>

We also handle IP addresses:

    >>> ms.load("RFC1213-MIB")
    'RFC1213-MIB'
    >>> ms.RFC1213_MIB.ipRouteNextHop(0,0,0,0) << "10.147.12.03"
    <OID RFC1213-MIB::ipRouteNextHop.0.0.0.0 (SNMPv2-SMI::IpAddress) = 10.147.12.3>
    >>> ms.RFC1213_MIB.ipRouteNextHop(0,0,0,1) << [27,18,19,33]
    <OID RFC1213-MIB::ipRouteNextHop.0.0.0.1 (SNMPv2-SMI::IpAddress) = 27.18.19.33>

Please note that "&" operator will return a boolean and "+=" and "-="
will alter and return the copy by adding or removing some bits. No
other operators are allowed. Something like that won't work:

    >>> "dot1dLocalVlanCapable" in a
    False
    >>> 7 in a
    False

The "in" operator is of the OID, not its value. You can't use any
other binary operators.
"""

import platform
import os.path
import socket

try:
    from ctypes import c_longdouble
except ImportError:
    # http://svn.python.org/projects/ctypes/branches/ctypes-1.1/
    raise ImportError("need ctypes 1.1.0 or more, with long double support")
from ctypes import *
from ctypes.util import find_library
from glob import glob
from datetime import timedelta

# Load and check version of libsmi
libname = find_library("smi")
if not libname:
    raise ImportError("unable to find SMI library")
try:
    lib = CDLL(libname)
except OSError:
    raise ImportError("unable to load %s" % libname)
minversion = [2,26,0]
curversion = [int(i) for i
              in c_char_p.in_dll(lib, "smi_library_version").value.split(":")]
if curversion < minversion:
    raise ImportError("needs at least libsmi %s" % ":".join(minversion))
if curversion[0] != minversion[0]:
    raise ImportError("needs libsmi v%d" % curversion[0])

# We need libc
libc = CDLL(find_library("c"))

# Prototypes
class SMIMODULE(Structure):
    _fields_ = [ ("name", c_char_p),
                 ("path", c_char_p),
                 ("organization", c_char_p),
                 ("contactinfo", c_char_p),
                 ("description", c_char_p),
                 ("reference", c_char_p),
                 ("language", c_int),
                 ("conformance", c_int) ]
class SMIVALUEU(Union):
    _fields_ = [ ("unsigned64", c_uint64),
                 ("integer64", c_int64),
                 ("unsigned32", c_uint32),
                 ("integer32", c_int32),
                 ("float32", c_float),
                 ("float64", c_double),
                 ("float128", c_longdouble),
                 ("oid", POINTER(c_uint)),
                 ("ptr", POINTER(c_byte)) ]
class SMIVALUE(Structure):
    _fields_ = [ ("basetype", c_int),
                 ("len", c_uint),
                 ("value", SMIVALUEU) ]
class SMINAMEDNUMBER(Structure):
    _fields_ = [ ("name", c_char_p),
                 ("value", SMIVALUE) ]
class SMINODE(Structure):
    _fields_ = [ ("name", c_char_p),
                 ("oidlen", c_int),
                 ("oid", POINTER(c_uint)),
                 ("decl", c_int),
                 ("access", c_int),
                 ("status", c_int),
                 ("format", c_char_p),
                 ("value", SMIVALUE),
                 ("units", c_char_p),
                 ("description", c_char_p),
                 ("reference", c_char_p),
                 ("indexkind", c_int),
                 ("implied", c_int),
                 ("create", c_int),
                 ("nodekind", c_int) ]
class SMITYPE(Structure):
    _fields_ = [ ("name", c_char_p),
                 ("basetype", c_int),
                 ("decl", c_int),
                 ("format", c_char_p),
                 ("value", SMIVALUE),
                 ("units", c_char_p),
                 ("status", c_int),
                 ("description", c_char_p),
                 ("reference", c_char_p) ]
SmiBaseType = { 0: "unknown",
                1: "integer32",
                2: "octetstring",
                3: "objectidentifier",
                4: "unsigned32",
                5: "integer64",
                6: "unsigned64",
                7: "float32",
                8: "float64",
                9: "float128",
                10: "enum",
                11: "bits",
                12: "pointer",
                }

lib.smiInit.argtypes = [c_char_p]
lib.smiIsLoaded.argtypes = [c_char_p]
lib.smiSetPath.argtypes = [c_char_p]
lib.smiGetPath.argtypes = []
lib.smiGetPath.restype = c_char_p
lib.smiLoadModule.argtypes = [c_char_p]
lib.smiLoadModule.restype = c_char_p
lib.smiGetModule.argtypes = [c_char_p]
lib.smiGetModule.restype = POINTER(SMIMODULE)
lib.smiGetFirstModule.argtypes = []
lib.smiGetFirstModule.restype = POINTER(SMIMODULE)
lib.smiGetNextModule.argtypes = [POINTER(SMIMODULE)]
lib.smiGetNextModule.restype = POINTER(SMIMODULE)
lib.smiGetModuleIdentityNode.argtypes = [POINTER(SMIMODULE)]
lib.smiGetModuleIdentityNode.restype = POINTER(SMINODE)
lib.smiGetNode.argtypes = [POINTER(SMIMODULE), c_char_p]
lib.smiGetNode.restype = POINTER(SMINODE)
lib.smiGetNodeByOID.argtypes = [c_uint, POINTER(c_uint)]
lib.smiGetNodeByOID.restype = POINTER(SMINODE)
lib.smiGetFirstNode.argtypes = [POINTER(SMIMODULE), c_uint]
lib.smiGetFirstNode.restype = POINTER(SMINODE)
lib.smiGetNextNode.argtypes = [POINTER(SMINODE), c_uint]
lib.smiGetNextNode.restype = POINTER(SMINODE)
lib.smiRenderOID.argtypes = [c_uint, POINTER(c_uint), c_int]
lib.smiRenderOID.restype = c_void_p # Not c_char_p, we need to free it after use
lib.smiGetNodeType.argtypes = [POINTER(SMINODE)]
lib.smiGetNodeType.restype = POINTER(SMITYPE)
lib.smiRenderType.argtypes = [POINTER(SMITYPE), c_int]
lib.smiRenderType.restype = c_void_p # Not c_char_p, we need to free it after use
lib.smiRenderValue.argtypes = [POINTER(SMIVALUE), POINTER(SMITYPE), c_int]
lib.smiRenderValue.restype = c_void_p # Not c_char_p, we need to free it after use
lib.smiGetFirstNamedNumber.argtypes = [POINTER(SMITYPE)]
lib.smiGetFirstNamedNumber.restype = POINTER(SMINAMEDNUMBER)
lib.smiGetNextNamedNumber.argtypes = [POINTER(SMINAMEDNUMBER)]
lib.smiGetNextNamedNumber.restype = POINTER(SMINAMEDNUMBER)
SMIERRORHANDLER = CFUNCTYPE(None, c_char_p, c_int, c_int, c_char_p, c_char_p)
lib.smiSetErrorHandler.argtypes = [SMIERRORHANDLER]
lib.smiSetErrorHandler.restype = None
lib.smiSetErrorLevel.argtypes = [c_int]
lib.smiSetErrorLevel.restype = None
lib.smiGetFlags.argtypes = []
lib.smiGetFlags.restype = c_int
lib.smiSetFlags.argtypes = [c_int]
lib.smiSetFlags.restype = None

# Exceptions
class SMIException(Exception): pass
class SMINoSuchModule(SMIException):

    def __init__(self, module):
        self.module = module
    
    def __str__(self):
        return "module %s does not exist" % self.module

class SMINoSuchOID(SMIException):

    def __init__(self, oid):
        self.oid = oid

    def __str__(self):
        return "%r cannot be converted into oid" % self.oid

class SMIModuleLoadError(SMIException): pass
class SMIParseError(SMIException):
    
    def __init__(self, path, line, severity, message, tag):
        self.path = path
        self.line = line
        self.severity = severity
        self.message = message
        self.tag = tag

    def __str__(self):
        if self.path:
            return "error while parsing %s:%d: %s" % (self.path, self.line,
                                                      self.message)
        return "parse error: %s" % self.message

# Initialize SMI
result = lib.smiInit("snimpy")
if result != 0:
    raise ImportError("unable to initialize libsmi")

# Setup error handler
def handle_parse_error(path, line, severity, message, tag):
    if severity < 0:
        raise SMIParseError(path, line, severity, message, tag)
lib.smiSetErrorLevel(1)
flags = lib.smiGetFlags() | 0x2000 | 0x4000 | 0x8000
lib.smiSetFlags(flags)
#lib.smiSetErrorHandler(SMIERRORHANDLER(handle_parse_error))

class OID:
    """Representation for one OID"""

    def __init__(self, *args, **kwargs):
        oid = []
        value = kwargs.get("value", None)
        for a in args:
            if type(a) is list or type(a) is tuple:
                oid.extend([int(u) for u in a])
            elif type(a) is int or type(a) is long:
                oid.append(int(a))
            elif isinstance(a, Node):
                oid.extend([int(a.node.oid[i]) for i in range(0, a.node.oidlen)])
            elif type(a) is str:
                oid.extend([int(i) for i in a.split(".") if i != ""])
            else:
                raise ValueError("don't know how to decode %r" % a)
        self.oid = oid
        array = (c_uint * len(self.oid))(*self.oid)
        self.type = None
        self.__dict__["value"] = None
        self._value = None
        self.node = lib.smiGetNodeByOID(len(self.oid), array)
        if self.node:
            self.node = self.node.contents
            self.__doc__ = self.node.description
            self.iid = self.oid[self.node.oidlen:]
            if len(self.iid) == 1:
                self.iid = self.iid[0]
            elif len(self.iid) == 0:
                self.iid = None
            self.type = lib.smiGetNodeType(byref(self.node))
            if self.type:
                self.type = self.type.contents
            else:
                self.type = None
        if value is not None:
            self.set(value)

    def __cmp__(self, other):
        if not isinstance(other, OID):
            other = OID(other)
        if self.oid < other.oid:
            return -1
        if self.oid == other.oid:
            return 0
        return 1

    def __hash__(self):
        return tuple(self.oid).__hash__()

    def __contains__(self, item):
        """Check if the given item is a suboid.

        @param item: suboid to check
        """
        if not isinstance(item, OID):
            try:
                item = OID(item)
            except ValueError:
                return False
        if len(item.oid) < len(self.oid):
            return False
        return item.oid[:len(self.oid)] == self.oid

    def __len__(self):
        return len(self.oid)

    def __getitem__(self, nb):
        return self.oid[nb]

    def __iter__(self):
        return self.oid.__iter__()

    def __repr__(self):
        value = ""
        type = ""
        oid = ""
        if self.type and self.type.name:
            s = lib.smiRenderType(byref(self.type), 0xff)
            t = c_char_p(s).value[:]
            libc.free(s)
            type = " (%s)" % t
        if self.value is not None:
            if self._value is None or self.type is None:
                value = " = %r" % self.value
            else:
                if SmiBaseType.get(self.type.basetype, None) == "unsigned32" and \
                        self.type.name == "TimeTicks":
                    value = " = %d day%s, %02d:%02d:%02d.%02d" % (self.value.days,
                                                                  self.value.days > 1 and "s" or "",
                                                                  self.value.seconds / 3600,
                                                                  (self.value.seconds % 3600)/60,
                                                                  self.value.seconds % 60,
                                                                  self.value.microseconds / 10000)
                else:
                    v = lib.smiRenderValue(byref(self._value),
                                           byref(self.type), 0xff)
                    t = c_char_p(v).value[:]
                    libc.free(v)
                    if t != "":
                        value = " = %s" % t
                    else:
                        value = " = (empty)"
        return '<OID %s%s%s>' % (self, type, value)

    def __str__(self):
        array = (c_uint * len(self.oid))(*self.oid)
        r = lib.smiRenderOID(len(self.oid), array, 0xff)
        if not r:
            raise SMINoSuchOID(self.oid)
        result = c_char_p(r).value[:]
        libc.free(r)
        return result

    def getNamedNumber(self, name):
        """Retrieve index of a named number.

        @param name: name of the named number
        @return: corresponding number
        """
        found = None
        n = lib.smiGetFirstNamedNumber(byref(self.type))
        while n:
            if n.contents.name == name:
                found = n.contents.value.value.integer32
                break
            n = lib.smiGetNextNamedNumber(n)
        if found is None:
            raise ValueError("%r does not exist in possible values for this OID" % name)
        return found

    def set(self, value):
        """Bind a value to this OID.

        We try to be smart. If we know the type of the OID, we will
        accept a large range of types for value. Otherwise, we try to
        guess the type of the OID with the help of the type of value.
        """
        if not self.type:
            # Don't know the type of this OID
            if type(value) not in [float, str, int, long] and not isinstance(value, OID):
                raise ValueError("don't know how to handle %r" % value)
            self.__dict__["value"] = value
            self._value = None
            return self
        if SmiBaseType.get(self.type.basetype, None) in ["float32",
                                                         "float64",
                                                         "float128"]:
            self.__dict__["value"] = float(value)
            kw = {self.type.basetype: self.value}
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=0, # It seems that len is not used for simple datatype
                                   value=SMIVALUE(**kw))
        if SmiBaseType.get(self.type.basetype, None) == "pointer":
            raise NotImplementedError("pointer datatype is not implemented")
        if SmiBaseType.get(self.type.basetype, None) == "integer32":
            self.__dict__["value"] = int(value)
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=sizeof(c_int32),
                                   value=SMIVALUEU(integer32=self.value))
        elif SmiBaseType.get(self.type.basetype) == "unsigned32":
            if self.type.name == "TimeTicks":
                if type(value) in [int, long]:
                    self.__dict__["value"] = timedelta(milliseconds=value*10)
                elif isinstance(value, timedelta):
                    self.__dict__["value"] = value
                else:
                    raise ValueError("timeticks need to be int or timedelta")
                value = self.value.days * 24 * 60 * 60 * 100 + \
                    self.value.seconds * 100 + self.value.microseconds / 10000
            else:
                self.__dict__["value"] = int(value)
                value = int(value)
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=sizeof(c_uint32),
                                   value=SMIVALUEU(unsigned32=value))
        elif SmiBaseType.get(self.type.basetype, None) == "integer64":
            self.__dict__["value"] = int(value)
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=sizeof(c_int64),
                                   value=SMIVALUEU(integer64=self.value))
        elif SmiBaseType.get(self.type.basetype, None) == "unsigned64":
            self.__dict__["value"] = int(value)
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=sizeof(c_uint64),
                                   value=SMIVALUEU(unsigned64=self.value))
        elif SmiBaseType.get(self.type.basetype, None) == "objectidentifier":
            if not isinstance(value, OID):
                self.__dict__["value"] = OID(value)
            else:
                self.__dict__["value"] = value
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=len(self.value),
                                   value=SMIVALUEU(oid=(c_uint*len(self.value))(*self.value)))
        elif SmiBaseType.get(self.type.basetype, None) == "enum":
            if type(value) in [int, long]:
                self.__dict__["value"] = value
            elif type(value) is str:
                found = self.getNamedNumber(value)
                self.__dict__["value"] = found
            else:
                raise ValueError("OID is enum but don't know how to handle %r" % value)
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=sizeof(c_int32),
                                   value=SMIVALUEU(integer32=self.value))
        elif SmiBaseType.get(self.type.basetype, None) == "octetstring":
            if self.type.name == "IpAddress":
                if type(value) == str:
                    try:
                        self.__dict__["value"] = socket.inet_ntoa(socket.inet_aton(value))
                    except:
                        raise ValueError("%r is not an IP address" % value)
                elif type(value) in [list, tuple]:
                    try:
                        self.__dict__["value"] = socket.inet_ntoa(
                            socket.inet_aton(".".join(map(str,value))))
                    except:
                        raise ValueError("%r is not an IP address" % value)
                else:
                    raise ValueError("%r is not an IP address" % value)
                value = socket.inet_aton(self.value)
                l = len(value)
            else:
                value = str(value)
                self.__dict__["value"] = value
                value = value + '\x00'
                l = len(value) - 1
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=l,
                                   value=SMIVALUEU(
                    ptr=(c_byte*len(value))(*[ord(i) for i in value])))
        elif SmiBaseType.get(self.type.basetype, None) == "bits":
            self.__dict__["value"] = []
            self += value
        else:
            raise ValueError("unknown base type (%d)" % self.type.basetype)
        return self
    __lshift__ = set

    def __and__(self, other):
        """Check presence of some bits in BITS field"""
        if SmiBaseType.get(self.type.basetype, None) != "bits":
            return NotImplementedError("operator only usable on bits")
        if type(other) in [long, int, str]:
            other = [other]
        if type(other) in [list, tuple]:
            for v in other:
                if type(v) is str:
                    # Bit name
                    found = self.getNamedNumber(v)
                    if found not in self.value:
                        return False
                else:
                    v = int(v)
                    if v not in self.value:
                        return False
            return True
        else:
            raise NotImplementedError("only int, str and lists are allowed for bit operations")

    def __iadd__(self, other):
        """Add bits to a BITs field"""
        if SmiBaseType.get(self.type.basetype, None) != "bits":
            return NotImplementedError("operator only usable on bits")
        if type(other) in [long, int, str]:
            other = [other]
        if type(other) in [list, tuple]:
            newvalue = []
            bits = []
            for v in other + self.value:
                if type(v) is str:
                    # Bit name
                    found = self.getNamedNumber(v)
                    if found not in newvalue:
                        if len(bits) <= found/8:
                            bits.extend([0]*(found/8 - len(bits) + 1))
                        bits[found/8] |= 1<<(7-(found%8))
                        newvalue.append(found)
                else:
                    # Bit number
                    v = int(v)
                    if v not in newvalue:
                        if len(bits) <= v/8:
                            bits.extend([0]*(v/8 - len(bits) + 1))
                        bits[v/8] |= 1<<(7-(v%8))
                        newvalue.append(v)
            self.__dict__["value"] = newvalue
            self._value = SMIVALUE(basetype=self.type.basetype,
                                   len=len(bits),
                                   value=SMIVALUEU(ptr=(c_byte*len(bits))(*bits)))
        else:
            raise NotImplementedError("only int, str and lists are allowed to specify bits")
        return self

    def __isub__(self, other):
        """Remove some bits from BITS field"""
        if SmiBaseType.get(self.type.basetype, None) != "bits":
            return NotImplementedError("operator only usable on bits")
        if type(other) in [long, int, str]:
            other = [other]
        if type(other) in [list, tuple]:
            newvalue = self.value
            for v in other:
                if type(v) is str:
                    found = self.getNamedNumber(v)
                    try:
                        newvalue.remove(found)
                    except ValueError:
                        pass
                else:
                    v = int(v)
                    try:
                        newvalue.remove(v)
                    except ValueError:
                        pass
            self.set(newvalue)
        else:
            raise NotImplementedError("only int, str and lists are allowed to specify bits")
        return self

    def __setattr__(self, name, value):
        if name == "value":
            self.set(value)
        else:
            self.__dict__[name] = value

class Node:
    """Representation for one node"""

    def __init__(self, node, module):
        self.node = node
        self.module = module
        self.name = node.name
        self.__doc__ = node.description

    def __repr__(self):
        return '<Node "%s" of module %s>' % (self.name,
                                             self.module.name)

    def __call__(self, *args):
        base = [self.node.oid[i] for i in range(0, self.node.oidlen)]
        return OID(base, *args)

class Module:
    """Representation for one module"""

    def __init__(self, module):
        self.module = lib.smiGetModule(module)
        if not self.module:
            raise SMINoSuchModule(module)
        self.module = self.module.contents
        self.name = self.module.name
        self.__doc__ = self.module.description
        node = lib.smiGetFirstNode(byref(self.module), 0xffff)
        while node:
            if node.contents.name and node.contents.name not in self.__dict__:
                name = "".join([x.isalnum() and x or "_"
                                for x in node.contents.name])
                self.__dict__[name] = Node(node.contents,
                                           self.module)
            node = lib.smiGetNextNode(node, 0xffff)
            

    def __repr__(self):
        return '<Module %s loaded from "%s">' % (self.name,
                                                 self.module.path)

class FakeModule:
    """Placeholder for a real module.

    This is done to avoid to waste memory by instanciating a complete
    module while never using it.
    """

    def __init__(self, name):
        self.name = name

class ModuleStore(object):
    """Store for parsed MIB modules.

    All instances of this class would behave in the same way since the
    work is done by a single instance of libsmi library.
    """

    def __init__(self):
        self._update_module_list()

    def __getattribute__(self, name):
        if name == "path":
            return lib.smiGetPath()
        real = object.__getattribute__(self, name)
        if isinstance(real, FakeModule):
            return Module(real.name)
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == "path":
            lib.smiSetPath(value)
        else:
            object.__setattr__(self, name, value)

    def _update_module_list(self):
        """Include the available modules into the name space of the given object.

        We use this trick to make modules available to builtin
        function C{dir()}.
        """
        mod = lib.smiGetFirstModule()
        while mod:
            name = "".join([x.isalnum() and x or "_"
                            for x in mod.contents.name])
            if name not in self.__dict__ or isinstance(self.__dict__[name],
                                                       FakeModule):
                self.__dict__[name] = FakeModule(mod.contents.name)
            mod = lib.smiGetNextModule(mod)

    def module(self, module):
        """Access to a module given its name.

        @param module: module name
        """
        return Module(module)
    m = module

    def load(self, module):
        """Load the given module.

        The module is first globbed to allow to load multiple modules
        at once. Therefore, C{module} can be either a module name like
        C{BRIDGE-MIB} or a path to a file or a path to multiple files
        using wildcards.

        We try to expand "~" and variables.

        If multiple modules are to be loaded, this function does not
        raise any error but return the list of modules loaded. If only
        one module is about to be loaded, the failure of this function
        will raise an exception if the module cannot be loaded.
        """

        if type(module) is str:
            module = os.path.expandvars(os.path.expanduser(module))
            modules = glob(module)
            if not modules:
                modules = [ module ]
        else:
            modules = list(module)
        if len(modules) == 1 and modules[0] == module:
            name = lib.smiLoadModule(module)
            if not name:
                raise SMIModuleLoadError("unable to load module %s" % module)
            self._update_module_list()
            return name
        success = []
        for m in modules:
            name = lib.smiLoadModule(m)
            if name:
                success.append(name)
        self._update_module_list()
        return success

ms = ModuleStore()
