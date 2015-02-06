from distutils.command.build import build
from setuptools import setup
from setuptools.command.test import test
from setuptools.command.install import install
import snimpy


class SnimpyTestCommand(test):
    def run_tests(self, *args, **kwds):
        # Ensure we keep a reference to multiprocessing and pysnmp to
        # avoid errors at the end of the test
        import multiprocessing
        import pysnmp
        SnimpyTestCommand.multiprocessing = multiprocessing
        SnimpyTestCommand.pysnmp = pysnmp
        return test.run_tests(self, *args, **kwds)


def get_cffi_modules():
    import snimpy.smi
    return [snimpy.smi.ffi.verifier.get_extension()]


class SnimpyBuildCommand(build):
    def finalize_options(self):
        self.distribution.ext_modules = get_cffi_modules()
        return build.finalize_options(self)


class SnimpyInstallCommand(install):
    def finalize_options(self):
        self.distribution.ext_modules = get_cffi_modules()
        return install.finalize_options(self)

if __name__ == "__main__":
    readme = open('README.rst').read()
    history = open('HISTORY.rst').read().replace('.. :changelog:', '')

    setup(name="snimpy",
          version=snimpy.__version__,
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Intended Audience :: System Administrators',
              'License :: OSI Approved :: ISC License (ISCL)',
              'Operating System :: POSIX',
              'Programming Language :: Python :: 2',
              'Programming Language :: Python :: 3',
              'Topic :: System :: Networking',
              'Topic :: Utilities',
              'Topic :: System :: Monitoring'
          ],
          url='https://github.com/vincentbernat/snimpy',
          description=snimpy.__doc__,
          long_description=readme + '\n\n' + history,
          author=snimpy.__author__,
          author_email=snimpy.__email__,
          packages=["snimpy"],
          entry_points={
              'console_scripts': [
                  'snimpy = snimpy.main:interact',
              ],
          },
          data_files=[('share/man/man1', ['man/snimpy.1'])],
          zip_safe=False,
          install_requires=["cffi>=0.8", "pysnmp >= 4"],
          setup_requires=["cffi>=0.8"],
          tests_require=["cffi>=0.8", "pysnmp >= 4", "nose", "mock"],
          test_suite="nose.collector",
          cmdclass={
              "test": SnimpyTestCommand,
              "build": SnimpyBuildCommand,
              "install": SnimpyInstallCommand,
          },
          )
