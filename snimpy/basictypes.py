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
Snimpy will use the types defined in this module to make a bridge
between the MIB and SNMP.
"""

import struct
import socket
from datetime import timedelta

import mib, snmp

class Type:
    """Base class for all types"""

    def __init__(self, entity, value):
        """Create a new typed value

        @param entity: L{mib.Entity} instance
        @param value: value to set
        """
        if not isinstance(entity, mib.Entity):
            raise TypeError("%r not a mib.Entity instance" % entity)
        if entity.type != self.__class__:
            raise ValueError("MIB node is %r. We are %r" % (entity.type,
                                                            self.__class))
        self.entity = entity
        self.set(value)

    def set(self, value):
        raise NotImplementedError

    def pack(self):
        raise NotImplementedError

    def __repr__(self):
        r = repr(self.value)
        if r.startswith("<"):
            return '<%s = %s>' % (self.__class__.__name__,
                                  r)
        else:
            return '%s(%s)' % (self.__class__.__name__,
                               r)

class IpAddress(Type):
    """Class for IP address"""

    def set(self, value):
        if type(value) in [list, tuple]:
            value = ".".join([str(a) for a in value])
        try:
            value = socket.inet_ntoa(socket.inet_aton(value))
        except:
            raise ValueError("%r is not a valid IP" % value)
        self.value = [int(a) for a in value.split(".")]

    def pack(self):
        return (snmp.ASN_IPADDRESS,
                socket.inet_aton(".".join(["%d" % x for x in self.value])))

    def __str__(self):
        return ".".join([str(a) for a in self.value])

    def __cmp__(self, other):
        if not isinstance(other, IpAddress):
            try:
                other = IpAddress(self.entity, other)
            except:
                raise NotImplementedError
        if self.value == other.value:
            return 0
        if self.value < other.value:
            return -1
        return 1

    def __getitem__(self, nb):
        return self.value[nb]

class String(Type):
    """Class for any string"""

    def set(self, value):
        self.value = str(value)

    def pack(self):
        return (snmp.ASN_OCTET_STR, self.value)

    def __str__(self):
        return self.value

    def __getattr__(self, attr):
        # Ugly hack to be like an string
        return getattr(str(self), attr)

    def __ior__(self, value):
        nvalue = [ord(u) for u in self.value]
        if type(value) not in [tuple, list]:
            value = [value]
        for v in value:
            if type(v) is not int:
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < v/8 + 1:
                nvalue.extend([0] * (v/8 + 1 - len(self.value)))
            nvalue[v/8] |= 1 << (7-v%8)
        self.value = "".join([chr(i) for i in nvalue])
        return self

    def __isub__(self, value):
        nvalue = [ord(u) for u in self.value]
        if type(value) not in [tuple, list]:
            value = [value]
        for v in value:
            if type(v) is not int:
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < v/8 + 1:
                continue
            nvalue[v/8] &= ~(1 << (7-v%8))
        self.value = "".join([chr(i) for i in nvalue])
        return self

    def __and__(self, value):
        nvalue = [ord(u) for u in self.value]
        if type(value) not in [tuple, list]:
            value = [value]
        for v in value:
            if type(v) is not int:
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < v/8 + 1:
                return False
            if not(nvalue[v/8] & (1 << (7-v%8))):
                return False
        return True

class Integer(Type):
    """Class for any integer"""

    def set(self, value):
        self.value = long(value)

    def pack(self):
        if self.value >= (1L << 64):
            raise OverflowError("too large to be packed")
        if self.value >= (1L << 32):
            # Pack in a 64 bit counter
            return (snmp.ASN_OCTET_STR,
                    struct.pack("LL",
                                self.value/(1L << 32),
                                self.value%(1L << 32)))
        if self.value >= 0:
            return (snmp.ASN_INTEGER, struct.pack("L", self.value))
        if self.value >= -(1L << 31):
            return (snmp.ASN_INTEGER, struct.pack("l", self.value))
        raise OverflowError("too small to be packed")

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __getattr__(self, attr):
        # Ugly hack to be like an integer
        return getattr(long(self), attr)

class Enum(Type):
    """Class for enumeration"""

    def set(self, value):
        if value in self.entity.enum:
            self.value = value
            return
        for (k, v) in self.entity.enum.iteritems():
            if (v == value):
                self.value = k
                return
        raise ValueError("%r is not a valid value for %s" % (value,
                                                             self.entity))

    def pack(self):
        return (snmp.ASN_INTEGER, struct.pack("l", self.value))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            try:
                other = self.__class__(self.entity, other)
            except:
                raise NotImplementedError
        return self.value == other.value

    def __str__(self):
        return "%s(%d)" % (self.entity.enum[self.value], self.value)

class Oid(Type):
    """Class for OID"""

    def set(self, value):
        if type(value) in [list, tuple]:
            self.value = tuple([int(v) for v in value])
        elif type(value) is str:
            self.value = tuple([int(i) for i in value.split(".") if i])
        elif isinstance(value, mib.Entity):
            self.value = tuple(value.oid)
        else:
            raise TypeError("don't know how to convert %r to OID" % value)
            
    def pack(self):
        return (snmp.ASN_OBJECT_ID, "".join([struct.pack("l", x) for x in self.value]))
                 
    def __cmp__(self, other):
        if not isinstance(other, Oid):
            other = Oid(self.entity, other)
        if tuple(self.value) == tuple(other.value):
            return 0
        if self.value > other.value:
            return 1
        return -1

    def __contains__(self, item):
        """Test if item is a sub-oid of this OID"""
        if not isinstance(item, Oid):
            item = Oid(self.entity, item)
        return tuple(item.value[:len(self.value)]) == \
            tuple(self.value[:len(self.value)])


class Boolean(Enum):
    """Class for boolean"""

    def set(self, value):
        if type(value) is bool:
            if value:
                Enum.set(self, "true")
            else:
                Enum.set(self, "false")
        else:
            Enum.set(self, value)

    def __getattr__(self, attr):
        if self.value == 1:
            return getattr(True, attr)
        return getattr(False, attr)

class Timeticks(Type):
    """Class for timeticks"""

    def set(self, value):
        if type(value) is int:
            # Value in centiseconds
            self.value = timedelta(0, value/100.)
        elif isinstance(value, timedelta):
            self.value = value
        else:
            raise TypeError("dunno how to handle %r" % value)

    def pack(self):
        return (snmp.ASN_INTEGER,
                struct.pack("l",
                            self.value.days*3600*24*100 + self.value.seconds*100 +
                            self.value.microseconds/10000))

    def __str__(self):
        return str(self.value)

    def __cmp__(self, other):
        if type(other) is int:
            other = timedelta(0, other/100.)
        elif not isinstance(other, timedelta):
            raise NotImplementedError("only compare to int or timedelta")
        if self.value == other:
            return 0
        if self.value < other:
            return -1
        return 1

    def __eq__(self, other):
        return self.__cmp__(other) == 0
    def __lt__(self, other):
        return self.__cmp__(other) < 0
    def __gt__(self, other):
        return self.__cmp__(other) > 0

class Bits(Type):
    """Class for bits"""

    def set(self, value):
        bits = []
        if type(value) not in [tuple, list]:
            value = [value]
        for v in value:
            found = False
            if v in self.entity.enum:
                if v not in bits:
                    bits.append(v)
                    found = True
            else:
                for (k, t) in self.entity.enum.iteritems():
                    if (t == v):
                        if k not in bits:
                            bits.append(k)
                            found = True
                            break
            if not found:
                raise ValueError("%r is not a valid bit value" % v)
        bits.sort()
        self.value = bits

    def pack(self):
        string = []
        for b in self.value:
            if len(string) < b/16 + 1:
                string.extend([0]*(b/16 - len(string)+1))
            string[b/16] |= 1 << (7 - b%16)
        return (snmp.ASN_OCTET_STR, "".join([chr(x) for x in string]))

    def __eq__(self, other):
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        return self.value == other.value

    def __str__(self):
        result = []
        for b in self.value:
            result.append("%s(%d)" % (self.entity.enum[b], b))
        return ", ".join(result)

    def __and__(self, other):
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        for o in other.value:
            if o not in self.value:
                return False
        return True

    def __ior__(self, other):
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        for o in other.value:
            if o not in self.value:
                self.value.append(o)
        self.value.sort()
        return self

    def __isub__(self, other):
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        for o in other.value:
            if o in self.value:
                self.value.remove(o)
        return self

def build(mibname, entity, value):
    """Build a new basic type with the given value.

    @param mibname: MIB to use to locate the entity
    @param entity: entity that will be attached to this type
    @param value: initial value to set for the type
    @return: a Type instance
    """
    m = mib.get(mibname, entity)
    t = m.type(m, value)
    return t
