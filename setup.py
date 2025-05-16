import os
from setuptools import setup, find_packages

rtd = os.environ.get("READTHEDOCS", None) == "True"


if __name__ == "__main__":
    readme = open("README.rst").read()
    history = open("HISTORY.rst").read().replace(".. :changelog:", "")

    setup(
        name="snimpy",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: ISC License (ISCL)",
            "Operating System :: POSIX",
            "Programming Language :: Python :: 3",
            "Topic :: System :: Networking",
            "Topic :: Utilities",
            "Topic :: System :: Monitoring",
        ],
        url="https://github.com/vincentbernat/snimpy",
        description="interactive SNMP tool",
        long_description=readme + "\n\n" + history,
        long_description_content_type="text/x-rst",
        author="Vincent Bernat",
        author_email="bernat@luffy.cx",
        packages=["snimpy"],
        entry_points={
            "console_scripts": [
                "snimpy = snimpy.main:interact",
            ],
        },
        data_files=[("share/man/man1", ["man/snimpy.1"])],
        zip_safe=False,
        cffi_modules=(not rtd and ["snimpy/smi_build.py:ffi"] or []),
        install_requires=[
            "cffi >= 1.0.0",
            "pysnmp >= 4, < 6",
            "pyasn1 <= 0.6.0",
            'pyasyncore; python_version >= "3.12"',
            "setuptools",
        ],
        setup_requires=["cffi >= 1.0.0", "setuptools_scm"],
        use_scm_version=True,
    )
