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

"""This module is a low-level interface to manipulate and
extract information from MIB files. It is a CFFI_ wrapper around
libsmi_. You may find convenient to use it in other projects but the
wrapper is merely here to serve *Snimpy* use and is therefore
incomplete.

.. _libsmi: http://www.ibr.cs.tu-bs.de/projects/libsmi/
.. _CFFI: http://cffi.readthedocs.org/
"""

from snimpy import cffi_fix  # nopep8
from cffi import FFI

ffi = FFI()
ffi.cdef("""

typedef char *SmiIdentifier;
typedef unsigned long SmiUnsigned32;
typedef long SmiInteger32;
typedef unsigned long long SmiUnsigned64;
typedef long long SmiInteger64;
typedef unsigned int SmiSubid;
typedef float SmiFloat32;
typedef double SmiFloat64;
typedef long double SmiFloat128;

typedef enum SmiBasetype {
    SMI_BASETYPE_INTEGER32,
    SMI_BASETYPE_OCTETSTRING,
    SMI_BASETYPE_OBJECTIDENTIFIER,
    SMI_BASETYPE_UNSIGNED32,
    SMI_BASETYPE_INTEGER64,
    SMI_BASETYPE_UNSIGNED64,
    SMI_BASETYPE_ENUM,
    SMI_BASETYPE_BITS,
    ...
} SmiBasetype;
typedef struct SmiType {
    SmiIdentifier       name;
    SmiBasetype         basetype;
    char                *format;
    ...;
} SmiType;

typedef enum SmiIndexkind {
    SMI_INDEX_INDEX,
    SMI_INDEX_AUGMENT,
    ...
} SmiIndexkind;

typedef unsigned int SmiNodekind;
#define SMI_NODEKIND_NODE         ...
#define SMI_NODEKIND_SCALAR       ...
#define SMI_NODEKIND_TABLE        ...
#define SMI_NODEKIND_ROW          ...
#define SMI_NODEKIND_COLUMN       ...

typedef struct SmiNode {
    SmiIdentifier       name;
    unsigned int        oidlen;
    SmiSubid            *oid;
    char                *format;
    SmiIndexkind        indexkind;
    int                 implied;
    SmiNodekind         nodekind;
    ...;
} SmiNode;

typedef struct SmiValue {
    SmiBasetype             basetype;
    union {
        SmiUnsigned64       unsigned64;
        SmiInteger64        integer64;
        SmiUnsigned32       unsigned32;
        SmiInteger32        integer32;
        SmiFloat32          float32;
        SmiFloat64          float64;
        SmiFloat128         float128;
        SmiSubid            *oid;
        char                *ptr;
    } value;
    ...;
} SmiValue;

typedef struct SmiRange {
    SmiValue            minValue;
    SmiValue            maxValue;
} SmiRange;

typedef struct SmiModule {
    SmiIdentifier       name;
    int                 conformance;
    ...;
} SmiModule;

typedef struct SmiElement {
    ...;
} SmiElement;

typedef struct SmiNamedNumber {
    SmiIdentifier       name;
    SmiValue            value;
} SmiNamedNumber;

int          smiInit(const char *);
void         smiExit(void);
void         smiSetErrorLevel(int);
void         smiSetFlags(int);
char        *smiLoadModule(const char *);
SmiModule   *smiGetModule(const char *);
SmiModule   *smiGetNodeModule(SmiNode *);
SmiType     *smiGetNodeType(SmiNode *);
SmiType     *smiGetParentType(SmiType *);
char        *smiRenderNode(SmiNode *, int);
SmiElement  *smiGetFirstElement(SmiNode *);
SmiElement  *smiGetNextElement(SmiElement *);
SmiNode     *smiGetElementNode(SmiElement *);
SmiRange    *smiGetFirstRange(SmiType *);
SmiRange    *smiGetNextRange(SmiRange *);
SmiNode     *smiGetNode(SmiModule *, const char *);
SmiNode     *smiGetFirstNode(SmiModule *, SmiNodekind);
SmiNode     *smiGetNextNode(SmiNode *, SmiNodekind);
SmiNode     *smiGetParentNode(SmiNode *);
SmiNode     *smiGetRelatedNode(SmiNode *);
SmiNode     *smiGetFirstChildNode(SmiNode *);
SmiNode     *smiGetNextChildNode(SmiNode *);
SmiNamedNumber *smiGetFirstNamedNumber(SmiType *);
SmiNamedNumber *smiGetNextNamedNumber(SmiNamedNumber *);

#define SMI_FLAG_ERRORS ...
#define SMI_FLAG_RECURSIVE ...
#define SMI_RENDER_ALL ...
""")

_smi = ffi.verify("""
#include <smi.h>
""", libraries=["smi"])


class SMIException(Exception):

    """SMI related exception. Any exception thrown in this module is
    inherited from this one."""


class Node(object):

    """MIB node. An instance of this class represents a MIB node. It
    can be specialized by other classes, like :class:`Scalar`,
    :class:`Table`, :class:`Column`, :class:`Node`.
    """

    def __init__(self, node):
        """Create a new MIB node.

        :param node: libsmi node supporting this node.
        """
        self.node = node

    @property
    def type(self):
        """Get the basic type associated with this node.

        :return: The class from :mod:`basictypes` module which can
            represent the node. When retrieving a valid value for
            this node, the returned class can be instanciated to get
            an appropriate representation.
        """
        from snimpy import basictypes
        t = _smi.smiGetNodeType(self.node)
        target = {
            _smi.SMI_BASETYPE_INTEGER32: basictypes.Integer,
            _smi.SMI_BASETYPE_INTEGER64: basictypes.Integer,
            _smi.SMI_BASETYPE_UNSIGNED32: {b"TimeTicks": basictypes.Timeticks,
                                           None: basictypes.Unsigned32},
            _smi.SMI_BASETYPE_UNSIGNED64: basictypes.Unsigned64,
            _smi.SMI_BASETYPE_OCTETSTRING: {b"IpAddress": basictypes.IpAddress,
                                            None: basictypes.OctetString},
            _smi.SMI_BASETYPE_OBJECTIDENTIFIER: basictypes.Oid,
            _smi.SMI_BASETYPE_ENUM: {b"TruthValue": basictypes.Boolean,
                                     None: basictypes.Enum},
            _smi.SMI_BASETYPE_BITS: basictypes.Bits
        }.get(t.basetype, None)
        if isinstance(target, dict):
            tt = _smi.smiGetParentType(t)
            target = target.get((t.name != ffi.NULL and ffi.string(t.name)) or
                                (tt.name != ffi.NULL and ffi.string(
                                    tt.name)) or None,
                                target.get(None, None))

        if target is None:
            raise SMIException("unable to retrieve type of node")
        return target

    @property
    def fmt(self):
        """Get node format. The node format is a string to use to display
        a user-friendly version of the node. This is can be used for
        both octet strings or integers (to make them appear as decimal
        numbers).

        :return: The node format as a string or None if there is no
            format available.

        """
        t = _smi.smiGetNodeType(self.node)
        tt = _smi.smiGetParentType(t)
        f = (t != ffi.NULL and t.format != ffi.NULL and ffi.string(t.format) or
             tt != ffi.NULL and tt.format != ffi.NULL and
             ffi.string(tt.format)) or None
        if f is None:
            return None
        return f.decode("ascii")

    @property
    def oid(self):
        """Get OID for the current node. The OID can then be used to request
        the node from an SNMP agent.

        :return: OID as a tuple
        """
        return tuple([self.node.oid[i] for i in range(self.node.oidlen)])

    @property
    def ranges(self):
        """Get node ranges. An node can be restricted by a set of
        ranges. For example, an integer can only be provided between
        two values. For strings, the restriction is on the length of
        the string.

        The returned value can be `None` if no restriction on range
        exists for the current node, a single value if the range is
        fixed or a list of tuples or fixed values otherwise.

        :return: The valid range for this node.
        """
        t = _smi.smiGetNodeType(self.node)
        if t == ffi.NULL:
            return None

        ranges = []
        range = _smi.smiGetFirstRange(t)
        while range != ffi.NULL:
            m1 = self._convert(range.minValue)
            m2 = self._convert(range.maxValue)
            if m1 == m2:
                ranges.append(m1)
            else:
                ranges.append((m1, m2))
            range = _smi.smiGetNextRange(range)
        if len(ranges) == 0:
            return None
        if len(ranges) == 1:
            return ranges[0]
        return ranges

    @property
    def enum(self):
        """Get possible enum values. When the node can only take a discrete
        number of values, those values are defined in the MIB and can
        be retrieved through this property.

        :return: The dictionary of possible values keyed by the integer value.
        """
        t = _smi.smiGetNodeType(self.node)
        if t == ffi.NULL or t.basetype not in (_smi.SMI_BASETYPE_ENUM,
                                               _smi.SMI_BASETYPE_BITS):
            return None

        result = {}
        element = _smi.smiGetFirstNamedNumber(t)
        while element != ffi.NULL:
            result[self._convert(element.value)] = ffi.string(
                element.name).decode("ascii")
            element = _smi.smiGetNextNamedNumber(element)
        return result

    def __str__(self):
        return ffi.string(self.node.name).decode("ascii")

    def __repr__(self):
        r = _smi.smiRenderNode(self.node, _smi.SMI_RENDER_ALL)
        if r == ffi.NULL:
            return "<uninitialized {0} object at {1}>".format(
                self.__class__.__name__, hex(id(self)))
        module = _smi.smiGetNodeModule(self.node)
        if module == ffi.NULL:
            raise SMIException("unable to get module for {0}".format(
                self.node.name))
        return "<{0} {1} from '{2}'>".format(self.__class__.__name__,
                                             ffi.string(r),
                                             ffi.string(module.name))

    def _convert(self, value):
        attr = {_smi.SMI_BASETYPE_INTEGER32: "integer32",
                _smi.SMI_BASETYPE_UNSIGNED32: "unsigned32",
                _smi.SMI_BASETYPE_INTEGER64: "integer64",
                _smi.SMI_BASETYPE_UNSIGNED64: "unsigned64"}.get(value.basetype,
                                                                None)
        if attr is None:
            raise SMIException("unexpected type found in range")
        return getattr(value.value, attr)


class Scalar(Node):

    """MIB scalar node. This class represents a scalar value in the
    MIB. A scalar value is a value not contained in a table.
    """


class Table(Node):

    """MIB table node. This class represents a table. A table is an
    ordered collection of objects consisting of zero or more
    rows. Each object in the table is identified using an index. An
    index can be a single value or a list of values.
    """

    @property
    def columns(self):
        """Get table columns. The columns are the different kind of objects
        that can be retrieved in a table.

        :return: list of table columns (:class:`Column` instances)

        """
        child = _smi.smiGetFirstChildNode(self.node)
        if child == ffi.NULL:
            return []
        if child.nodekind != _smi.SMI_NODEKIND_ROW:
            raise SMIException("child {0} of {1} is not a row".format(
                ffi.string(child.name),
                ffi.string(self.node.name)))
        columns = []
        child = _smi.smiGetFirstChildNode(child)
        while child != ffi.NULL:
            if child.nodekind != _smi.SMI_NODEKIND_COLUMN:
                raise SMIException("child {0} of {1} is not a column".format(
                    ffi.string(child.name),
                    ffi.string(self.node.name)))
            columns.append(Column(child))
            child = _smi.smiGetNextChildNode(child)
        return columns

    @property
    def _row(self):
        """Get the table row.

        :return: row object (as an opaque object)
        """
        child = _smi.smiGetFirstChildNode(self.node)
        if child != ffi.NULL and child.indexkind == _smi.SMI_INDEX_AUGMENT:
            child = _smi.smiGetRelatedNode(child)
            if child == ffi.NULL:
                raise SMIException("AUGMENT index for {0} but "
                                   "unable to retrieve it".format(
                                       ffi.string(self.node.name)))
        if child == ffi.NULL:
            raise SMIException("{0} does not have a row".format(
                ffi.string(self.node.name)))
        if child.nodekind != _smi.SMI_NODEKIND_ROW:
            raise SMIException("child {0} of {1} is not a row".format(
                ffi.string(child.name),
                ffi.string(self.node.name)))
        if child.indexkind != _smi.SMI_INDEX_INDEX:
            raise SMIException("child {0} of {1} has an unhandled "
                               "kind of index".format(
                                   ffi.string(child.name),
                                   ffi.string(self.node.name)))
        return child

    @property
    def implied(self):
        """Is the last index implied? An implied index is an index whose size
        is not fixed but who is not prefixed by its size because this
        is the last index of a table.

        :return: `True` if and only if the last index is implied.
        """
        child = self._row
        if child.implied:
            return True
        return False

    @property
    def index(self):
        """Get indexes for a table. The indexes are used to locate a precise
        row in a table. They are a subset of the table columns.

        :return: The list of indexes (as :class:`Column` instances) of
            the table.
        """
        child = self._row
        lindex = []
        element = _smi.smiGetFirstElement(child)
        while element != ffi.NULL:
            nelement = _smi.smiGetElementNode(element)
            if nelement == ffi.NULL:
                raise SMIException("cannot get index "
                                   "associated with {0}".format(
                                       ffi.string(self.node.name)))
            if nelement.nodekind != _smi.SMI_NODEKIND_COLUMN:
                raise SMIException("index {0} for {1} is "
                                   "not a column".format(
                                       ffi.string(nelement.name),
                                       ffi.string(self.node.name)))
            lindex.append(Column(nelement))
            element = _smi.smiGetNextElement(element)
        return lindex


class Column(Node):

    """MIB column node. This class represent a column of a table."""

    @property
    def table(self):
        """Get table associated with this column.

        :return: The :class:`Table` instance associated to this
            column.
        """
        parent = _smi.smiGetParentNode(self.node)
        if parent == ffi.NULL:
            raise SMIException("unable to get parent of {0}".format(
                ffi.string(self.node.name)))
        if parent.nodekind != _smi.SMI_NODEKIND_ROW:
            raise SMIException("parent {0} of {1} is not a row".format(
                ffi.string(parent.name),
                ffi.string(self.node.name)))
        parent = _smi.smiGetParentNode(parent)
        if parent == ffi.NULL:
            raise SMIException("unable to get parent of {0}".format(
                ffi.string(self.node.name)))
        if parent.nodekind != _smi.SMI_NODEKIND_TABLE:
            raise SMIException("parent {0} of {1} is not a table".format(
                ffi.string(parent.name),
                ffi.string(self.node.name)))
        t = Table(parent)
        return t


def reset():
    """Reset libsmi to its initial state."""
    _smi.smiExit()
    if _smi.smiInit(b"snimpy") < 0:
            raise SMIException("unable to init libsmi")
    _smi.smiSetErrorLevel(0)
    try:
        _smi.smiSetFlags(_smi.SMI_FLAG_ERRORS | _smi.SMI_FLAG_RECURSIVE)
    except TypeError:
        pass                    # We are being mocked


def _get_module(name):
    """Get the SMI module from its name.

    :param name: The name of the module
    :return: The SMI module or `None` if not found (not loaded)
    """
    if not isinstance(name, bytes):
        name = name.encode("ascii")
    m = _smi.smiGetModule(name)
    if m == ffi.NULL:
        return None
    if m.conformance and m.conformance <= 1:
        return None
    return m


def _kind2object(kind):
    return {
        _smi.SMI_NODEKIND_NODE: Node,
        _smi.SMI_NODEKIND_SCALAR: Scalar,
        _smi.SMI_NODEKIND_TABLE: Table,
        _smi.SMI_NODEKIND_COLUMN: Column
    }.get(kind, Node)


def get(mib, name):
    """Get a node by its name.

    :param mib: The MIB name to query
    :param name: The object name to get from the MIB
    :return: the requested MIB node (:class:`Node`)
    """
    if not isinstance(mib, bytes):
        mib = mib.encode("ascii")
    module = _get_module(mib)
    if module is None:
        raise SMIException("no module named {0}".format(mib))
    node = _smi.smiGetNode(module, name.encode("ascii"))
    if node == ffi.NULL:
        raise SMIException("in {0}, no node named {1}".format(
            mib, name))
    pnode = _kind2object(node.nodekind)
    return pnode(node)


def _get_kind(mib, kind):
    """Get nodes of a given kind from a MIB.

    :param mib: The MIB name to search objects for
    :param kind: The SMI kind of object
    :return: The list of matched MIB nodes for the MIB
    """
    if not isinstance(mib, bytes):
        mib = mib.encode("ascii")
    module = _get_module(mib)
    if module is None:
        raise SMIException("no module named {0}".format(mib))
    lnode = []
    node = _smi.smiGetFirstNode(module, kind)
    while node != ffi.NULL:
        lnode.append(_kind2object(kind)(node))
        node = _smi.smiGetNextNode(node, kind)
    return lnode


def getNodes(mib):
    """Return all nodes from a given MIB.

    :param mib: The MIB name
    :return: The list of all MIB nodes for the MIB
    :rtype: list of :class:`Node` instances
    """
    return _get_kind(mib, _smi.SMI_NODEKIND_NODE)


def getScalars(mib):
    """Return all scalars from a given MIB.

    :param mib: The MIB name
    :return: The list of all scalars for the MIB
    :rtype: list of :class:`Scalar` instances
    """
    return _get_kind(mib, _smi.SMI_NODEKIND_SCALAR)


def getTables(mib):
    """Return all tables from a given MIB.

    :param mib: The MIB name
    :return: The list of all tables for the MIB
    :rtype: list of :class:`Table` instances
    """
    return _get_kind(mib, _smi.SMI_NODEKIND_TABLE)


def getColumns(mib):
    """Return all columns from a givem MIB.

    :param mib: The MIB name
    :return: The list of all columns for the MIB
    :rtype: list of :class:`Column` instances
    """
    return _get_kind(mib, _smi.SMI_NODEKIND_COLUMN)


def load(mib):
    """Load a MIB into the library.

    :param mib: The MIB to load, either a filename or a MIB name.
    :return: The MIB name that has been loaded.
    :except SMIException: The requested MIB cannot be loaded.
    """
    if not isinstance(mib, bytes):
        mib = mib.encode("ascii")
    modulename = _smi.smiLoadModule(mib)
    if modulename == ffi.NULL:
        raise SMIException("unable to load {0}".format(mib))
    modulename = ffi.string(modulename)
    if not _get_module(modulename.decode("ascii")):
        raise SMIException("{0} contains major SMI error "
                           "(check with smilint -s -l1)".format(mib))
    return modulename

reset()
