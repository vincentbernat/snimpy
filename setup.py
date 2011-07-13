from snimpy.version import VERSION
from distutils.core import setup, Extension

if __name__ == "__main__":
    setup(name="snimpy",
          version=VERSION,
          classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Operating System :: POSIX',
            'Programming Language :: C',
            'Programming Language :: Python',
            'Topic :: System :: Networking',
            'Topic :: Utilities',
            ],
          url='https://github.com/vincentbernat/snimpy',
          description="interactive SNMP tool",
          author="Vincent Bernat",
          author_email="bernat@luffy.cx",
          packages=["snimpy"],
          scripts=["bin/snimpy"],
          data_files = [('share/man/man1', ['man/snimpy.1'])],
          ext_modules = [
            Extension('snimpy.mib',
                      libraries = ['smi'],
                      sources= ['snimpy/mib.c']),
            Extension('snimpy.snmp',
                      libraries = ['netsnmp', 'crypto'],
                      sources= ['snimpy/snmp.c'])
            ]
          )
    
