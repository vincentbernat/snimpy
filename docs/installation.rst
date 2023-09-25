============
Installation
============

At the command line::

    $ easy_install snimpy

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv snimpy
    $ pip install snimpy

*Snimpy* requires libsmi_, a library to access SMI MIB
information. You need to install both the library and the development
headers. If *Snimpy* complains to not find ``smi.h``, you can help by
specifying where this file is located by exporting the appropriate
environment variable::

    $ export C_INCLUDE_PATH=/opt/local/include

On Debian/Ubuntu, you can install libsmi with::

    $ sudo apt-get install libffi-dev libsmi2-dev snmp-mibs-downloader

On RedHat and similar, you can use::

    $ sudo yum install libffi-devel libsmi-devel

On OS X, if you are using homebrew_, you can use::

    $ brew install libffi
    $ brew install libsmi

.. _libsmi: http://www.ibr.cs.tu-bs.de/projects/libsmi/
.. _homebrew: http://brew.sh

On Debian and Ubuntu, *Snimpy* is also available as a package you can
install with::

    $ sudo apt-get install snimpy

If you plan to use custom MIBs, note that as snimpy relies on libsmi_ to
find the MIBs, so you have to add the path to these MIBs in /etc/smi.conf or
$HOME/.smirc .
