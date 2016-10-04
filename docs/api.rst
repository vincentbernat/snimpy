==============
API reference
==============

While *Snimpy* is targeted at being used interactively or through
simple scripts, you can also use it from your Python program.

It provides a high-level interface as well as lower-level
ones. However, the effort is only put in th :mod:`manager` module and
other modules are considered as internal details.

:mod:`manager` module
----------------------

.. automodule:: snimpy.manager
    :members: Manager, load

Internal modules
----------------

Those modules shouldn't be used directly.

:mod:`mib` module
~~~~~~~~~~~~~~~~~

.. automodule:: snimpy.mib
    :members:

:mod:`snmp` module
~~~~~~~~~~~~~~~~~~

.. automodule:: snimpy.snmp
    :members:

:mod:`basictypes` module
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: snimpy.basictypes
    :members:
