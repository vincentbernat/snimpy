import shlex
from snimpy.version import VERSION
from setuptools import setup, Extension

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
    smi_cflags = check_output(["pkg-config", "--cflags", "libsmi"])
    smi_ldflags = check_output(["pkg-config", "--libs", "libsmi"])
    snmp_cflags = check_output(["net-snmp-config", "--base-cflags"])
    snmp_ldflags = check_output(["net-snmp-config", "--libs"])
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
          entry_points = {
              'console_scripts': [
                  'snimpy = snimpy.main:interact',
              ],
          },
          data_files = [('share/man/man1', ['man/snimpy.1'])],
          ext_modules = [
            Extension('snimpy.mib',
                      extra_compile_args= shlex.split(smi_cflags),
                      extra_link_args= shlex.split(smi_ldflags),
                      sources= ['snimpy/mib.c']),
            Extension('snimpy.snmp',
                      extra_compile_args= shlex.split(snmp_cflags),
                      extra_link_args= shlex.split(snmp_ldflags),
                      libraries= ['netsnmp', 'crypto'],
                      sources= ['snimpy/snmp.c'])
          ],
          tests_require = [
              "pysnmp >= 4",
              "nose",
          ],
          test_suite="nose.collector"
          )
