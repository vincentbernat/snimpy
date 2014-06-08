.. :changelog:

History
-------

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
* MIB parsing is still done with libsmi_ but through CFFI instead of a
  C module.
* More unittests. Many bugfixes.

.. _PySNMP: http://pysnmp.sourceforge.net/
.. _libsmi: http://www.ibr.cs.tu-bs.de/projects/libsmi/

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
