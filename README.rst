===============================
snimpy
===============================

.. image:: https://badge.fury.io/py/snimpy.svg
    :target: http://badge.fury.io/py/snimpy
    
.. image:: https://github.com/vincentbernat/snimpy/workflows/Tests/badge.svg

.. image:: https://coveralls.io/repos/vincentbernat/snimpy/badge.svg
        :target: https://coveralls.io/r/vincentbernat/snimpy

---

 Interactive SNMP tool.

*Snimpy* is a Python-based tool providing a simple interface to build
SNMP query. Here is a very simplistic example that allows us to
display the routing table of a given host::

    load("IP-FORWARD-MIB")
    m=M("localhost", "public", 2)
    routes = m.ipCidrRouteNextHop
    for x in routes:
        net, netmask, tos, src = x
        print("%15s/%-15s via %-15s src %-15s" % (net, netmask, routes[x], src))

You can either use *Snimpy* interactively throught its console
(derived from Python own console or from IPython_ if available) or
write *Snimpy* scripts which are just Python scripts with some global
variables available.

.. _IPython: http://ipython.org

* Free software: ISC license
* Documentation: http://snimpy.rtfd.org.

*Snimpy* requires libsmi_ to work correctly. See the documentation for
more information.

.. _libsmi: https://www.ibr.cs.tu-bs.de/projects/libsmi/

Features
--------

*Snimpy* is aimed at being the more Pythonic possible. You should forget
that you are doing SNMP requests. *Snimpy* will rely on MIB to hide SNMP
details. Here are some "features":

* MIB parser based on libsmi  (through CFFI)
* SNMP requests are handled by PySNMP (SNMPv1, SNMPv2 and SNMPv3
  support)
* scalars are just attributes of your session object
* columns are like a Python dictionary and made available as an
  attribute
* getting an attribute is like issuing a GET method
* setting an attribute is like issuing a SET method
* iterating over a table is like using GETNEXT
* when something goes wrong, you get an exception
