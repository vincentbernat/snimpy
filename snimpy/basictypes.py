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

    consume = 0                 # Consume all suboid if built from OID

    def __init__(self, entity, value):
        """Create a new typed value

        @param entity: L{mib.Entity} instance
        @param value: value to set
        """
        self.value = 0          # To avoid some recursive loop
        if not isinstance(entity, mib.Entity):
            raise TypeError("%r not a mib.Entity instance" % entity)
        if entity.type != self.__class__:
            raise ValueError("MIB node is %r. We are %r" % (entity.type,
                                                            self.__class))
        self.entity = entity
        if isinstance(value, Type):
            self.set(value.value)
        else:
            self.set(value)

    def set(self, value):
        raise NotImplementedError

    def pack(self):
        raise NotImplementedError

    def toOid(self):
        """Convert to an OID.

        If this function is implemented, then class function fromOid
        should also be implemented as the "invert" function of this one.

        This function only works if the entity is used as an index!
        Otherwise, it should raises NotImplementedError.

        @return: OID that can be used as index
        """
        raise NotImplementedError

    @classmethod
    def fromOid(cls, entity, oid):
        """Create instance from an OID.

        This is the sister function of toOid.

        @param oid: OID to use to create an instance
        @param entity: MIB entity we want to instantiate
        @return: a couple C{(l, v)} with C{l} the number of suboid
           needed to create the instance and v the instance created from
           the OID
        """
        raise NotImplementedError

    def display(self):
        return str(self)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        try:
            return '<%s: %s>' % (self.__class__.__name__,
                                 self.display())
        except:
            return '<%s ????>' % self.__class__.__name__

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

    def toOid(self):
        return tuple(self.value)

    @classmethod
    def fromOid(cls, entity, oid):
        if len(oid) < 4:
            raise ValueError("%r is too short for an IP address" % (oid,))
        return (4, cls(entity, oid[:4]))

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

    @classmethod
    def _fixedOrImplied(cls, entity):
        """Determine if the given entity is a fixed-len string or an
        implied var-len string.

        @param entity: entity to check
        @return: C{fixed} if it is fixed-len, C{implied} if implied var-len, C{False} otherwise
        """
        if not(entity.ranges) or type(entity.ranges) is not tuple:
            # Fixed length
            return "fixed"

        # We have a variable-len string. We need to know if it is impled.
        try:
            table = entity.table
        except:
            raise NotImplementedError("%r is not an index of a table" % entity)
        indexes = [str(a) for a in table.index]
        if str(entity) not in indexes:
            raise NotImplementedError("%r is not an index of a table" % entity)
        if str(entity) != indexes[-1] or not table.implied:
            # This index is not implied
            return False
        return "implied"

    def toOid(self):
        # To convert properly to OID, we need to know if it is a
        # fixed-len string, an implied string or a variable-len
        # string.
        if self._fixedOrImplied(self.entity):
            return tuple(ord(a) for a in self.value)
        return tuple([len(self.value)] + [ord(a) for a in self.value])

    @classmethod
    def fromOid(cls, entity, oid):
        type = cls._fixedOrImplied(entity)
        if type == "implied":
            # Eat everything
            return (len(oid), cls(entity,"".join([chr(x) for x in oid])))
        if type == "fixed":
            l = entity.ranges
            if len(oid) < l:
                raise ValueError(
                    "%r is too short for wanted fixed string (need at least %d)" % (oid, l))
            return (l, cls(entity,"".join([chr(x) for x in oid[:l]])))
        # This is var-len
        if not oid:
            raise ValueError("empty OID while waiting for var-len string")
        l = oid[0]
        if len(oid) < l + 1:
            raise ValueError(
                "%r is too short for variable-len string (need at least %d)" % (oid, l))
        return (l+1, cls(entity,"".join([chr(x) for x in oid[1:(l+1)]])))

    def _display(self, fmt):
        i = 0               # Position in self.value
        j = 0               # Position in fmt
        result = ""
        while i < len(self.value):
            if j < len(fmt):
                # repeater
                if fmt[j] == "*":
                    repeat = ord(self.value[i])
                    j += 1
                    i += 1
                else:
                    repeat = 1
                # length
                length = ""
                while fmt[j].isdigit():
                    length += fmt[j]
                    j += 1
                length = int(length)
                # format
                format = fmt[j]
                j += 1
                # seperator
                if j < len(fmt) and \
                        fmt[j] != "*" and not fmt[j].isdigit():
                    sep = fmt[j]
                    j += 1
                else:
                    sep = ""
                # terminator
                if j < len(fmt) and \
                        fmt[j] != "*" and not fmt[j].isdigit():
                    term = fmt[j]
                    j += 1
                else:
                    term = ""
            # building
            for r in range(repeat):
                bytes = self.value[i:i+length]
                i += length
                if format in ['o', 'x', 'd']:
                    if length > 8:
                        raise ValueError(
                            "don't know how to handle integers more than 4 bytes long")
                    bytes = "\x00"*(4-length) + bytes
                    number = struct.unpack("!l", bytes)[0]
                    if format == "o":
                        result += "%s" % oct(number)
                    elif format == "x":
                        result += "%s" % hex(number)[2:]
                    else:       # format == "d":
                        result += "%s" % str(number)
                else: # should be a, but can be something else like t
                    result += bytes
                result += sep
            if sep and term:
                result = result[:-1]
            result += term
        if term or sep:
            result = result[:-1]
        return result
        
    def display(self):
        if self.entity.fmt:
            return self._display(self.entity.fmt)
        if "\\x" not in repr(self.value):
            return self.value
        return "0x" + " ".join([("0%s" % hex(ord(a))[2:])[-2:] for a in self.value])

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
            if isinstance(v, Integer):
                v = int(v)
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
            if isinstance(v, Integer):
                v = int(v)
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
            if isinstance(v, Integer):
                v = int(v)
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

    def toOid(self):
        return (self.value,)

    @classmethod
    def fromOid(cls, entity, oid):
        if len(oid) < 1:
            raise ValueError("%r is too short for an integer" % (oid,))
        return (1, cls(entity, oid[0]))

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __str__(self):
        return str(self.value)

    def display(self):
        if self.entity.fmt:
            if self.entity.fmt[0] == "x":
                return hex(self.value)
            if self.entity.fmt[0] == "o":
                return oct(self.value)
            if self.entity.fmt[0] == "b":
                if self.value == 0:
                    return "0"
                if self.value > 0:
                    v = self.value
                    r = ""
                    while v > 0:
                        r = str(v%2) + r
                        v = v>>1
                    return r
            elif self.entity.fmt[0] == "d" and \
                    len(self.entity.fmt) > 2 and \
                    self.entity.fmt[1] == "-":
                dec = int(self.entity.fmt[2:])
                result = str(self.value)
                if len(result) < dec + 1:
                    result = "0"*(dec + 1 - len(result)) + result
                return "%s.%s" % (result[:-2], result[-2:])
        return str(self.value)

    def __getattr__(self, attr):
        # Ugly hack to be like an integer
        return getattr(self.value, attr)

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

    def toOid(self):
        return (self.value,)

    @classmethod
    def fromOid(cls, entity, oid):
        if len(oid) < 1:
            raise ValueError("%r is too short for an enumeration" % (oid,))
        return (1, cls(entity, oid[0]))

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

    def toOid(self):
        return self.value

    @classmethod
    def fromOid(cls, entity, oid):
        try:
            table = entity.table
        except:
            raise NotImplementedError("%r is not an index of a table" % entity)
        indexes = [str(a) for a in table.index]
        if str(entity) not in indexes:
            raise NotImplementedError("%r is not an index of a table" % entity)
        if str(entity) != indexes[-1] or not table.implied:
            # This index is not implied. We need the len
            if len(oid) < 1:
                raise ValueError("%r is too short for a not implied index" % entity)
            l = oid[0]
            if len(oid) < l + 1:
                raise ValueError("%r has an incorrect size (needs at least %d)" % (oid, l))
            return (l+1, cls(entity, oid[1:(l+1)]))
        else:
            # Eat everything
            return (len(oid), cls(entity, oid))

    def __str__(self):
        return ".".join([str(x) for x in self.value])
                 
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
        if type(value) is int or type(value) is long:
            # Value in centiseconds
            self.value = timedelta(0, value/100.)
        elif isinstance(value, timedelta):
            self.value = value
        else:
            raise TypeError("dunno how to handle %r (%s)" % (value, type(value)))

    def __int__(self):
        return self.value.days*3600*24*100 + self.value.seconds*100 + \
            self.value.microseconds/10000

    def toOid(self):
        return (int(self),)

    @classmethod
    def fromOid(cls, entity, oid):
        if len(oid) < 1:
            raise ValueError("%r is too short for a timetick" % (oid,))
        return (1, cls(entity, oid[0]))

    def pack(self):
        return (snmp.ASN_INTEGER,
                struct.pack("l",
                            int(self)))

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
        tryalternate = False
        if type(value) is str:
            for i,x in enumerate(value):
                if ord(x) == 0:
                    continue
                for j in range(8):
                    if ord(x) & (1 << (7-j)):
                        if j not in self.entity.enum:
                            tryalternate = True
                            break
                        bits.append(j)
                if tryalternate:
                    break
            self.value = bits
            if not tryalternate:
                return
            else:
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
        if type(other) is str:
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        return self.value == other.value

    def __str__(self):
        result = []
        for b in self.value:
            result.append("%s(%d)" % (self.entity.enum[b], b))
        return ", ".join(result)

    def __and__(self, other):
        if type(other) is str:
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        for o in other.value:
            if o not in self.value:
                return False
        return True

    def __ior__(self, other):
        if type(other) is str:
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        for o in other.value:
            if o not in self.value:
                self.value.append(o)
        self.value.sort()
        return self

    def __isub__(self, other):
        if type(other) is str:
            other = [other]
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
