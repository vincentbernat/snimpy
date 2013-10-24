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
import functools


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


import cffi.vengine_cpy
import cffi.vengine_gen

patch(cffi.vengine_cpy.VCPythonEngine)
patch(cffi.vengine_gen.VGenericEngine)
