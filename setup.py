from distutils.command.build import build
from setuptools import setup
from setuptools.command.install import install
import snimpy

try:
    import multiprocessing
    import pysnmp
except ImportError:
    pass


def get_ext_modules():
    import snimpy.mib
    return [snimpy.mib.ffi.verifier.get_extension()]


class CFFIBuild(build):
    def finalize_options(self):
        self.distribution.ext_modules = get_ext_modules()
        build.finalize_options(self)


class CFFIInstall(install):
    def finalize_options(self):
        self.distribution.ext_modules = get_ext_modules()
        install.finalize_options(self)

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
          install_requires=["cffi", "pysnmp >= 4"],
          setup_requires=["cffi"],
          tests_require=["cffi", "pysnmp >= 4", "nose", "mock"],
          test_suite="nose.collector"
          )
