from snimpy.version import VERSION
from distutils.core import setup

if __name__ == "__main__":
    setup(name="snimpy",
          version=VERSION,
          description="interactive SNMP tool",
          author="Vincent Bernat",
          author_email="bernat@luffy.cx",
          packages=["snimpy"],
          requires=["ctypes (>= 1.1)",],
          scripts=["bin/snimpy"],
          )
