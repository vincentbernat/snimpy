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
Very high level interface to SNMP and MIB for Snimpy
"""

from time import time
from UserDict import DictMixin
import snmp, mib, basictypes

class DelayedSetSession(object):
    """SNMP session that is able to delay SET requests.

    This is an adapter. The constructor takes the original (not
    delayed) session.
    """

    def __init__(self, session):
        self.session = session
        self.setters = []

    def get(self, *args):
        return self.session.get(*args)
    def getnext(self, *args):
        return self.session.getnext(*args)
    def set(self, *args):
        self.setters.extend(args)

    def commit(self):
        if self.setters:
            self.session.set(*self.setters)

class NoneSession(object):
    """SNMP session that will return None on unsucessful GET requests.

    In a normal session, a GET request returning `No such instance`
    error will trigger an exception. This session will catch such an
    error and return None instead.
    """

    def __init__(self, session):
        self.session = session
        self.set = self.session.set
        self.getnext = self.session.getnext

    def get(self, *args):
        try:
            return self.session.get(*args)
        except (snmp.SNMPNoSuchName,
                snmp.SNMPNoSuchObject,
                snmp.SNMPNoSuchInstance):
            if len(args) > 1:
                # We can't handle this case yet because we don't know
                # which value is unavailable.
                raise
            return ((args[0], None),)

class CachedSession(object):
    """SNMP session using a cache.

    This is an adapter. The constructor takes the original session.
    """

    def __init__(self, session, timeout=5):
        self.session = session
        self.cache = {}
        self.timeout = timeout
        self.count = 0

    def set(self, *args):
        return self.session.set(*args)

    def getorgetnext(self, op, *args):
        self.count += 1
        if (op, args) in self.cache:
            t, v = self.cache[op, args]
            if time() - t < self.timeout:
                return v
        value = getattr(self.session, op)(*args)
        self.cache[op, args] = [time(), value]
        self.flush()
        return value

    def get(self, *args):
        return self.getorgetnext("get", *args)
    def getnext(self, *args):
        return self.getorgetnext("getnext", *args)

    def flush(self):
        if self.count < 1000:
            return
        keys = self.cache.keys()
        for k in keys:
            if time() - self.cache[k][0] > self.timeout:
                del self.cache[k]
        self.count = 0

class Manager(object):

    # do we want this object to be populated with all nodes?
    _complete = False

    def __init__(self,
                 host="localhost",
                 community=None, version=None,
                 cache=False, none=False,
                 timeout=None, retries=None,
                 # SNMPv3
                 seclevel=None, secname=None,
                 authprotocol=None, authpassword=None,
                 privprotocol=None, privpassword=None):
        if host is None:
            host = Manager._host
        self._host = host
        if version is None:
            version = -1
        self._session = snmp.Session(host, community, version,
                                     seclevel, secname,
                                     authprotocol, authpassword,
                                     privprotocol, privpassword)
        if timeout is not None:
            self._session.timeout = int(timeout*1000000)
        if retries is not None:
            self._session.retries = retries
        if cache:
            if cache is True:
                self._session = CachedSession(self._session)
            else:
                self._session = CachedSession(self._session, cache)
        if none:
            self._session = NoneSession(self._session)

    def _locate(self, attribute):
        for m in loaded:
            try:
                a = mib.get(m, attribute)
                return (m,a)
            except mib.SMIException:
                pass
        raise AttributeError("%s is not an attribute" % attribute)


    def __getattribute__(self, attribute):
        if attribute.startswith("_"):
            return object.__getattribute__(self, attribute)
        m, a = self._locate(attribute)
        if isinstance(a, mib.Scalar):
            oid, result = self._session.get(a.oid + (0,))[0]
            if result is not None:
                return a.type(a, result)
            return None
        elif isinstance(a, mib.Column):
            return ProxyColumn(self._session, a)
        raise NotImplementedError

    def __setattr__(self, attribute, value):
        if attribute.startswith("_"):
            return object.__setattr__(self, attribute, value)
        m, a = self._locate(attribute)
        if not isinstance(value, basictypes.Type):
            value = a.type(a, value)
        if isinstance(a, mib.Scalar):
            self._session.set(a.oid + (0,), value)
            return
        raise AttributeError("%s is not writable" % attribute)

    def __repr__(self):
        return "<Manager for %s>" % self._host

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

    def __repr__(self):
        return "<%s for %s>" % (self.__class__.__name__,
                                repr(self.proxy)[1:-1])

class ProxyColumn(Proxy, DictMixin):
    """Proxy for column access"""

    def __init__(self, session, column):
        self.proxy = column
        self.session = session

    def _op(self, op, index, *args):
        if type(index) is not tuple:
            index = (index,)
        indextype = self.proxy.table.index
        if len(indextype) != len(index):
            raise ValueError(
                "%s column uses the following indexes: %r" % (str(self.proxy),
                                                              indextype))
        oidindex = []
        for i, ind in enumerate(index):
            ind = indextype[i].type(indextype[i], ind) # Cast to the
                                                       # correct type
                                                       # since we need
                                                       # "toOid()"
            oidindex.extend(ind.toOid())
        result = getattr(self.session, op)(self.proxy.oid + tuple(oidindex), *args)
        if op != "set":
            oid, result = result[0]
            if result is not None:
                return self.proxy.type(self.proxy, result)
            return None

    def __getitem__(self, index):
        return self._op("get", index)

    def __setitem__(self, index, value):
        if not isinstance(value, basictypes.Type):
            value = self.proxy.type(self.proxy, value)
        self._op("set", index, value)

    def keys(self):
        return [k for k in self]

    def has_key(self, object):
        try:
            self._op("get", object)
        except:
            return False
        return True

    def __iter__(self):
        for k, _ in self.iteritems():
            yield k

    def iteritems(self):
        count = 0
        oid = self.proxy.oid
        indexes = self.proxy.table.index

        while True:
            try:
                if self.session.bulk and self.session.use_bulk:
                    results = self.session.getbulk(oid)
                else:
                    results = self.session.getnext(oid)
            except snmp.SNMPEndOfMibView:
                break

            for noid, result in results:
                if noid <= oid:
                    noid = None
                    break
                oid = noid
                if not((len(oid) >= len(self.proxy.oid) and
                    oid[:len(self.proxy.oid)] == self.proxy.oid[:len(self.proxy.oid)])):
                    noid = None
                    break

                # oid should be turned into index
                index = oid[len(self.proxy.oid):]
                target = []
                for x in indexes:
                    l, o = x.type.fromOid(x, tuple(index))
                    target.append(x.type(x, o))
                    index = index[l:]
                count = count + 1
                if len(target) == 1:
                    # Should work most of the time
                    yield target[0], result
                else:
                    yield tuple(target), result

            if noid is None:
                break

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
                raise StopIteration
            except snmp.SNMPNoSuchName:
                # SNMPv1, we don't know
                pass
            except snmp.SNMPNoSuchObject:
                # The result is empty because the column is unknown
                raise

        raise StopIteration


loaded = []
def load(mibname):
    """Load a MIB"""
    m = mib.load(mibname)
    if m not in loaded:
        loaded.append(m)
        if Manager._complete:
            for o in mib.getScalars(m) + \
                    mib.getColumns(m):
                setattr(Manager, str(o), 1)

