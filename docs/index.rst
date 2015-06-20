Snimpy: interactive SNMP tool
====================================================

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

Why another tool?
-----------------

There are a lot of SNMP tools available but most of them have
important drawback when you need to reliably automatize operations.

`snmpget`, `snmpset` and `snmpwalk` are difficult to use in
scripts. Errors are printed on standard output and there is no easy
way to tell if the command was successful or not. Moreover, results
can be multiline (a long HexString for example). At least,
automatisation is done through the shell and OID or bit manipulation
are quite difficult.

Net-SNMP provides officiel bindings for Perl and
Python. Unfortunately, the integration is quite poor. You don't have
an easy way to load and browse MIBs and error handling is
inexistant. For example, the Python bindings will return None for a
non-existant OID. Having to check for this on each request is quite
cumbersome.

For Python, there are other bindings. For example, pysnmp_ provides a
pure Python implementation. However, MIBs need to be
compiled. Moreover, the exposed interface is still low-level. Sending
a simple SNMP GET can either take 10 lines or one line wrapped into 10
lines.

.. _pysnmp: http://pysnmp.sourceforge.net/

The two main points of *Snimpy* are:

* very high-level interface relying on MIBs
* raise exceptions when something goes wrong

Meantime, another Pythonic SNMP library based on Net-SNMP has been
released: `Easy SNMP`_. Its interface is a less Pythonic than *Snimpy*
but it doesn't need MIBs to work.

.. _Easy SNMP: https://github.com/fgimian/easysnmp

Contents
---------

.. toctree::
   :maxdepth: 1

   installation
   usage
   api
   contributing
   license
   history
