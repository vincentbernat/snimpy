"""interactive SNMP tool"""

try:
    from snimpy._version import __version__  # nopep8
except ImportError:
    __version__ = '0.0~dev'
