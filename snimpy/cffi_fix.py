# Copyright 2013 Donald Stufft and individual contributors
# Copyright 2013 Vincent Bernat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The original version is available here:
#   https://github.com/pyca/pynacl/blob/master/src/nacl/_cffi_fix.py
#
# This modified version will just call original implementation but
# with additional suffixes if needed.

import imp
import sys
import binascii
import functools
import threading


def get_so_suffixes():
    suffixes = [suffix
                for suffix, _, t in imp.get_suffixes()
                if t == imp.C_EXTENSION]

    if not suffixes:
        # bah, no C_EXTENSION available.  Occurs on pypy without cpyext
        if sys.platform == 'win32':
            suffixes = [".pyd"]
        else:
            suffixes = [".so"]

    return suffixes


def patch(cls):
    """Patch `find_module` method to try more suffixes."""
    original_find_module = cls.find_module

    @functools.wraps(original_find_module)
    def find_more_modules(self, module_name, path, so_suffix):
        suffixes = get_so_suffixes()
        if so_suffix in suffixes:
            suffixes.remove(so_suffix)
        suffixes.insert(0, so_suffix)
        for suffix in suffixes:
            filename = original_find_module(self, module_name, path, suffix)
            if filename is not None:
                return filename
        return None

    cls.find_module = find_more_modules


def create_modulename(prefix, cdef_sources, source, sys_version=sys.version):
    """
    This is the same as CFFI's create modulename except we don't include the
    CFFI version.
    """
    key = '\x00'.join([sys_version[:3], source, cdef_sources])
    key = key.encode('utf-8')
    k1 = hex(binascii.crc32(key[0::2]) & 0xffffffff)
    k1 = k1.lstrip('0x').rstrip('L')
    k2 = hex(binascii.crc32(key[1::2]) & 0xffffffff)
    k2 = k2.lstrip('0').rstrip('L')
    return '_{2}_cffi_{0}{1}'.format(k1, k2, prefix)


class LazyLibrary(object):
    def __init__(self, ffi):
        self._ffi = ffi
        self._lib = None
        self._lock = threading.Lock()

    def __getattr__(self, name):
        if self._lib is None:
            with self._lock:
                if self._lib is None:
                    self._lib = self._ffi.verifier.load_library()

        return getattr(self._lib, name)

import cffi.vengine_cpy
import cffi.vengine_gen

patch(cffi.vengine_cpy.VCPythonEngine)
patch(cffi.vengine_gen.VGenericEngine)
