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
.. _CFFI: http://cffi.readthedocs.io/
"""

try:
    from snimpy._smi import lib as _smi
    from snimpy._smi import ffi
except ImportError:
    from snimpy.smi_build import ffi, get_lib
    _smi = get_lib()


class SMIException(Exception):

    """SMI related exception. Any exception thrown in this module is
    inherited from this one."""


class Node(object):

    """MIB node. An instance of this class represents a MIB node. It
    can be specialized by other classes, like :class:`Scalar`,
    :class:`Table`, :class:`Column`, :class:`Node`.
    """

    def __init__(self, node, mibloader):
        """Create a new MIB node.

        :param node: libsmi node supporting this node.
        """
        self.node = node
        self._override_type = None
        self.mibloader = mibloader

    @property
    def type(self):
        """Get the basic type associated with this node.

        :return: The class from :mod:`basictypes` module which can
            represent the node. When retrieving a valid value for
            this node, the returned class can be instanciated to get
            an appropriate representation.
        """
        self.mibloader._switch()
        from snimpy import basictypes
        if self._override_type:
            t = self._override_type
        else:
            t = _smi.smiGetNodeType(self.node)
        if t == ffi.NULL:
            raise SMIException("unable to retrieve type of node")
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
    def typeName(self):
        """Retrieves the name of the the node's current declared type
        (not basic type).

        :return: A string representing the current declared type,
            suitable for assignment to type.setter.
        """
        self.mibloader._switch()
        if self._override_type:
            t = self._override_type
        else:
            t = _smi.smiGetNodeType(self.node)

        # This occurs when the type is "implied".
        if t.name == ffi.NULL:
            t = _smi.smiGetParentType(t)

        if t is None or t == ffi.NULL:
            raise SMIException("unable to retrieve the declared type "
                               "of the node '{0}'".format(self.node.name))

        return ffi.string(t.name)

    @typeName.setter
    def typeName(self, type_name):
        """Override the node's type to type_name, found using _getType.
        The new type must resolve to the same basictype.

        :param type_name: string name of the type.
        """
        self.mibloader._switch()
        current_override = self._override_type

        declared_type = _smi.smiGetNodeType(self.node)
        declared_basetype = self.type

        new_type = self.mibloader._getType(type_name)
        if not new_type:
            raise SMIException("no type named {0} in any loaded module".format(
                type_name))

        # Easiest way to find the new basetype is to set the override
        # and ask.
        self._override_type = new_type
        new_basetype = self.type

        if declared_basetype != new_basetype:
            self._override_type = current_override
            raise SMIException("override type {1} not compatible with "
                               "basetype of {0}".format(
                                   ffi.string(declared_type.name),
                                   ffi.string(new_type.name)))

    @typeName.deleter
    def typeName(self):
        """Clears the type override."""
        self._override_type = None

    @property
    def fmt(self):
        """Get node format. The node format is a string to use to display
        a user-friendly version of the node. This is can be used for
        both octet strings or integers (to make them appear as decimal
        numbers).

        :return: The node format as a string or None if there is no
            format available.

        """
        self.mibloader._switch()
        if self._override_type:
            t = self._override_type
        else:
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
        self.mibloader._switch()
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
        self.mibloader._switch()
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
        self.mibloader._switch()
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
        self.mibloader._switch()
        return ffi.string(self.node.name).decode("ascii")

    def __repr__(self):
        self.mibloader._switch()
        r = _smi.smiRenderNode(self.node, _smi.SMI_RENDER_ALL)
        if r == ffi.NULL:
            return "<uninitialized {0} object at {1}>".format(
                self.__class__.__name__, hex(id(self)))
        r = ffi.gc(r, _smi.free)
        module = _smi.smiGetNodeModule(self.node)
        if module == ffi.NULL:
            raise SMIException("unable to get module for {0}".format(
                self.node.name))
        return "<{0} {1} from '{2}'>".format(self.__class__.__name__,
                                             ffi.string(r),
                                             ffi.string(module.name))

    def _convert(self, value):
        self.mibloader._switch()
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
        self.mibloader._switch()
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
            columns.append(Column(child, self.mibloader))
            child = _smi.smiGetNextChildNode(child)
        return columns

    @property
    def _row(self):
        """Get the table row.

        :return: row object (as an opaque object)
        """
        self.mibloader._switch()
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
        self.mibloader._switch()
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
        self.mibloader._switch()
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
            lindex.append(Column(nelement, self.mibloader))
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
        self.mibloader._switch()
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
        t = Table(parent, self.mibloader)
        return t


_lastError = None


@ffi.callback("void(char *, int, int, char *, char*)")
def _logError(path, line, severity, msg, tag):
    global _lastError
    if path != ffi.NULL and msg != ffi.NULL:
        _lastError = "{0}:{1}: {2}".format(ffi.string(path), line,
                                           ffi.string(msg))
    else:
        _lastError = None


def reset():
    """Reset libsmi to its initial state."""
    global _mibloader
    _smi.smiExit()
    if _smi.smiInit(b"snimpy") < 0:
            raise SMIException("unable to init libsmi")
    _smi.smiSetErrorLevel(1)
    _smi.smiSetErrorHandler(_logError)
    try:
        _smi.smiSetFlags(_smi.SMI_FLAG_ERRORS | _smi.SMI_FLAG_RECURSIVE)
    except TypeError:
        pass                    # We are being mocked
    _mibloader = MibLoader()


class MibLoader(object):
    """Isolated MIB loader to support multiple sets of MIBs"""

    _datasetid = 0

    def __init__(self):
        global _datasetid
        self._tag = "snimpy:{0}".format(
                                        MibLoader._datasetid
                                      ).encode('ascii')
        MibLoader._datasetid += 1

    def _switch(self):
        """Switch to this object's set of loaded MIBs"""
        if _smi.smiInit(self._tag) < 0:
            raise SMIException("unable to switch to the MIB loader")

    def path(self, path=None):
        """Set or get a search path to libsmi.

        When no path is provided, return the current path,
        unmodified. Otherwise, set the path to the specified value.

        :param path: The string to be used to change the search path or
                     `None`

        """
        self._switch()
        if path is None:
            # Get the path
            path = _smi.smiGetPath()
            if path == ffi.NULL:
                raise SMIException("unable to get current libsmi path")
            path = ffi.gc(path, _smi.free)
            result = ffi.string(path)
            return result.decode("utf8")

        # Set the path
        if not isinstance(path, bytes):
            path = path.encode("utf8")
        if _smi.smiSetPath(path) < 0:
            raise SMIException("unable to set the path {0}".format(path))

    def _get_module(self, name):
        """Get the SMI module from its name.

        :param name: The name of the module
        :return: The SMI module or `None` if not found (not loaded)
        """
        self._switch()
        if not isinstance(name, bytes):
            name = name.encode("ascii")
        m = _smi.smiGetModule(name)
        if m == ffi.NULL:
            return None
        if m.conformance and m.conformance <= 1:
            return None
        return m

    def _kind2object(self, kind):
        return {
            _smi.SMI_NODEKIND_NODE: Node,
            _smi.SMI_NODEKIND_SCALAR: Scalar,
            _smi.SMI_NODEKIND_TABLE: Table,
            _smi.SMI_NODEKIND_COLUMN: Column
        }.get(kind, Node)

    def get(self, mib, name):
        """Get a node by its name.

        :param mib: The MIB name to query
        :param name: The object name to get from the MIB
        :return: the requested MIB node (:class:`Node`)
        """
        self._switch()
        if not isinstance(mib, bytes):
            mib = mib.encode("ascii")
        module = self._get_module(mib)
        if module is None:
            raise SMIException("no module named {0}".format(mib))
        node = _smi.smiGetNode(module, name.encode("ascii"))
        if node == ffi.NULL:
            raise SMIException("in {0}, no node named {1}".format(
                mib, name))
        pnode = self._kind2object(node.nodekind)
        return pnode(node, self)

    def getByOid(self, oid):
        """Get a node by its OID.

        :param oid: The OID as a tuple
        :return: The requested MIB node (:class:`Node`)
        """
        self._switch()
        node = _smi.smiGetNodeByOID(len(oid), oid)
        if node == ffi.NULL:
            raise SMIException("no node for {0}".format(
                ".".join([str(o) for o in oid])))
        pnode = self._kind2object(node.nodekind)
        return pnode(node, self)

    def _getType(self, type_name):
        """Searches for a smi type through all loaded modules.

        :param type_name: The name of the type to search for.
        :return: The requested type (:class:`smi.SmiType`), if found, or None.
        """
        if not isinstance(type_name, bytes):
            type_name = type_name.encode("ascii")
        for module in self._loadedModules():
            new_type = _smi.smiGetType(module, type_name)
            if new_type != ffi.NULL:
                return new_type
        return None

    def _get_kind(self, mib, kind):
        """Get nodes of a given kind from a MIB.

        :param mib: The MIB name to search objects for
        :param kind: The SMI kind of object
        :return: The list of matched MIB nodes for the MIB
        """
        if not isinstance(mib, bytes):
            mib = mib.encode("ascii")
        module = self._get_module(mib)
        if module is None:
            raise SMIException("no module named {0}".format(mib))
        lnode = []
        node = _smi.smiGetFirstNode(module, kind)
        while node != ffi.NULL:
            lnode.append(self._kind2object(kind)(node, self))
            node = _smi.smiGetNextNode(node, kind)
        return lnode

    def getNodes(self, mib):
        """Return all nodes from a given MIB.

        :param mib: The MIB name
        :return: The list of all MIB nodes for the MIB
        :rtype: list of :class:`Node` instances
        """
        self._switch()
        return self._get_kind(mib, _smi.SMI_NODEKIND_NODE)

    def getScalars(self, mib):
        """Return all scalars from a given MIB.

        :param mib: The MIB name
        :return: The list of all scalars for the MIB
        :rtype: list of :class:`Scalar` instances
        """
        self._switch()
        return self._get_kind(mib, _smi.SMI_NODEKIND_SCALAR)

    def getTables(self, mib):
        """Return all tables from a given MIB.

        :param mib: The MIB name
        :return: The list of all tables for the MIB
        :rtype: list of :class:`Table` instances
        """
        self._switch()
        return self._get_kind(mib, _smi.SMI_NODEKIND_TABLE)

    def getColumns(self, mib):
        """Return all columns from a givem MIB.

        :param mib: The MIB name
        :return: The list of all columns for the MIB
        :rtype: list of :class:`Column` instances
        """
        self._switch()
        return self._get_kind(mib, _smi.SMI_NODEKIND_COLUMN)

    def load(self, mib):
        """Load a MIB into the library.

        :param mib: The MIB to load, either a filename or a MIB name.
        :return: The MIB name that has been loaded.
        :except SMIException: The requested MIB cannot be loaded.
        """
        self._switch()
        if not isinstance(mib, bytes):
            mib = mib.encode("ascii")
        modulename = _smi.smiLoadModule(mib)
        if modulename == ffi.NULL:
            raise SMIException(
                    "unable to find {0} (check the path)".format(mib))
        modulename = ffi.string(modulename)
        if not self._get_module(modulename.decode("ascii")):
            details = "check with smilint -s -l1"
            if _lastError is not None:
                details = "{0}: {1}".format(_lastError,
                                            details)
            raise SMIException(
                "{0} contains major SMI error ({1})".format(mib, details))
        return modulename

    def _loadedModules(self):
        """Generates the list of loaded modules.

        :yield: The :class:`smi.SmiModule` of all currently loaded modules.
        """
        module = _smi.smiGetFirstModule()
        while module != ffi.NULL:
            yield module

            module = _smi.smiGetNextModule(module)

    def loadedMibNames(self):
        """Generates the list of loaded MIB names.

        :yield: The names of all currently loaded MIBs.
        """
        self._switch()
        for module in self._loadedModules():
            yield ffi.string(module.name).decode('utf-8')


reset()
_getType = _mibloader._getType
path = _mibloader.path
get = _mibloader.get
getByOid = _mibloader.getByOid
getColumns = _mibloader.getColumns
getNodes = _mibloader.getNodes
getScalars = _mibloader.getScalars
getTables = _mibloader.getTables
load = _mibloader.load
loadedMibNames = _mibloader.loadedMibNames
