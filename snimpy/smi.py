#
# snimpy -- Interactive SNMP tool
#
# Copyright (C) 2015 Vincent Bernat <bernat@luffy.cx>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

"""This module just exports libsmi through CFFI_.

.. _CFFI: http://cffi.readthedocs.org/
"""

import sys
import binascii
import threading
from cffi import FFI
from cffi.verifier import Verifier

_CDEF = """

typedef char *SmiIdentifier;
typedef unsigned long SmiUnsigned32;
typedef long SmiInteger32;
typedef unsigned long long SmiUnsigned64;
typedef long long SmiInteger64;
typedef unsigned int SmiSubid;
typedef float SmiFloat32;
typedef double SmiFloat64;
typedef long double SmiFloat128;

typedef enum SmiBasetype {
    SMI_BASETYPE_INTEGER32,
    SMI_BASETYPE_OCTETSTRING,
    SMI_BASETYPE_OBJECTIDENTIFIER,
    SMI_BASETYPE_UNSIGNED32,
    SMI_BASETYPE_INTEGER64,
    SMI_BASETYPE_UNSIGNED64,
    SMI_BASETYPE_ENUM,
    SMI_BASETYPE_BITS,
    ...
} SmiBasetype;
typedef struct SmiType {
    SmiIdentifier       name;
    SmiBasetype         basetype;
    char                *format;
    ...;
} SmiType;

typedef enum SmiIndexkind {
    SMI_INDEX_INDEX,
    SMI_INDEX_AUGMENT,
    ...
} SmiIndexkind;

typedef unsigned int SmiNodekind;
#define SMI_NODEKIND_NODE         ...
#define SMI_NODEKIND_SCALAR       ...
#define SMI_NODEKIND_TABLE        ...
#define SMI_NODEKIND_ROW          ...
#define SMI_NODEKIND_COLUMN       ...

typedef struct SmiNode {
    SmiIdentifier       name;
    unsigned int        oidlen;
    SmiSubid            *oid;
    char                *format;
    SmiIndexkind        indexkind;
    int                 implied;
    SmiNodekind         nodekind;
    ...;
} SmiNode;

typedef struct SmiValue {
    SmiBasetype             basetype;
    union {
        SmiUnsigned64       unsigned64;
        SmiInteger64        integer64;
        SmiUnsigned32       unsigned32;
        SmiInteger32        integer32;
        SmiFloat32          float32;
        SmiFloat64          float64;
        SmiFloat128         float128;
        SmiSubid            *oid;
        char                *ptr;
    } value;
    ...;
} SmiValue;

typedef struct SmiRange {
    SmiValue            minValue;
    SmiValue            maxValue;
} SmiRange;

typedef struct SmiModule {
    SmiIdentifier       name;
    int                 conformance;
    ...;
} SmiModule;

typedef struct SmiElement {
    ...;
} SmiElement;

typedef struct SmiNamedNumber {
    SmiIdentifier       name;
    SmiValue            value;
} SmiNamedNumber;

typedef void (SmiErrorHandler) (char *path, int line,
  int severity, char *msg, char *tag);

int          smiInit(const char *);
void         smiExit(void);
void         smiSetErrorLevel(int);
void         smiSetErrorHandler(SmiErrorHandler *);
void         smiSetFlags(int);
char        *smiLoadModule(const char *);
SmiModule   *smiGetFirstModule();
SmiModule   *smiGetNextModule(SmiModule *);
SmiModule   *smiGetModule(const char *);
SmiModule   *smiGetNodeModule(SmiNode *);
SmiType     *smiGetNodeType(SmiNode *);
SmiType     *smiGetParentType(SmiType *);
SmiType     *smiGetType(SmiModule *, char *);
SmiModule   *smiGetTypeModule(SmiType *);
char        *smiRenderNode(SmiNode *, int);
SmiElement  *smiGetFirstElement(SmiNode *);
SmiElement  *smiGetNextElement(SmiElement *);
SmiNode     *smiGetElementNode(SmiElement *);
SmiRange    *smiGetFirstRange(SmiType *);
SmiRange    *smiGetNextRange(SmiRange *);
SmiNode     *smiGetNode(SmiModule *, const char *);
SmiNode     *smiGetNodeByOID(unsigned int oidlen, SmiSubid *);
SmiNode     *smiGetFirstNode(SmiModule *, SmiNodekind);
SmiNode     *smiGetNextNode(SmiNode *, SmiNodekind);
SmiNode     *smiGetParentNode(SmiNode *);
SmiNode     *smiGetRelatedNode(SmiNode *);
SmiNode     *smiGetFirstChildNode(SmiNode *);
SmiNode     *smiGetNextChildNode(SmiNode *);
SmiNamedNumber *smiGetFirstNamedNumber(SmiType *);
SmiNamedNumber *smiGetNextNamedNumber(SmiNamedNumber *);

#define SMI_FLAG_ERRORS ...
#define SMI_FLAG_RECURSIVE ...
#define SMI_RENDER_ALL ...
"""

_SOURCE = """
#include <smi.h>
"""


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

    @property
    def lib(self):
        if self._lib is None:
            self._lib = self._ffi.verifier.load_library()
        return self._lib

    def __getattr__(self, name):
        return getattr(self.lib, name)

ffi = FFI()
ffi.cdef(_CDEF)
ffi.verifier = Verifier(
    ffi,
    _SOURCE,
    libraries=["smi"],
    modulename=create_modulename("Mib", _CDEF, _SOURCE))
smi = LazyLibrary(ffi)

__all__ = [ffi]
