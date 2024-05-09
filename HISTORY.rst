.. :changelog:

History
-------

1.0.3 (2024-05-09)
++++++++++++++++++

* Temporarily depend on pysnmp-lextudio < 6 to fix stuck SNMP requests.

1.0.2 (2023-12-12)
++++++++++++++++++

* Compatibility with Python 3.12 by adding dependency to pyasyncore.

1.0.1 (2023-06-30)
++++++++++++++++++

* Switch to pysnmp-lextudio, a maintained fork of PySNMP.

1.0.0 (2021-05-29)
++++++++++++++++++

* Drop compatibility with Python 2.

0.8.14 (2020-04-26)
+++++++++++++++++++

* Add ``items()`` in addition to ``iteritems()`` This is an iterator
  on Python 3 and return a list of items in Python 2.

0.8.13 (2018-10-12)
+++++++++++++++++++

* Compatibility with Python 3.7.
* Fix an issue with implied index when reusing indexes between tables.

0.8.12 (2017-10-02)
+++++++++++++++++++

* Support for more recent versions of IPython.
* Support for SNMPv3 context name.
* Support for notification nodes (MIB only).

0.8.11 (2016-08-13)
+++++++++++++++++++

* Fix IPython interactive shell.
* Fix IPv6 handling for sessions.
* Ability for a session to return None instead of raising an exception.

0.8.10 (2016-02-16)
+++++++++++++++++++

* Ability to walk a table (if the first index is accessible).
* Ability to do a partial walk (courtesy of Alex Unigovsky).

0.8.8 (2015-11-15)
++++++++++++++++++

* Fix thread-safety problem introduced in 0.8.6. This also undo any
  improvement advertised in 0.8.6 when using multiple
  threads. However, performance should be kept when using a single
  thread.

0.8.7 (2015-11-14)
++++++++++++++++++

* Ability to specify a module name when querying a manager.
* Compatibility with PySNMP 4.3
* Array-like interface for OIDs.
* Ability to restrict lookups to a specific MIB: m['IF-MIB'].ifDescr.
* Fix multithread support with SNMPv3 (with a performance impact).

0.8.6 (2015-06-24)
++++++++++++++++++

* Major speed improvement.
* Major memory usage improvement.

0.8.5 (2015-04-04)
++++++++++++++++++

* Ability to set SMI search path (with ``mib.path()``)
* Fix documentation build on *Read the Doc*.
* Add a loose mode to manager to loosen type coercion.

0.8.4 (2015-02-10)
++++++++++++++++++

* More CFFI workarounds, including cross-compilation support.
* Ability to override a node type.
* Automatic workaround for "SNMP too big" error message.

0.8.3 (2014-08-18)
++++++++++++++++++

* IPv6 support.


0.8.2 (2014-06-08)
++++++++++++++++++

* Minor bugfixes.

0.8.1 (2013-10-25)
++++++++++++++++++

* Workaround a problem with CFFI extension installation.

0.8.0 (2013-10-19)
++++++++++++++++++++

* Python 3.3 support. Pypy support.
* PEP8 compliant.
* Sphinx documentation.
* Octet strings with a display hint are now treated differently than
  plain octet strings (unicode). Notably, they can now be set using
  the displayed format (for example, for MAC addresses).

0.7.0 (2013-09-23)
++++++++++++++++++

* Major rewrite.
* SNMP support is now provided through PySNMP_.
* MIB parsing is still done with ``libsmi`` but through CFFI instead of a
  C module.
* More unittests. Many bugfixes.

.. _PySNMP: https://www.pysnmp.com/

0.6.4 (2013-03-21)
++++++++++++++++++

* GETBULK support.
* MacAddress SMI type support.

0.6.3 (2012-04-13)
++++++++++++++++++

* Support for IPython 0.12.
* Minor bugfixes.

0.6.2 (2012-01-19)
++++++++++++++++++

* Ability to return None instead of getting an exception.

0.6.1 (2012-01-14)
++++++++++++++++++

* Thread safety and efficiency.

0.6 (2012-01-10)
++++++++++++++++++

* SNMPv3 support

0.5.1 (2011-08-07)
++++++++++++++++++

* Compatibility with IPython 0.11.
* Custom timeouts and retries.

0.5 (2010-02-03)
++++++++++++++++++

* Check conformity of loaded modules.
* Many bugfixes.

0.4 (2009-06-06)
++++++++++++++++++

* Allow to cache requests.

0.3 (2008-11-23)
++++++++++++++++++

* Provide a manual page.
* Use a context manager to group SET requests.

0.2.1 (2008-09-28)
++++++++++++++++++

* First release on PyPI.
