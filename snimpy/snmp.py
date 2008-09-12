##############################################################################
##                                                                          ##
## snimpy -- Interactive SNMP tool                                          ##
##                                                                          ##
## Copyright (C) Vincent Bernat <bernat@luffy.cx>                           ##
##                                                                          ##
## Permission to use, copy, modify, and distribute this software for any    ##
## purpose with or without fee is hereby granted, provided that the above   ##
## copyright notice and this permission notice appear in all copies.        ##
##                                                                          ##
## THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES ##
## WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         ##
## MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  ##
## ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   ##
## WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    ##
## ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  ##
## OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           ##
##                                                                          ##
##############################################################################

"""Send SNMP packets

This module is aimed at sending SNMP packets (and get the answers). It
uses net-snmp library. It is not a complete implementation but
something suitable for small scripts and interactive use.
"""

import socket

from ctypes import *
from ctypes.util import find_library

import mib

# We need libc
libc = CDLL(find_library("c"))

# Get lib Net-SNMP
libname = find_library("netsnmp")
if not libname:
    raise ImportError("unable to find Net-SNMP library")
try:
    lib = CDLL(libname)
except OSError:
    raise ImportError("unable to load %s" % libname)
lib.netsnmp_get_version.argtypes = []
lib.netsnmp_get_version.restype = c_char_p
minversion = [5, 1, 0]
curversion = [int(i) for i in lib.netsnmp_get_version().split(".")]
if curversion < minversion:
    raise ImportError("needs at least net-snmp %s" % ".".join(minversion))
if curversion > [5,2,0]:
    localname = [('localname', c_char_p)]
    if curversion > [5,3,0]:
        paramName = [('paramName', c_char_p)]

# Prototypes
oid = c_long
SNMP_VERSION_1 = 0
SNMP_VERSION_2c = 1
ASN_CONTEXT = 0x80
ASN_CONSTRUCTOR = 0x20
ASN_APPLICATION = 0x40
ASN_PRIMITIVE = 0x00
ASN_OPAQUE_TAG2 = 0x30
SNMP_MSG_GET = (ASN_CONTEXT | ASN_CONSTRUCTOR | 0x0)
SNMP_MSG_GETNEXT = (ASN_CONTEXT | ASN_CONSTRUCTOR | 0x1)
SNMP_MSG_RESPONSE = (ASN_CONTEXT | ASN_CONSTRUCTOR | 0x2)
SNMP_MSG_SET = (ASN_CONTEXT | ASN_CONSTRUCTOR | 0x3)
SNMP_NOSUCHOBJECT = ASN_CONTEXT | ASN_PRIMITIVE | 0x0
SNMP_NOSUCHINSTANCE = ASN_CONTEXT | ASN_PRIMITIVE | 0x1
SNMP_ENDOFMIBVIEW = ASN_CONTEXT | ASN_PRIMITIVE | 0x2
SNMP_ERR_NOSUCHNAME = 2
USM_AUTH_KU_LEN = 32
USM_PRIV_KU_LEN = 32
class NETSNMP_SESSION(Structure): pass
class NETSNMP_PDU(Structure): pass
class NETSNMP_VARIABLE_LIST(Structure): pass
AUTHENTICATOR = CFUNCTYPE(c_char_p, POINTER(c_int), c_char_p, c_int)
NETSNMP_CALLBACK = CFUNCTYPE(c_int,
                             c_int, POINTER(NETSNMP_SESSION),
                             c_int, POINTER(NETSNMP_PDU),
                             c_void_p)
fields  = [ ('version', c_long),
            ('retries', c_int),
            ('timeout', c_long),
            ('flags', c_ulong),
            ('subsession', POINTER(NETSNMP_SESSION)),
            ('next', POINTER(NETSNMP_SESSION)),
            ('peername', c_char_p),
            ('remote_port', c_ushort), ]
fields += localname
fields += [ ('local_port', c_ushort),
            ('authenticator', AUTHENTICATOR),
            ('callback', NETSNMP_CALLBACK),
            ('callback_magic', c_void_p),
            ('s_errno', c_int),
            ('s_snmp_errno', c_int),
            ('sessid', c_long),
            ('community', c_char_p),
            ('community_len', c_size_t),
            ('rcvMsgMaxSize', c_size_t),
            ('sndMsgMaxSize', c_size_t),
            
            ('isAuthoritative', c_byte),
            ('contextEngineID', c_char_p),
            ('contextEngineIDLen', c_size_t),
            ('engineBoots', c_uint),
            ('engineTime', c_uint),
            ('contextName', c_char_p),
            ('contextNameLen', c_size_t),
            ('securityEngineID', c_char_p),
            ('securityEngineIDLen', c_size_t),
            ('securityName', c_char_p),
            ('securityNameLen', c_size_t),
            
            ('securityAuthProto', POINTER(oid)),
            ('securityAuthProtoLen', c_size_t),
            ('securityAuthKey', c_byte * USM_AUTH_KU_LEN),
            ('securityAuthKeyLen', c_size_t),
            ('securityAuthLocalKey', c_char_p),
            ('securityAuthLocalKeyLen', c_size_t),
            
            ('securityPrivProto', POINTER(oid)),
            ('securityPrivProtoLen', c_size_t),
            ('securityPrivKey', c_char * USM_PRIV_KU_LEN),
            ('securityPrivKeyLen', c_size_t),
            ('securityPrivLocalKey', c_char_p),
            ('securityPrivLocalKeyLen', c_size_t), ]
fields += paramName
fields += [ ('securityModel', c_int),
            ('securityLevel', c_int),
            
            ('securityInfo', c_void_p),
            
            ('myvoid', c_void_p) ]
NETSNMP_SESSION._fields_ = fields

class COUNTER64(Structure):
    _fields_ = [
        ('high', c_ulong),
        ('low', c_ulong),
        ]

class NETSNMP_VARDATA(Union):
    _fields_ = [
        ('integer', POINTER(c_long)),
        ('uinteger', POINTER(c_ulong)),
        ('string', c_char_p),
        ('objid', POINTER(oid)),
        ('bitstring', POINTER(c_ubyte)),
        ('counter64', POINTER(COUNTER64)),
        ('floatVal', POINTER(c_float)),
        ('doubleVal', POINTER(c_double)),
        ]    
MAX_OID_LEN = 128
NETSNMP_VARIABLE_LIST._fields_ = [
    ('next_variable', POINTER(NETSNMP_VARIABLE_LIST)),
    ('name', POINTER(oid)),
    ('name_length', c_size_t),
    ('type', c_char),
    ('val', NETSNMP_VARDATA),
    ('val_len', c_size_t),
    ('name_loc', oid * MAX_OID_LEN),
    ('buf', c_char * 40),
    ('data', c_void_p),
    ('dataFreeHook', CFUNCTYPE(c_void_p)),
    ('index', c_int),
    ]

NETSNMP_PDU._fields_ = [
    ('version', c_long ),
    ('command', c_int ),
    ('reqid', c_long ),
    ('msgid', c_long ),
    ('transid', c_long ),
    ('sessid', c_long ),
    ('errstat', c_long ),
    ('errindex', c_long ),
    ('time', c_ulong ),
    ('flags', c_ulong ),
    ('securityModel', c_int ),
    ('securityLevel', c_int ),
    ('msgParseModel', c_int ),
    ('transport_data', c_void_p),
    ('transport_data_length', c_int ),
    ('tDomain', POINTER(oid)),
    ('tDomainLen', c_size_t ),
    ('variables', POINTER(NETSNMP_VARIABLE_LIST)),
    ('community', c_char_p),
    ('community_len', c_size_t ),
    ('enterprise', POINTER(oid)),
    ('enterprise_length', c_size_t ),
    ('trap_type', c_long ),
    ('specific_type', c_long ),
    ('agent_addr', c_byte * 4),
    ('contextEngineID', c_char_p ),
    ('contextEngineIDLen', c_size_t ),
    ('contextName', c_char_p),
    ('contextNameLen', c_size_t ),
    ('securityEngineID', c_char_p),
    ('securityEngineIDLen', c_size_t ),
    ('securityName', c_char_p),
    ('securityNameLen', c_size_t ),
    ('priority', c_int ),
    ('range_subid', c_int ),
    ('securityStateRef', c_void_p),
    ]

lib.snmp_sess_init.argtypes = [POINTER(NETSNMP_SESSION)]
lib.snmp_sess_init.restype = None
lib.snmp_open.argtypes = [POINTER(NETSNMP_SESSION)]
lib.snmp_open.restype = POINTER(NETSNMP_SESSION)
lib.snmp_close.argtypes = [POINTER(NETSNMP_SESSION)]
lib.snmp_close.restype = c_int
lib.snmp_error.argtypes = [POINTER(NETSNMP_SESSION), POINTER(c_int),
                           POINTER(c_int), POINTER(c_char_p)]
lib.snmp_error.restype = None
lib.snmp_errstring.argtypes = [c_int]
lib.snmp_errstring.restype = c_char_p
lib.snmp_pdu_create.argtypes = [c_int]
lib.snmp_pdu_create.restype = POINTER(NETSNMP_PDU)
lib.snmp_add_null_var.argtypes = [POINTER(NETSNMP_PDU), POINTER(oid), c_size_t]
lib.snmp_add_null_var.restype = POINTER(NETSNMP_VARIABLE_LIST)
lib.snmp_add_var.argtypes = [POINTER(NETSNMP_PDU), POINTER(oid), c_size_t, c_char, c_char_p]
lib.snmp_add_var.restype = c_int
lib.snmp_synch_response.argtypes = [POINTER(NETSNMP_SESSION), POINTER(NETSNMP_PDU),
                                    POINTER(POINTER(NETSNMP_PDU))]
lib.snmp_synch_response.restype = c_int
lib.snmp_free_pdu.argtypes = [POINTER(NETSNMP_PDU)]
lib.snmp_free_pdu.restype = None

# Exceptions
class SNMPException(Exception): pass
class SNMPNoSuchObject(SNMPException): pass
class SNMPNoSuchInstance(SNMPException): pass
class SNMPEndOfMIB(SNMPException): pass
class SNMPUnsupportedType(SNMPException): pass
class SNMPGenericError(SNMPException):
    
    def __init__(self, sess):
        self.sess = sess

    def __str__(self):
        liberr = c_int()
        syserr = c_int()
        error = c_char_p()
        lib.snmp_error(self.sess, byref(liberr),
                       byref(syserr), byref(error))
        if not error:
            raise SNMPException("unable to get a meaningful error")
        e = error.value[:]
        libc.free(error)
        return e

class SNMPPacketError(SNMPException):

    def __init__(self, response):
        self.response = response

    def __str__(self):
        return "%s (%d)" % (lib.snmp_errstring(self.response),
                            self.response)

decode_integer32 = lambda pdu: pdu.val.integer.contents.value
decode_unsigned32 = lambda pdu: pdu.val.uinteger.contents.value
def decode_unsigned64(pdu):
    result = pdu.val.counter64.contents
    return (result.high << 32L) + result.low
decode_integer64 = decode_unsigned64
def decode_bits(pdu):
    s = string_at(pdu.val.bitstring, pdu.val_len)
    result = []
    for i in range(0, len(s)):
        if ord(s[i]) != 0:
            for j in range(0, 8):
                if ord(s[i]) & (1<<j):
                    result.append(i*8 + (7-j))
    result.sort()
    return result
decode_float32 = lambda pdu: pdu.val.floatVal.contents.value
decode_float64 = lambda pdu: pdu.val.doubleVal.contents.value

# We use pdu.val.bitstring since we are not sure this is a real string
decode_octetstring = lambda pdu: string_at(pdu.val.bitstring, pdu.val_len)
decode_objectidentifier = lambda pdu: mib.OID(
    tuple([pdu.val.objid[i] for i in range(0, pdu.val_len / sizeof(c_ulong))]))
def decode_ip(pdu):
    s = string_at(pdu.val.bitstring, pdu.val_len)
    return socket.inet_ntoa(s[:4])

asn = { 0x02: { "name": "INTEGER", "basetype": "integer32" },
        0x03: { "name": "BITS", "basetype": "bits" },
        0x04: { "name": "STRING", "basetype": "octetstring" },
        0x06: { "name": "OID", "basetype": "objectidentifier" },
        ASN_APPLICATION | 0: { "name": "IP", "basetype": "octetstring", "typename": "IpAddress",
                               "decoder": decode_ip },
        ASN_APPLICATION | 1: { "name": "COUNTER", "basetype": "unsigned32" },
        ASN_APPLICATION | 2: { "name": "GAUGE", "basetype": "unsigned32" },
        ASN_APPLICATION | 3: { "name": "TIMETICKS", "basetype": "unsigned32", "typename": "TimeTicks" },
        ASN_APPLICATION | 4: { "name": "OPAQUE", "basetype": "octetstring" },
        ASN_APPLICATION | 6: { "name": "COUNTER64", "basetype": "unsigned64" },
        ASN_APPLICATION | 7: { "name": "UINTEGER", "basetype": "unsigned32" },
        ASN_APPLICATION | 8: { "name": "FLOAT", "basetype": "float32" },
        ASN_APPLICATION | 9: { "name": "DOUBLE", "basetype": "float64" },
        ASN_APPLICATION | 10: { "name": "INTEGER64", "basetype": "integer64" },
        ASN_APPLICATION | 11: { "name": "UNSIGNED64", "basetype": "unsigned64" },
        ASN_OPAQUE_TAG2 + (ASN_APPLICATION | 6): { "name": "OPAQUE COUNTER64", "basetype": "octetstring" },
        ASN_OPAQUE_TAG2 + (ASN_APPLICATION | 8): { "name": "OPAQUE FLOAT", "basetype": "octetstring" },
        ASN_OPAQUE_TAG2 + (ASN_APPLICATION | 9): { "name": "OPAQUE DOUBLE", "basetype": "octetstring" },
        ASN_OPAQUE_TAG2 + (ASN_APPLICATION | 10): { "name": "OPAQUE INTEGER64", "basetype": "octetsring" },
        ASN_OPAQUE_TAG2 + (ASN_APPLICATION | 11): { "name": "OPAQUE UNSIGNED64", "basetype": "octetsring" }
        }

def decode(pdu):
    """Decode the given PDU as a list of OID."""
    result = []
    var = pdu.variables
    while var:
        var = var.contents
        o = mib.OID([var.name[i] for i in range(0, var.name_length)])
        if ord(var.type) == SNMP_NOSUCHOBJECT:
            raise SNMPNoSuchObject("No Such Object available on this agent at OID %r" % o)
        if ord(var.type) == SNMP_NOSUCHINSTANCE:
            raise SNMPNoSuchInstance("No Such Instance currently exists at OID %r" % o)
        if ord(var.type) == SNMP_ENDOFMIBVIEW:
            raise SNMPEndOfMIB("No more variable left in MIB: OID %r is out of range" % o)
        if ord(var.type) not in asn:
            raise SNMPUnsupportedType("unsupported type received (%d)" % ord(var.type))
        handle = asn[ord(var.type)]
        if o.type is not None:
            if mib.SmiBaseType.get(o.type.basetype, None) != handle["basetype"]:
                if handle["name"] == "INTEGER" and \
                        mib.SmiBaseType.get(o.type.basetype, None) == "enum":
                    pass
                elif handle["name"] == "STRING" and \
                        mib.SmiBaseType.get(o.type.basetype, None) == "bits":
                    handle = asn[0x03]
                else:
                    raise SNMPException("received %s while waiting for %s at %r" % (handle["name"],
                                                                                    mib.SmiBaseType.get(
                                o.type.basetype, None), o))
        result.append(o << handle.get("decoder",
                                      globals()["decode_%s" % handle["basetype"]])(var))
        var = var.next_variable
    return result

class Session:

    # Default values
    host = "localhost"
    community = "public"
    version = SNMP_VERSION_2c
    port = 161

    def __init__(self, host=None, community=None,
                 version=None, port=None, **kw):
        """Create a new session.

        @param host: host to connect to
        @param community: community to use
        @param version: SNMP version to use
        @param port: port to use
        
        Other named args are passed to netsnmp session structure. This
        should allow to do many things but is widely untested.
        """
        if host is None:
            host = Session.host
        if community is None:
            community = Session.community
        if version is None:
            version = Session.version
        if port is None:
            port = Session.port
        sess = NETSNMP_SESSION()
        lib.snmp_sess_init(byref(sess))
        sess.community = community
        sess.community_len = len(community)
        sess.version = version
        sess.peername = host
        sess.remote_port = port
        for k in kw:
            setattr(sess, k, kw[k])
        newsess = lib.snmp_open(byref(sess))
        if not newsess:
            raise SNMPGenericError(sess)
        self.sess = newsess

    def op(self, op, goid):
        """Invoke SNMP operation.

        This method can be used for get, set and getnext.

        @param op: operation to invoke like C{SNMP_MSG_GET}
        @param goid: either an OID or a list of OID
        @return: a binded OID or a list of binded OID
        """
        if type(goid) not in [tuple, list]:
            goid = [ goid ]
            notalist = True
        else:
            notalist = False
        req = lib.snmp_pdu_create(op)
        for o in goid:
            if isinstance(o, mib.Node):
                o = o()
            if not isinstance(o, mib.OID):
                raise ValueError("need %r instance and got %r" % (mib.OID, o))
            if op != SNMP_MSG_SET:
                lib.snmp_add_null_var(req, (oid*len(o))(*o.oid), len(o))
            else:
                if o.type is None:
                    # Need to guess the type
                    t = None
                    try:
                        socket.inet_ntoa(socket.inet_aton(value))
                    except ValueError:
                        pass
                    else:
                        t = 'a'
                        value = str(value)
                    if t is None:
                        if type(o.value) is str:
                            t = 'x'
                            value = " ".join([ "%02x" % ord(a) for a in o.value ])
                        elif type(o.value) is int:
                            t = 'i'
                            value = str(o.value)
                        elif isinstance(o.value, mib.OID):
                            t = 'o'
                            value = ".".join(o.value.oid)
                        elif type(o.value) in [list, tuple]:
                            t = 'b'
                            value = " ".join(o.value)
                        else:
                            raise SNMPException("unable to handle %r" % o)
                else:
                    # We use o.type to set the type
                    if o.type.name == "IpAddress":
                        t = 'a'
                        value = str(o.value)
                    if mib.SmiBaseType[o.type.basetype] in ["integer32",
                                                            "integer64",
                                                            "enum"]:
                        t = 'i'
                        value = str(o.value)
                    elif mib.SmiBaseType[o.type.basetype] == "octetstring":
                        t = 'x'
                        value = " ".join([ "%02x" % ord(a) for a in o.value ])
                    elif mib.SmiBaseType[o.type.basetype] == "objectidentifier":
                        t = 'o'
                        value = ".".join(o.value.oid)
                    elif mib.SmiBaseType[o.type.basetype].startswith("unsigned"):
                        t = 'u'
                        value = str(o.value)
                    elif mib.SmiBaseType[o.type.basetype] == "bits":
                        t = 'b'
                        value = " ".join(o.value)
                    else:
                        raise SNMPException("unable to handle %r for set operation" % o)
                if lib.snmp_add_var(req, (oid*len(o))(*o.oid), len(o), t, value) != 0:
                    raise SNMPException("unable to add var %r" % o)
        response = POINTER(NETSNMP_PDU)()
        try:
            if lib.snmp_synch_response(self.sess, req, byref(response)) != 0:
                raise SNMPGenericError(self.sess)
            if response.contents.errstat != 0:
                if response.contents.errstat == SNMP_ERR_NOSUCHNAME:
                    raise SNMPNoSuchObject(
                        "No Such Object available on this agent at OID %r" % goid)
                raise SNMPPacketError(response.contents.errstat)
            result = decode(response.contents)
        finally:
            lib.snmp_free_pdu(response)
        if notalist:
            return result[0]
        return result

    def walk(self, goid, loop=False):
        """Walk from a given oid.

        @param goid: an OID to walk.
        @param loop: allow loops
        @return: iterator on the results
        """
        results = 0
        if isinstance(goid, mib.Node):
            goid = goid()
        if not isinstance(goid, mib.OID):
            raise ValueError("need %r instance and got %r" % (mib.OID, o))
        o = goid
        try:
            while True:
                no = self.getnext(o)
                if not loop and no.oid <= o.oid:
                    raise SNMPException("we are looping at %r" % no)
                o = no
                if o not in goid:
                    if not results:
                        yield self.get(goid)
                        raise StopIteration
                    raise StopIteration
                results += 1
                yield o
        except (SNMPNoSuchObject, SNMPNoSuchInstance, SNMPEndOfMIB):
            if not results:
                # We try to get the original OID
                yield self.get(goid)
                raise StopIteration


    get = lambda self, goid: self.op(SNMP_MSG_GET, goid)
    getnext = lambda self, goid: self.op(SNMP_MSG_GETNEXT, goid)
    set = lambda self, goid: self.op(SNMP_MSG_SET, goid)

    def __del__(self):
        if not self.sess: return
        lib.snmp_close(self.sess)

# Some helper functions
def get(*args, **kwargs):
    return Session().get(*args, **kwargs)
def getnext(*args, **kwargs):
    return Session().getnext(*args, **kwargs)
def walk(*args, **kwargs):
    return Session().walk(*args, **kwargs)
def set(*args, **kwargs):
    return Session().set(*args, **kwargs)
