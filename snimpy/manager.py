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

"""This module is the high-level interface to *Snimpy*. It exposes
:class:`Manager` class to instantiate a new manager (which is an SNMP
client). This is the preferred interface for *Snimpy*.

Here is a simple example of use of this module::

    >>> load("IF-MIB")
    >>> m = Manager("localhost")
    >>> m.ifDescr[1]
    <String: lo>
"""

import inspect
from time import time
from collections.abc import MutableMapping, Container, Iterable, Sized
from snimpy import snmp, mib, basictypes


class DelegatedSession:

    """General class for SNMP session for delegation"""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, attr):
        return getattr(self._session, attr)

    def __setattribute__(self, attr, value):
        return setattr(self._session, attr, value)


class DelayedSetSession(DelegatedSession):

    """SNMP session that is able to delay SET requests.

    This is an adapter. The constructor takes the original (not
    delayed) session.
    """

    def __init__(self, session):
        DelegatedSession.__init__(self, session)
        self.setters = []

    def set(self, *args):
        self.setters.extend(args)

    def commit(self):
        if self.setters:
            self._session.set(*self.setters)


class NoneSession(DelegatedSession):

    """SNMP session that will return None on unsucessful GET requests.

    In a normal session, a GET request returning `No such instance`
    error will trigger an exception. This session will catch such an
    error and return None instead.
    """

    def get(self, *args):
        try:
            return self._session.get(*args)
        except (snmp.SNMPNoSuchName,
                snmp.SNMPNoSuchObject,
                snmp.SNMPNoSuchInstance):
            if len(args) > 1:
                # We can't handle this case yet because we don't know
                # which value is unavailable.
                raise
            return ((args[0], None),)


class CachedSession(DelegatedSession):

    """SNMP session using a cache.

    This is an adapter. The constructor takes the original session.
    """

    def __init__(self, session, timeout=5):
        DelegatedSession.__init__(self, session)
        self.cache = {}  # contains (operation, oid) -> [time, result] entries
        self.timeout = timeout
        self.count = 0

    def getorwalk(self, op, *args):
        self.count += 1
        if (op, args) in self.cache:
            t, v = self.cache[op, args]
            if time() - t < self.timeout:
                return v
        value = getattr(self._session, op)(*args)
        self.cache[op, args] = [time(), value]
        if op == "walkmore":
            # also cache all the get requests we got for free
            for oid, get_value in value:
                self.count += 1
                self.cache["get", (oid, )] = [time(), ((oid, get_value), )]
        self.flush()
        return value

    def get(self, *args):
        return self.getorwalk("get", *args)

    def walk(self, *args):
        assert(len(args) == 1)  # we should ony walk one oid at a time
        return self.getorwalk("walkmore", *args)

    def flush(self):
        keys = list(self.cache.keys())
        for k in keys:
            if time() - self.cache[k][0] > self.timeout:
                del self.cache[k]
        self.count = 0


def MibRestrictedManager(original, mibs):

    """Copy an existing manager but restrict its view to the given set of
    MIBs.
    """
    clone = Manager(**original._constructor_args)
    clone._loaded = mibs
    return clone


class Manager:

    """SNMP manager. An instance of this class will represent an SNMP
    manager (client).

    When a MIB is loaded with :func:`load`, scalars and row names from
    it will be made available as an instance attribute. For a scalar,
    reading the corresponding attribute will get its value while
    setting it will allow to modify it:

        >>> load("SNMPv2-MIB")
        >>> m = Manager("localhost", "private")
        >>> m.sysContact
        <String: root>
        >>> m.sysContact = "Brian Jones"
        >>> m.sysContact
        <String: Brian Jones>

    For a row name, the provided interface is like a Python
    dictionary. Requesting an item using its index will retrieve the
    value from the agent (the server)::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> m.ifDescr[1]
        <String: lo>
        >>> m.ifName[1] = "Loopback interface"

    Also, it is possible to iterate on a row name to get all available
    values for index::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> for idx in m.ifDescr:
        ...     print(m.ifDescr[idx])

    You can get a slice of index values from a table by iterating on
    a row name subscripted by a partial index::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> for idx in m.ipNetToMediaPhysAddress[1]:
        ...     print(idx)
        (<Integer: 1>, <IpAddress: 127.0.0.1>)

    You can use multivalue indexes in two ways: using Pythonic
    multi-dimensional dict syntax, or by providing a tuple containing
    index values::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> m.ipNetToMediaPhysAddress[1]['127.0.0.1']
        <String: aa:bb:cc:dd:ee:ff>
        >>> m.ipNetToMediaPhysAddress[1, '127.0.0.1']
        <String: aa:bb:cc:dd:ee:ff>

    A context manager is also provided. Any modification issued inside
    the context will be delayed until the end of the context and then
    grouped into a single SNMP PDU to be executed atomically::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> with m:
        ...     m.ifName[1] = "Loopback interface"
        ...     m.ifName[2] = "First interface"

    Any error will be turned into an exception::

        >>> load("IF-MIB")
        >>> m = Manager("localhost", "private")
        >>> m.ifDescr[999]
        Traceback (most recent call last):
            ...
        SNMPNoSuchName: There is no such variable name in this MIB.

    """

    # do we want this object to be populated with all nodes?
    _complete = False

    def __init__(self,
                 host="localhost",
                 community="public", version=2,
                 cache=False, none=False,
                 timeout=None, retries=None,
                 loose=False, bulk=40,
                 # SNMPv3
                 secname=None,
                 authprotocol=None, authpassword=None,
                 privprotocol=None, privpassword=None,
                 contextname=None):
        """Create a new SNMP manager. Some of the parameters are explained in
        :meth:`snmp.Session.__init__`.

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
        :param cache: Should caching be enabled? This can be either a
            boolean or an integer to specify the cache timeout in
            seconds. If `True`, the default timeout is 5 seconds.
        :type cache: bool or int
        :param none: Should `None` be returned when the agent does not
            know the requested OID? If `True`, `None` will be returned
            when requesting an inexisting scalar or column.
        :type none: bool
        :param timeout: Use the specified value in seconds as timeout.
        :type timeout: int
        :param retries: How many times the request should be retried?
        :type retries: int
        :param loose: Enable loose typing. When type coercion fails
            (for example when a MIB declare an element to be an ASCII
            string while it is not), just return the raw result
            instead of an exception. This mode should be enabled with
            caution. Patching the MIB is a better idea.
        :type loose: bool
        :param bulk: Max-repetition to use to speed up MIB walking
            with `GETBULK`. Set to `0` to disable.
        :type bulk: int
        """
        if host is None:
            host = Manager._host
        self._host = host
        self._session = snmp.Session(host, community, version,
                                     secname,
                                     authprotocol, authpassword,
                                     privprotocol, privpassword,
                                     contextname=contextname,
                                     bulk=bulk)
        if timeout is not None:
            self._session.timeout = int(timeout * 1000000)
        if retries is not None:
            self._session.retries = retries
        if cache:
            if cache is True:
                self._session = CachedSession(self._session)
            else:
                self._session = CachedSession(self._session, cache)
        if none:
            self._session = NoneSession(self._session)
        self._loose = loose
        self._loaded = loaded

        # To be able to clone, we save the arguments provided to the
        # constructor in a generic way
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        self._constructor_args = {a: values[a]
                                  for a in args
                                  if a != 'self'}

    def _locate(self, attribute):
        for m in self._loaded:
            try:
                a = mib.get(m, attribute)
                return (m, a)
            except mib.SMIException:
                pass
        raise AttributeError("{} not found in any MIBs".format(attribute))

    def __getattribute__(self, attribute):
        if attribute.startswith("_"):
            return object.__getattribute__(self, attribute)
        m, a = self._locate(attribute)
        if isinstance(a, mib.Scalar):
            oid, result = self._session.get(a.oid + (0,))[0]
            if result is not None:
                try:
                    return a.type(a, result)
                except ValueError:
                    if self._loose:
                        return result
                    raise
            return None
        elif isinstance(a, mib.Column):
            return ProxyColumn(self._session, a, self._loose)
        elif isinstance(a, mib.Table):
            return ProxyTable(self._session, a, self._loose)
        raise NotImplementedError

    def __setattr__(self, attribute, value):
        if attribute.startswith("_"):
            return object.__setattr__(self, attribute, value)
        m, a = self._locate(attribute)
        if not isinstance(value, basictypes.Type):
            value = a.type(a, value, raw=False)
        if isinstance(a, mib.Scalar):
            self._session.set(a.oid + (0,), value)
            return
        raise AttributeError("{} is not writable".format(attribute))

    def __getitem__(self, modulename):
        modulename = modulename.encode('ascii')
        for m in loaded:
            if modulename == m:
                return MibRestrictedManager(self, [m])
        raise KeyError("{} is not a loaded module".format(modulename))

    def __repr__(self):
        return "<Manager for {}>".format(self._host)

    def __enter__(self):

        """In a context, we group all "set" into a single request"""
        self._osession = self._session
        self._session = DelayedSetSession(self._session)
        return self

    def __exit__(self, type, value, traceback):
        """When we exit, we should execute all "set" requests"""
        try:
            if type is None:
                self._session.commit()
        finally:
            self._session = self._osession
            del self._osession


class Proxy:
    """A proxy for some base type, notably a column or a table."""

    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__,
                                    repr(self.proxy)[1:-1])


class ProxyIter(Proxy, Sized, Iterable, Container):
    """Proxy for an iterable sequence.

    This a proxy offering the ABC of an iterable sequence (something
    like a set but without set operations). This will be used by both
    `ProxyColumn` and `ProxyTable`.
    """

    def _op(self, op, index, *args):
        if not isinstance(index, tuple):
            index = (index,)
        indextype = self.proxy.table.index
        if len(indextype) != len(index):
            raise ValueError(
                "{} column uses the following "
                "indexes: {!r}".format(self.proxy, indextype))
        oidindex = []
        for i, ind in enumerate(index):
            # Cast to the correct type since we need "toOid()"
            ind = indextype[i].type(indextype[i], ind, raw=False)
            implied = self.proxy.table.implied and i == len(index)-1
            oidindex.extend(ind.toOid(implied))
        result = getattr(
            self.session,
            op)(self.proxy.oid + tuple(oidindex),
                *args)
        if op != "set":
            oid, result = result[0]
            if result is not None:
                try:
                    return self.proxy.type(self.proxy, result)
                except ValueError:
                    if self._loose:
                        return result
                    raise
            return None

    def __contains__(self, object):
        try:
            self._op("get", object)
        except Exception:
            return False
        return True

    def __iter__(self):
        for k, _ in self.iteritems():
            yield k

    def __len__(self):
        len(list(self.iteritems()))

    def items(self, *args, **kwargs):
        return self.iteritems(*args, **kwargs)

    def iteritems(self, table_filter=None):
        count = 0
        oid = self.proxy.oid
        indexes = self.proxy.table.index

        if table_filter is not None:
            if len(table_filter) >= len(indexes):
                raise ValueError("Table filter has too many elements")
            oid_suffix = []
            # Convert filter elements to correct types
            for i, part in enumerate(table_filter):
                part = indexes[i].type(indexes[i], part, raw=False)
                # implied = False:
                #   index never includes last element
                #   (see 'len(table_filter) >= len(indexes)')
                oid_suffix.extend(part.toOid(implied=False))
            oid += tuple(oid_suffix)

        walk_oid = oid
        for noid, result in self.session.walk(oid):
            if noid <= oid:
                noid = None
                break
            oid = noid
            if not(len(oid) >= len(walk_oid) and
                    oid[:len(walk_oid)] ==
                    walk_oid[:len(walk_oid)]):
                noid = None
                break

            # oid should be turned into index
            index = tuple(oid[len(self.proxy.oid):])
            target = []
            for i, x in enumerate(indexes):
                implied = self.proxy.table.implied and i == len(indexes)-1
                l, o = x.type.fromOid(x, index, implied)
                target.append(x.type(x, o))
                index = index[l:]
            count = count + 1
            if result is not None:
                try:
                    result = self.proxy.type(self.proxy, result)
                except ValueError:
                    if not self._loose:
                        raise
            if len(target) == 1:
                # Should work most of the time
                yield target[0], result
            else:
                yield tuple(target), result

        if count == 0:
            # We did not find any element. Is it because the column is
            # empty or because the column does not exist. We do a SNMP
            # GET to know. If we get a "No such instance" exception,
            # this means the column is empty. If we get "No such
            # object", this means the column does not exist. We cannot
            # make such a distinction with SNMPv1.
            try:
                self.session.get(self.proxy.oid)
            except snmp.SNMPNoSuchInstance:
                # OK, the set of result is really empty
                return
            except snmp.SNMPNoAccess:
                # Some implementations seem to return NoAccess (PySNMP is one)
                return
            except snmp.SNMPNoSuchName:
                # SNMPv1, we don't know
                pass
            except snmp.SNMPNoSuchObject:
                # The result is empty because the column is unknown
                raise


class ProxyTable(ProxyIter):
    """Proxy for table access.

    We just use the first accessible index as a column. However, the mapping
    operations are not available.
    """

    def __init__(self, session, table, loose):
        self.proxy = None
        for column in table.columns:
            if column.accessible:
                self.proxy = column
                break
        if self.proxy is None:
            raise NotImplementedError("No accessible column in the table.")
        self.session = session
        self._loose = loose


class ProxyColumn(ProxyIter, MutableMapping):
    """Proxy for column access"""

    def __init__(self, session, column, loose, oid_suffix=()):
        self.proxy = column
        self.session = session
        self._loose = loose
        self._oid_suffix = oid_suffix

    def __getitem__(self, index):
        # If supplied index is partial we return new ProxyColumn
        # with appended OID suffix
        idx_len = len(self.proxy.table.index)
        suffix_len = len(self._oid_suffix)
        if isinstance(index, tuple):
            if len(index) + suffix_len < idx_len:
                return self._partial(index)
        elif idx_len > suffix_len + 1:
            return self._partial((index,))

        # Otherwise a read op is made
        if not isinstance(index, tuple):
            index = (index,)
        return self._op("get", self._oid_suffix + index)

    def __setitem__(self, index, value):
        if not isinstance(value, basictypes.Type):
            value = self.proxy.type(self.proxy, value, raw=False)
        if not isinstance(index, tuple):
            index = (index,)
        self._op("set", self._oid_suffix + index, value)

    def __delitem__(self, index):
        raise NotImplementedError("cannot suppress a column")

    def __contains__(self, index):
        if not isinstance(index, tuple):
            index = (index,)
        return ProxyIter.__contains__(self, self._oid_suffix + index)

    def _partial(self, index):
        """Create new ProxyColumn based on current one,
        but with appended OID suffix"""
        new_suffix = self._oid_suffix + index
        return ProxyColumn(self.session, self.proxy, self._loose, new_suffix)

    def items(self, *args, **kwargs):
        return self.iteritems(*args, **kwargs)

    def iteritems(self, table_filter=None):
        resulting_filter = self._oid_suffix
        if table_filter is not None:
            if not isinstance(table_filter, tuple):
                table_filter = (table_filter,)
            resulting_filter += table_filter
        return ProxyIter.iteritems(self, resulting_filter)


loaded = []


def load(mibname):
    """Load a MIB in memory.

    :param mibname: MIB name or filename
    :type mibname: str
    """
    m = mib.load(mibname)
    if m not in loaded:
        loaded.append(m)
        if Manager._complete:
            for o in mib.getScalars(m) + \
                    mib.getColumns(m) + \
                    mib.getTables(m):
                setattr(Manager, str(o), 1)
