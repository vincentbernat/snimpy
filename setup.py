import os
from setuptools import setup

rtd = os.environ.get("READTHEDOCS", None) == "True"

setup(
    cffi_modules=(not rtd and ["snimpy/smi_build.py:ffi"] or []),
)
