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

    $ sudo apt-get install libsmi2-dev

On RedHat and similar, you can use::

    $ sudo yum install libsmi-devel

On OS X, if you are using homebrew_, you can use::

    $ brew install libsmi

.. _libsmi: http://www.ibr.cs.tu-bs.de/projects/libsmi/
.. _homebrew: http://brew.sh

On Debian and Ubuntu, *Snimpy* is also available as a package you can
install with::

    $ sudo apt-get install snimpy
