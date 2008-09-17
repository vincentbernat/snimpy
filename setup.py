from snimpy.version import VERSION
from distutils.core import setup, Extension

if __name__ == "__main__":
    setup(name="snimpy",
          version=VERSION,
          description="interactive SNMP tool",
          author="Vincent Bernat",
          author_email="bernat@luffy.cx",
          packages=["snimpy"],
          scripts=["bin/snimpy"],
          ext_modules = [
            Extension('snimpy.mib',
                      libraries = ['smi'],
                      sources= ['snimpy/mib.c']) ]
          )
    
