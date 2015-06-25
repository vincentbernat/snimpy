"""interactive SNMP tool"""

__author__ = 'Vincent Bernat'
__email__ = 'bernat@luffy.cx'

try:
    from snimpy._version import __version__  # nopep8
except ImportError:
    __version__ = '0.0~dev'
