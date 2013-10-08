snimpy -- Interactive SNMP tool
===============================

[![Build Status](https://travis-ci.org/vincentbernat/snimpy.png?branch=master)](https://travis-ci.org/vincentbernat/snimpy)
[![Pypi package](https://badge.fury.io/py/snimpy.png)](http://badge.fury.io/py/snimpy)
[![Downloads](https://pypip.in/d/snimpy/badge.png)](https://crate.io/packages/snimpy?version=latest)

 https://github.com/vincentbernat/snimpy

Introduction
------------

Snimpy is a Python-based tool providing a simple interface to build
SNMP query. Here is a very simplistic example that allows to display
the routing table of a given host:

```python
load("IP-FORWARD-MIB")
m=M("localhost", "public", 2)
routes = m.ipCidrRouteNextHop
for x in routes:
    net, netmask, tos, src = x
    print "%15s/%-15s via %-15s src %-15s" % (net, netmask, routes[x], src)
```

You can either use snimpy interactively throught its console (derived
from Python own console or from IPython if available) or write snimpy
scripts which are just Python scripts with some global variables
available.

This is not a general-use SNMP module. You can find better ones:

 - pycopia
 - pynetsnmp, a ctype based implementation using Net-SNMP
 - PySNMP, a pure Python implementation
 - Net-SNMP own library Python
 - many others

This is not really a replacement for snmpget, snmpwalk and
snmpset. You cannot query arbitrary OID and you can only walk tables,
not any node. Moreover, if remote host sends bogus value, snimpy will
just stop with an exception (this is also a feature).

Snimpy is aimed at being the more Pythonic possible. You should forget
that you are doing SNMP requests. Snimpy will rely on MIB to hide SNMP
details. Here are some "features" of snmimpy:

 - MIB parser based on libsmi  (through CFFI)
 - SNMP requests are handled by PySNMP
 - scalars are just attributes of your session object
 - columns are like a Python dictionary and made available as
   an attribute
 - getting an attribute is like issuing a GET method
 - setting an attribute is like issuing a SET method
 - iterating over a table is like using GETNEXT
 - when something goes wrong, you get an exception

License
-------

Snimpy is licensed under MIT/X11 license. See at the top of source
files for details.

Installation and usage
----------------------

You can install using:

     python setup.py build
     python setup.py install

Or without installation:

     python bin/snimpy.py

See examples in `examples/` directory for some real examples on how to
use it.

If you don't specify a file, the interactive console is
spawned. Otherwise, the given script is executed and the remaining
arguments are served as arguments for the script.

You get a classic Python environment. There are two additional objects
available:

 - The `load()` method that takes a MIB name or a path to a
   filename. The MIB will be loaded into memory and made available in
   all SNMP managers:

```python
load("IF-MIB")
load("/usr/share/mibs/ietf/IF-MIB")
```

 - the `M` class which is used to instantiate a manager (a SNMP client):

```python
m = M()
m = M(host="localhost", community="private", version=2)
m = M("localhost", "private", 2)
m = M(community="private")
m = M(version=3,
      secname="readonly",
      authprotocol="MD5", authpassword="authpass",
      privprotocol="AES", privpassword="privpass")
```

A manager instance contains all the scalars and the columns that are
in the MIB loaded with the load() method. There is no table, node or
other entities. For a scalar, getting and setting a value is a simple
as :

```python
print m.sysDescr
m.sysName = "newhostname"
```

For a column, you get a dictionary-like interface:

```python
for index in m.ifDescr: print repr(m.ifDescr[i])
m.ifAdminStatus[3] = "down"
```

If you want to group several write into a single request, you can do
it with `with` keyword of Python 2.5+:

```python
with M("localhost", "private") as m:
    m.sysName = "toto"
    m.ifAdminStatus[20] = "down"
```

Or:

```python
m = M("localhost", "private")
with m:
    m.sysName = "toto"
    m.ifAdminStatus[20] = "down"
```

There is also a caching mechanism which is disabled by default:

```python
import time
m = M("localhost", cache=True)
print m.sysUpTime
time.sleep(1)
print m.sysUpTime
time.sleep(1)
print m.sysUpTime
time.sleep(10)
print m.sysUpTime
```

You can also use the number of seconds the cache should be hold.

```python
m = M("localhost", cache=20)
```

You can also set a custom timeout and a custom retries value. For
example, to wait 2.5 seconds before timeout occurs and retry 10 times,
you can use:

```python
m = M("localhost", timeout=2.5, retry=10)
```

snimpy will stop on any error with an exception. This allows you to
not check the result at each step. Your script can't go awry. If this
behaviour does not suit you, it is possible to suppress exceptions
when querying inexistant objects. Instead of an exception, you'll get
`None`.

```python
m = M("localhost", none=True)
```

That's all!

Threads
-------

snimpy should be thread-safe. There are two ground rules:

 1. You must load MIB before invoking additional threads.
 2. You must not share a session between several threads.

Why another tool?
-----------------

There are a lot of SNMP tools available but most of them have
important drawback when you need to reliably automatize operations.

snmpget, snmpset and snmpwalk are difficult to use in scripts. Errors
are printed on standard output and there is no easy way to tell if the
command was successful or not. Moreover, results can be multiline (a
long HexString for example). At least, automatisation is done through
the shell and OID or bit manipulation are quite difficult.

Net-SNMP provides officiel bindings for Perl and
Python. Unfortunately, the integration is quite poor. You don't have
an easy way to load and browse MIBs and error handling is
inexistant. For example, the Python bindings will return None for a
non-existant OID. Having to check for this on each request is quite
cumbersome.

For Python, there are other bindings. For example, pysnmp provides a
pure Python implementation. However, MIBs need to be
compiled. Moreover, the exposed interface is still low-level. Sending
a simple SNMP GET can either take 10 lines or one line wrapped into 10
lines.

Some other Python bindings are not maintained any more. For example
yasnmp does not compile with current libsnmp.

The two main points of snimpy are:

 - very high-level interface
 - raise exceptions when something goes wrong

About "major SMI errors"
------------------------

If you get an exception like `RAPID-CITY contains major SMI errors
(check with smilint -s -l1)`, this means that there are some grave
errors in this MIB which may lead to segfaults if the MIB is used as
is. Usually, this means that some identifier are unknown. Use `smilint
-s -l1 YOUR-MIB` to see what the problem is and try to solve all
problems reported by lines beginning by "[1]".

For example :

    $ smilint -s -l1 rapid_city.mib
    rapid_city.mib:30: [1] failed to locate MIB module `IGMP-MIB'
    rapid_city.mib:32: [1] failed to locate MIB module `DVMRP-MIB'
    rapid_city.mib:34: [1] failed to locate MIB module `IGMP-MIB'
    rapid_city.mib:27842: [1] unknown object identifier label `igmpInterfaceIfIndex'
    rapid_city.mib:27843: [1] unknown object identifier label `igmpInterfaceQuerier'
    rapid_city.mib:27876: [1] unknown object identifier label `dvmrpInterfaceIfIndex'
    rapid_city.mib:27877: [1] unknown object identifier label `dvmrpInterfaceOperState'
    rapid_city.mib:27894: [1] unknown object identifier label `dvmrpNeighborIfIndex'
    rapid_city.mib:27895: [1] unknown object identifier label `dvmrpNeighborAddress'
    rapid_city.mib:32858: [1] unknown object identifier label `igmpCacheAddress'
    rapid_city.mib:32858: [1] unknown object identifier label `igmpCacheIfIndex'

To solve the problem here, load IGMP-MIB and DVMRP-MIB before loading
rapid_city.mib. IGMP-MIB should be pretty easy to find. For DVMRP-MIB, try Google. You should find [this RFC][1].

[1]: http://tools.ietf.org/id/draft-thaler-dvmrp-mib-09.txt

Download it and use `smistrip` to get the MIB. You can check that the
problem is solved with this command :

    $ smilint -p ../cisco/IGMP-MIB.my -p ./DVMRP-MIB -s -l1 rapid_city.mib

You will get a lot of errors in IGMP-MIB and DVMRP-MIB but no line
with `[1]`: everything should be fine. To load `rapid_city.mib`, you need to do this:

```python
load("../cisco/IGMP-MIB.my")
load("./DVMRP-MIB")
load("rapid_city.mib")
```
