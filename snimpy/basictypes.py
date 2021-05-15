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
This module is aimed at providing Pythonic representation of
various SNMP types. Each SMIv2 type is mapped to a corresponding class
which tries to mimic a basic type from Python. For example, display
strings are like Python string while SMIv2 integers are just like
Python integers. This module is some kind of a hack and its use
outside of *Snimpy* seems convoluted.
"""

import struct
import re
import ipaddress
from datetime import timedelta
from pysnmp.proto import rfc1902

from snimpy import mib


def ordering_with_cmp(cls):
    ops = {'__lt__': lambda self, other: self.__cmp__(other) < 0,
           '__gt__': lambda self, other: self.__cmp__(other) > 0,
           '__le__': lambda self, other: self.__cmp__(other) <= 0,
           '__ge__': lambda self, other: self.__cmp__(other) >= 0,
           '__eq__': lambda self, other: self.__cmp__(other) == 0,
           '__ne__': lambda self, other: self.__cmp__(other) != 0}
    for opname, opfunc in ops.items():
        opfunc.__name__ = opname
        opfunc.__doc__ = getattr(int, opname).__doc__
        setattr(cls, opname, opfunc)
    return cls


class Type:

    """Base class for all types."""

    def __new__(cls, entity, value, raw=True):
        """Create a new typed value.

        :param entity: A :class:`mib.Node` instance
        :param value: The value to set
        :param raw: Whetever the raw value is provided (as opposed to
            a user-supplied value). This parameter is important when
            the provided input is ambiguous, for example when it is an
            array of bytes.
        :type raw: bool
        :return: an instance of the new typed value
        """
        if entity.type != cls:
            raise ValueError("MIB node is {}. We are {}".format(entity.type,
                                                                cls))

        if cls == OctetString and entity.fmt is not None:
            # Promotion of OctetString to String if we have unicode stuff
            if isinstance(value, (String, str)) or not raw:
                cls = String

        if not isinstance(value, Type):
            value = cls._internal(entity, value)
        else:
            value = cls._internal(entity, value._value)
        if issubclass(cls, str):
            self = str.__new__(cls, value)
        elif issubclass(cls, bytes):
            self = bytes.__new__(cls, value)
        elif issubclass(cls, int):
            self = int.__new__(cls, value)
        else:
            self = object.__new__(cls)

        self._value = value
        self.entity = entity

        if cls == OctetString and entity.fmt is not None:
            # A display-hint propose to use only ascii and UTF-8
            # chars. We promote an OCTET-STRING to a DisplayString if
            # we have a format. This means we won't be able to access
            # individual bytes in this format, only the full displayed
            # version.
            value = String._internal(entity, self)
            self = str.__new__(String, value)
            self._value = value
            self.entity = entity

        if isinstance(self, String):
            # Ensure that strings follow their format, if it is applied.
            # This is safer and simpler than toOid, as it does not do
            # additional validation.
            self._toBytes()

        return self

    def __init__(self, *args, **kwargs):
        # Neutralize __init__ from other inherited classes
        pass

    @classmethod
    def _internal(cls, entity, value):
        """Get internal value for a given value."""
        raise NotImplementedError  # pragma: no cover

    def pack(self):
        """Prepare the instance to be sent on the wire."""
        raise NotImplementedError  # pragma: no cover

    def toOid(self, implied=False):
        """Convert to an OID.

        If this function is implemented, then class function
        :meth:`fromOid` should also be implemented as the "invert"
        function of this one.

        This function only works if the entity is used as an index!
        Otherwise, it should raises NotImplementedError.

        :return: An OID that can be used as index
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        """Create instance from an OID.

        This is the sister function of :meth:`toOid`.

        :param oid: The OID to use to create an instance
        :param entity: The MIB entity we want to instantiate
        :return: A couple `(l, v)` with `l` the number of suboids
           needed to create the instance and `v` the instance created from
           the OID
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def _fixedLen(cls, entity):
        """Determine if the given entity is fixed-len

        This function is a helper that is used for String and
        Oid. When converting a variable-length type to an OID, we need
        to prefix it by its len or not depending of what the MIB say.

        Node that the type can be used in an index with IMPLIED keyword.
        In that case, even when this function returns False, the OID
        will not be prefixed by its length.

        :param entity: entity to check
        :return: `True` if it is fixed-len, `False` otherwise
        """
        if entity.ranges and not isinstance(entity.ranges, (tuple, list)):
            # Fixed length
            return True
        else:
            # Variable length
            return False

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__,
                                 str(self))


@ordering_with_cmp
class IpAddress(Type, ipaddress.IPv4Address):

    """Class representing an IP address/"""

    @classmethod
    def _internal(cls, entity, value):
        if isinstance(value, (list, tuple)):
            value = ".".join([str(a) for a in value])
        try:
            value = ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError:
            raise ValueError("{!r} is not a valid IP".format(value))
        return value

    def pack(self):
        return rfc1902.IpAddress(str(self._value))

    def toOid(self, implied=False):
        return tuple(self._value.packed)

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        if len(oid) < 4:
            raise ValueError(
                "{!r} is too short for an IP address".format(oid))
        return (4, cls(entity, oid[:4]))

    def __cmp__(self, other):
        if not isinstance(other, IpAddress):
            try:
                other = IpAddress(self.entity, other)
            except Exception:
                raise NotImplementedError  # pragma: no cover
        if self._value == other._value:
            return 0
        if self._value < other._value:
            return -1
        return 1

    def __getitem__(self, nb):
        return self._value.packed[nb]


class StringOrOctetString(Type):

    def toOid(self, implied=False):
        # To convert properly to OID, we need to know if it is a
        # fixed-len string, an implied string or a variable-len
        # string.
        b = self._toBytes()

        if implied or self._fixedLen(self.entity):
            return tuple(b)
        else:
            return (len(b),) + tuple(b)

    def _toBytes(self):
        raise NotImplementedError

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        oid = tuple(o & 0xff for o in oid)
        if implied:
            # Eat everything
            return (len(oid), cls(entity, bytes(oid)))
        if cls._fixedLen(entity):
            length = entity.ranges
            if len(oid) < length:
                raise ValueError(
                    "{} is too short for wanted fixed "
                    "string (need at least {:d})".format(oid, length))
            return (length,
                    cls(entity, bytes(oid[:length])))

        # This is var-len
        if not oid:
            raise ValueError("empty OID while waiting for var-len string")
        length = oid[0]
        if len(oid) < length + 1:
            raise ValueError(
                "{} is too short for variable-len "
                "string (need at least {:d})".format(oid, length))
        return (
            (length + 1,
             cls(entity, bytes(oid[1:(length + 1)]))))

    def pack(self):
        return rfc1902.OctetString(self._toBytes())


class OctetString(StringOrOctetString, bytes):

    """Class for a generic octet string. This class should be compared to
    :class:`String` which is used to represent a display string. This
    class is usually used to store raw bytes, like a bitmask of
    VLANs.
    """

    @classmethod
    def _internal(cls, entity, value):
        # Internally, we are using bytes
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("ascii")
        return bytes(value)

    def _toBytes(self):
        return self._value

    def __ior__(self, value):
        nvalue = bytearray(self._value)
        if not isinstance(value, (tuple, list)):
            value = [value]
        for v in value:
            if not isinstance(v, int):
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < (v >> 3) + 1:
                nvalue.extend([0] * ((v >> 3) + 1 - len(self._value)))
            nvalue[v >> 3] |= 1 << (7 - v % 8)
        return self.__class__(self.entity, bytes(nvalue))

    def __isub__(self, value):
        nvalue = bytearray(self._value)
        if not isinstance(value, (tuple, list)):
            value = [value]
        for v in value:
            if not isinstance(v, int):
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < (v >> 3) + 1:
                continue
            nvalue[v >> 3] &= ~(1 << (7 - v % 8))
        return self.__class__(self.entity, bytes(nvalue))
        return self

    def __and__(self, value):
        nvalue = bytearray(self._value)
        if not isinstance(value, (tuple, list)):
            value = [value]
        for v in value:
            if not isinstance(v, int):
                raise NotImplementedError(
                    "on string, bit-operation are limited to integers")
            if len(nvalue) < (v >> 3) + 1:
                return False
            if not(nvalue[v >> 3] & (1 << (7 - v % 8))):
                return False
        return True


class String(StringOrOctetString, str):

    """Class for a display string. Such a string is an unicode string and
    it is therefore expected that only printable characters are
    used. This is usually the case if the corresponding MIB node comes
    with a format string.

    With such an instance, the user is expected to be able to provide
    a formatted. For example, a MAC address could be written
    `00:11:22:33:44:55`.
    """

    @classmethod
    def _parseOctetFormat(cls, fmt, j):
        # repeater
        if fmt[j] == "*":
            dorepeat = True
            j += 1
        else:
            dorepeat = False

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

        return (j, dorepeat, length, format, sep, term)

    @classmethod
    def _fromBytes(cls, value, fmt):
        i = 0               # Position in value
        j = 0               # Position in fmt
        result = ""
        term = None
        sep = None
        while i < len(value):
            if j < len(fmt):
                j, dorepeat, length, format, sep, term = cls._parseOctetFormat(
                    fmt, j)

            # building
            if dorepeat:
                repeat = value[i]
                i += 1
            else:
                repeat = 1
            for r in range(repeat):
                bb = value[i:i + length]
                i += length
                if format in ['o', 'x', 'd']:
                    if length > 4:
                        raise ValueError(
                            "don't know how to handle integers "
                            "more than 4 bytes long")
                    bb = b"\x00" * (4 - length) + bb
                    number = struct.unpack(b"!l", bb)[0]
                    if format == "o":
                        # In Python2, oct() is 01242, while it is 0o1242 in
                        # Python3
                        result += "".join(oct(number).partition("o")[0:3:2])
                    elif format == "x":
                        result += hex(number)[2:]
                    else:       # format == "d":
                        result += str(number)
                elif format == "a":
                    result += bb.decode("ascii")
                elif format == "t":
                    result += bb.decode("utf-8")
                else:
                    raise ValueError("{!r} cannot be represented with "
                                     "the given display string ({})".format(
                                         bb, fmt))
                result += sep
            if sep and term:
                result = result[:-1]
            result += term
        if term or sep:
            result = result[:-1]
        return result

    def _toBytes(self):
        # We need to reverse what was done by `_fromBytes`. This is
        # not an exact science. In most case, this is easy because a
        # separator is used but sometimes, this is not. We do some
        # black magic that will fail.
        i = 0
        j = 0
        fmt = self.entity.fmt
        bb = b""
        while i < len(self._value):
            if j < len(fmt):
                parsed = self._parseOctetFormat(fmt, j)
                j, dorepeat, length, format, sep, term = parsed
                if format == "o":
                    fmatch = "(?P<o>[0-7]{{1,{0}}})".format(
                        int(length * 2.66667) + 1)
                elif format == "x":
                    fmatch = "(?P<x>[0-9A-Fa-f]{{1,{0}}})".format(length * 2)
                elif format == "d":
                    fmatch = "(?P<d>[0-9]{{1,{0}}})".format(
                        int(length * 2.4083) + 1)
                elif format == "a":
                    fmatch = "(?P<a>(?:.|\n){{1,{0}}})".format(length)
                elif format == "t":
                    fmatch = "(?P<t>(?:.|\n){{1,{0}}})".format(length)
                else:
                    raise ValueError("{!r} cannot be parsed due to an "
                                     "incorrect format ({})".format(
                                         self._value, fmt))
            repeats = []
            while True:
                mo = re.match(fmatch, self._value[i:])
                if not mo:
                    raise ValueError("{!r} cannot be parsed because it "
                                     "does not match format {} at "
                                     "index {}".format(self._value, fmt, i))
                if format in ["o", "x", "d"]:
                    if format == "o":
                        r = int(mo.group("o"), 8)
                    elif format == "x":
                        r = int(mo.group("x"), 16)
                    else:
                        r = int(mo.group("d"))
                    result = struct.pack(b"!l", r)[-length:]
                else:
                    result = mo.group(1).encode("utf-8")
                i += len(mo.group(1))
                if dorepeat:
                    repeats.append(result)
                    if i < len(self._value):
                        # Approximate...
                        if sep and self._value[i] == sep:
                            i += 1
                        elif term and self._value[i] == term:
                            i += 1
                            break
                    else:
                        break
                else:
                    break
            if dorepeat:
                bb += bytes([len(repeats)])
                bb += b"".join(repeats)
            else:
                bb += result
                if i < len(self._value) and (sep and self._value[i] == sep or
                                             term and self._value[i] == term):
                    i += 1

        return bb

    @classmethod
    def _internal(cls, entity, value):
        # Internally, we use the displayed string. We have a special
        # case if the value is an OctetString to do the conversion.
        if isinstance(value, OctetString):
            return cls._fromBytes(value._value, entity.fmt)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    def __str__(self):
        return self._value


class Integer(Type, int):

    """Class for any integer."""

    @classmethod
    def _internal(cls, entity, value):
        return int(value)

    def pack(self):
        if self._value >= (1 << 64):
            raise OverflowError("too large to be packed")
        if self._value >= (1 << 32):
            return rfc1902.Counter64(self._value)
        if self._value >= 0:
            return rfc1902.Integer(self._value)
        if self._value >= -(1 << 31):
            return rfc1902.Integer(self._value)
        raise OverflowError("too small to be packed")

    def toOid(self, implied=False):
        return (self._value,)

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        if len(oid) < 1:
            raise ValueError("{} is too short for an integer".format(oid))
        return (1, cls(entity, oid[0]))

    def __str__(self):
        if self.entity.fmt:
            if self.entity.fmt[0] == "x":
                return hex(self._value)
            if self.entity.fmt[0] == "o":
                return oct(self._value)
            if self.entity.fmt[0] == "b":
                if self._value == 0:
                    return "0"
                if self._value > 0:
                    v = self._value
                    r = ""
                    while v > 0:
                        r = str(v % 2) + r
                        v = v >> 1
                    return r
            elif self.entity.fmt[0] == "d" and \
                    len(self.entity.fmt) > 2 and \
                    self.entity.fmt[1] == "-":
                dec = int(self.entity.fmt[2:])
                result = str(self._value)
                if len(result) < dec + 1:
                    result = "0" * (dec + 1 - len(result)) + result
                return "{}.{}".format(result[:-2], result[-2:])
        return str(self._value)


class Unsigned32(Integer):

    """Class to represent an unsigned 32bits integer."""

    def pack(self):
        if self._value >= (1 << 32):
            raise OverflowError("too large to be packed")
        if self._value < 0:
            raise OverflowError("too small to be packed")
        return rfc1902.Unsigned32(self._value)


class Unsigned64(Integer):

    """Class to represent an unsigned 64bits integer."""

    def pack(self):
        if self._value >= (1 << 64):
            raise OverflowError("too large to be packed")
        if self._value < 0:
            raise OverflowError("too small to be packed")
        return rfc1902.Counter64(self._value)


class Enum(Integer):

    """Class for an enumeration. An enumaration is an integer but labels
    are attached to some values for a more user-friendly display."""

    @classmethod
    def _internal(cls, entity, value):
        if value in entity.enum:
            return value
        for (k, v) in entity.enum.items():
            if (v == value):
                return k
        try:
            return int(value)
        except Exception:
            raise ValueError("{!r} is not a valid "
                             "value for {}".format(value,
                                                   entity))

    def pack(self):
        return rfc1902.Integer(self._value)

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        if len(oid) < 1:
            raise ValueError(
                "{!r} is too short for an enumeration".format(oid))
        return (1, cls(entity, oid[0]))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            try:
                other = self.__class__(self.entity, other)
            except Exception:
                raise NotImplementedError  # pragma: no cover
        return self._value == other._value

    def __ne__(self, other):
        return not(self.__eq__(other))

    def __str__(self):
        if self._value in self.entity.enum:
            return (
                "{}({:d})".format(self.entity.enum[self._value], self._value)
            )
        else:
            return str(self._value)


@ordering_with_cmp
class Oid(Type):

    """Class to represent and OID."""

    @classmethod
    def _internal(cls, entity, value):
        if isinstance(value, (list, tuple)):
            return tuple(int(v) for v in value)
        elif isinstance(value, str):
            return tuple(int(i) for i in value.split(".") if i)
        elif isinstance(value, mib.Node):
            return tuple(value.oid)
        else:
            raise TypeError(
                "don't know how to convert {!r} to OID".format(value))

    def pack(self):
        return rfc1902.univ.ObjectIdentifier(self._value)

    def toOid(self, implied=False):
        if implied or self._fixedLen(self.entity):
            return self._value
        else:
            return tuple([len(self._value)] + list(self._value))

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        if cls._fixedLen(entity):
            # A fixed OID? We don't like this. Provide a real example.
            raise ValueError(
                "{!r} seems to be a fixed-len OID index. Odd.".format(entity))
        if not implied:
            # This index is not implied. We need the len
            if len(oid) < 1:
                raise ValueError(
                    "{!r} is too short for a not "
                    "implied index".format(entity))
            length = oid[0]
            if len(oid) < length + 1:
                raise ValueError(
                    "{!r} has an incorrect size "
                    "(needs at least {:d})".format(oid, length))
            return (length + 1, cls(entity, oid[1:(length + 1)]))
        else:
            # This index is implied. Eat everything
            return (len(oid), cls(entity, oid))

    def __str__(self):
        return ".".join([str(x) for x in self._value])

    def __cmp__(self, other):
        if not isinstance(other, Oid):
            other = Oid(self.entity, other)
        if tuple(self._value) == tuple(other._value):
            return 0
        if self._value > other._value:
            return 1
        return -1

    def __getitem__(self, index):
        return self._value[index]

    def __contains__(self, item):
        """Test if item is a sub-oid of this OID"""
        if not isinstance(item, Oid):
            item = Oid(self.entity, item)
        return tuple(item._value[:len(self._value)]) == \
            tuple(self._value[:len(self._value)])


class Boolean(Enum):

    """Class for a boolean."""

    @classmethod
    def _internal(cls, entity, value):
        if isinstance(value, bool):
            if value:
                return Enum._internal(entity, "true")
            else:
                return Enum._internal(entity, "false")
        else:
            return Enum._internal(entity, value)

    def __nonzero__(self):
        if self._value == 1:
            return True
        else:
            return False

    def __bool__(self):
        return self.__nonzero__()


@ordering_with_cmp
class Timeticks(Type):

    """Class for timeticks."""

    @classmethod
    def _internal(cls, entity, value):
        if isinstance(value, int):
            # Value in centiseconds
            return timedelta(0, value / 100.)
        elif isinstance(value, timedelta):
            return value
        else:
            raise TypeError(
                "dunno how to handle {!r} ({})".format(value, type(value)))

    def __int__(self):
        return self._value.days * 3600 * 24 * 100 + \
            self._value.seconds * 100 + \
            self._value.microseconds // 10000

    def toOid(self, implied=False):
        return (int(self),)

    @classmethod
    def fromOid(cls, entity, oid, implied=False):
        if len(oid) < 1:
            raise ValueError("{!r} is too short for a timetick".format(oid))
        return (1, cls(entity, oid[0]))

    def pack(self):
        return rfc1902.TimeTicks(int(self))

    def __str__(self):
        return str(self._value)

    def __cmp__(self, other):
        if isinstance(other, Timeticks):
            other = other._value
        elif isinstance(other, int):
            other = timedelta(0, other / 100.)
        elif not isinstance(other, timedelta):
            raise NotImplementedError(
                "only compare to int or "
                "timedelta, not {}".format(type(other)))
        if self._value == other:
            return 0
        if self._value < other:
            return -1
        return 1


class Bits(Type):

    """Class for bits."""

    @classmethod
    def _internal(cls, entity, value):
        bits = set()
        tryalternate = False
        if isinstance(value, bytes):
            for i, x in enumerate(value):
                if x == 0:
                    continue
                for j in range(8):
                    if x & (1 << (7 - j)):
                        k = (i * 8) + j
                        if k not in entity.enum:
                            tryalternate = True
                            break
                        bits.add(k)
                if tryalternate:
                    break
            if not tryalternate:
                return bits
            else:
                bits = set()
        elif not isinstance(value, (tuple, list, set, frozenset)):
            value = {value}
        for v in value:
            found = False
            if v in entity.enum:
                bits.add(v)
                found = True
            else:
                for (k, t) in entity.enum.items():
                    if (t == v):
                        bits.add(k)
                        found = True
                        break
            if not found:
                raise ValueError("{!r} is not a valid bit value".format(v))
        return bits

    def pack(self):
        if self._value:
            string = [0] * ((max(self._value) // 8) + 1)
        else:
            string = []
        for b in self._value:
            string[b // 8] |= 1 << (7 - b % 8)
        return rfc1902.Bits(bytes(string))

    def __eq__(self, other):
        if isinstance(other, str):
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        return self._value == other._value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        result = []
        for b in sorted(self._value):
            result.append("{}({:d})".format(self.entity.enum[b], b))
        return ", ".join(result)

    def __and__(self, other):
        if isinstance(other, str):
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        return len(self._value & other._value) > 0

    def __ior__(self, other):
        if isinstance(other, str):
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        self._value |= other._value
        return self

    def __isub__(self, other):
        if isinstance(other, str):
            other = [other]
        if not isinstance(other, Bits):
            other = Bits(self.entity, other)
        self._value -= other._value
        return self


def build(mibname, node, value):
    """Build a new basic type with the given value.

    :param mibname: The MIB to use to locate the entity.
    :param node: The node that will be attached to this type.
    :param value: The initial value to set for the type.
    :return: A :class:`Type` instance
    """
    m = mib.get(mibname, node)
    t = m.type(m, value)
    return t
