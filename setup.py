from setuptools import setup
import snimpy

try:
    import multiprocessing
    import pysnmp
except ImportError:
    pass

try:
    from subprocess import check_output
except ImportError:
    import subprocess
    def check_output(*popenargs, **kwargs):
        r"""Run command with arguments and return its output as a byte string.

        Backported from Python 2.7. See:
          https://gist.github.com/edufelipe/1027906
        """
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
        return output

if __name__ == "__main__":
    # MIB module
    try:
        import snimpy.mib
        ext_modules = [ snimpy.mib.ffi.verifier.get_extension() ]
    except ImportError:
        ext_modules = []

    setup(name="snimpy",
          version=snimpy.__version__,
          classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: ISC License',
            'Operating System :: POSIX',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Topic :: System :: Networking',
            'Topic :: Utilities',
            'Topic :: System :: Monitoring'
            ],
          url='https://github.com/vincentbernat/snimpy',
          description=snimpy.__doc__,
          author=snimpy.__author__,
          author_email=snimpy.__email__,
          packages=["snimpy"],
          entry_points = {
              'console_scripts': [
                  'snimpy = snimpy.main:interact',
              ],
          },
          data_files = [('share/man/man1', ['man/snimpy.1'])],
          ext_modules = ext_modules,
          zip_safe = False,
          install_requires = [ "cffi", "pysnmp >= 4" ],
          setup_requires = [ "cffi" ],
          tests_require = [ "cffi", "pysnmp >= 4", "nose", "mock" ],
          test_suite="nose.collector"
          )
