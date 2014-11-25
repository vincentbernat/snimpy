========
Usage
========

Invocation
----------

There are three ways to use *Snimpy*:

1. Interactively through a console.
2. As a script interpreter.
3. As a regular Python module.

Interactive use
+++++++++++++++

*Snimpy* can be invoked with either `snimpy` or `python -m
snimpy`. Without any other arhument, the interactive console is
spawned. Otherwise, the given script is executed and the remaining
arguments are served as arguments for the script.

When running interactively, you get a classic Python
environment. There are two additional objects available:

* The `load()` method that takes a MIB name or a path to a
  filename. The MIB will be loaded into memory and made available in
  all SNMP managers::

    load("IF-MIB")
    load("/usr/share/mibs/ietf/IF-MIB")

* The `M` class which is used to instantiate a manager (a SNMP
  client)::

    m = M()
    m = M(host="localhost", community="private", version=2)
    m = M("localhost", "private", 2)
    m = M(community="private")
    m = M(version=3,
          secname="readonly",
          authprotocol="MD5", authpassword="authpass",
          privprotocol="AES", privpassword="privpass")

A manager instance contains all the scalars and the columns in MIB
loaded with the `load()` method. There is no table, node or other
entities. For a scalar, getting and setting a value is a simple as::

    print m.sysDescr
    m.sysName = "newhostname"

For a column, you get a dictionary-like interface::

    for index in m.ifDescr: 
	print repr(m.ifDescr[index])
    m.ifAdminStatus[3] = "down"

If you want to group several write into a single request, you can do
it with `with` keyword::

    with M("localhost", "private") as m:
        m.sysName = "toto"
        m.ifAdminStatus[20] = "down"

There is also a caching mechanism which is disabled by default::

    import time
    m = M("localhost", cache=True)
    print m.sysUpTime
    time.sleep(1)
    print m.sysUpTime
    time.sleep(1)
    print m.sysUpTime
    time.sleep(10)
    print m.sysUpTime

You can also specify the number of seconds data should be cached::

    m = M("localhost", cache=20)

It's also possible to set a custom timeout and a custom value for the
number of retries. For example, to wait 2.5 seconds before timeout
occurs and retry 10 times, you can use::

    m = M("localhost", timeout=2.5, retries=10)

*Snimpy* will stop on any error with an exception. This allows you to
not check the result at each step. Your script can't go awry. If this
behaviour does not suit you, it is possible to suppress exceptions
when querying inexistant objects. Instead of an exception, you'll get
`None`::

    m = M("localhost", none=True)

Script interpreter
++++++++++++++++++

*Snimpy* can be run as a script interpreter. There are two ways to do
this. The first one is to invoke *Snimpy* and provide a script name as
well as any argument you want to pass to the script::

    $ snimpy example-script.py arg1 arg2
    $ python -m snimpy example-script.py arg1 arg2

The second one is to use *Snimpy* as a shebang_ interpreter. For
example, here is a simple script::

    #!/usr/bin/env snimpy
    
    load("IF-MIB")
    m = M("localhost")
    print(m.ifDescr[0])

The script can be invoked as any shell script.

.. _shebang: http://en.wikipedia.org/wiki/Shebang_(Unix)

Inside the script, you can use any valid Python code. You also get the
`load()` method and the `M` class available, like for the interactive
use.

Regular Python module
+++++++++++++++++++++

*Snimpy* can also be imported as a regular Python module::

    from snimpy.manager import Manager as M
    from snimpy.manager import load
    
    load("IF-MIB")
    m = M("localhost")
    print(m.ifDescr[0])

About "major SMI errors"
------------------------

If you get an exception like `RAPID-CITY contains major SMI errors
(check with smilint -s -l1)`, this means that there are some grave
errors in this MIB which may lead to segfaults if the MIB is used as
is. Usually, this means that some identifier are unknown. Use `smilint
-s -l1 YOUR-MIB` to see what the problem is and try to solve all
problems reported by lines beginning by `[1]`.

For example::

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

To solve the problem here, load `IGMP-MIB` and `DVMRP-MIB` before
loading `rapid_city.mib`. `IGMP-MIB` should be pretty easy to
find. For `DVMRP-MIB`, try Google.

Download it and use `smistrip` to get the MIB. You can check that the
problem is solved with this command::

    $ smilint -p ../cisco/IGMP-MIB.my -p ./DVMRP-MIB -s -l1 rapid_city.mib

You will get a lot of errors in `IGMP-MIB` and `DVMRP-MIB` but no line
with `[1]`: everything should be fine. To load `rapid_city.mib`, you
need to do this::

    load("../cisco/IGMP-MIB.my")
    load("./DVMRP-MIB")
    load("rapid_city.mib")
