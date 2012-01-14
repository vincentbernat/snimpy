/******************************************************************************
 **                                                                          **
 ** snimpy -- Interactive SNMP tool                                          **
 **                                                                          **
 ** Copyright (C) Vincent Bernat <bernat@luffy.cx>                           **
 **                                                                          **
 ** Permission to use, copy, modify, and distribute this software for any    **
 ** purpose with or without fee is hereby granted, provided that the above   **
 ** copyright notice and this permission notice appear in all copies.        **
 **                                                                          **
 ** THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES **
 ** WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         **
 ** MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  **
 ** ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   **
 ** WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    **
 ** ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  **
 ** OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           **
 **                                                                          **
 ******************************************************************************/

/* Simple interface to libnetsnmp */

#include <Python.h>
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>


/* Exceptions */
struct ErrorException {
	int error;
	char *name;
	PyObject *exception;
};
static PyObject *SnmpException;
static PyObject *SnmpNoSuchObject;
static PyObject *SnmpNoSuchInstance;
static PyObject *SnmpEndOfMibView;
static struct ErrorException SnmpErrorToException[] = {
	{ SNMP_ERR_TOOBIG, "SNMPTooBig" },
	{ SNMP_ERR_NOSUCHNAME, "SNMPNoSuchName" },
	{ SNMP_ERR_BADVALUE, "SNMPBadValue" },
	{ SNMP_ERR_READONLY,  "SNMPReadonly" },
	{ SNMP_ERR_GENERR, "SNMPGenerr" },
	{ SNMP_ERR_NOACCESS, "SNMPNoAccess" },
	{ SNMP_ERR_WRONGTYPE, "SNMPWrongType" },
	{ SNMP_ERR_WRONGLENGTH, "SNMPWrongLength" },
	{ SNMP_ERR_WRONGENCODING, "SNMPWrongEncoding" },
	{ SNMP_ERR_WRONGVALUE, "SNMPWrongValue" },
	{ SNMP_ERR_NOCREATION, "SNMPNoCreation" },
	{ SNMP_ERR_INCONSISTENTVALUE, "SNMPInconsistentValue" },
	{ SNMP_ERR_RESOURCEUNAVAILABLE, "SNMPResourceUnavailable" },
	{ SNMP_ERR_COMMITFAILED, "SNMPCommitFailed" },
	{ SNMP_ERR_UNDOFAILED, "SNMPUndoFailed" },
	{ SNMP_ERR_AUTHORIZATIONERROR, "SNMPAuthorizationError" },
	{ SNMP_ERR_NOTWRITABLE, "SNMPNotWritable" },
	{ SNMP_ERR_INCONSISTENTNAME, "SNMPInconsistentName" },
	{ -1, NULL },
};

/* Types */
static PyObject *TypesModule;

typedef struct {
	PyObject_HEAD
	void *ss;
} SnmpObject;

static void
Snmp_dealloc(SnmpObject* self)
{
	if (self->ss)
		snmp_sess_close(self->ss);
	self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
Snmp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	SnmpObject *self;

	self = (SnmpObject *)type->tp_alloc(type, 0);
	if (self != NULL)
		self->ss = NULL;
	return (PyObject *)self;
}

static void
Snmp_raise_error(void *session, int open)
{
	int liberr, snmperr;
	char *err;
	if (!open)
		snmp_sess_error(session, &liberr, &snmperr, &err);
	else
		snmp_error((struct snmp_session *)session, &liberr, &snmperr, &err);
	PyErr_Format(SnmpException, "%s", err);
	free(err);
}

static int
Snmp_init(SnmpObject *self, PyObject *args, PyObject *kwds)
{
	PyObject *host=NULL, *community=NULL,
		*secname=NULL, *seclevel=NULL,
		*authprotocol=NULL, *authpassword=NULL,
		*privprotocol=NULL, *privpassword=NULL;
	char *chost=NULL;
	int version = 2;
	struct snmp_session session;

	static char *kwlist[] = {"host", "community", "version",
				 "seclevel", "secname",
				 "authprotocol", "authpassword",
				 "privprotocol", "privpassword",
				 NULL};
		
	if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OiOOOOOO", kwlist, 
					 &host, &community, &version,
					 &seclevel, &secname,
					 &authprotocol, &authpassword,
					 &privprotocol, &privpassword))
		return -1; 

	snmp_sess_init(&session);
	if ((chost = PyString_AsString(host)) == NULL)
		return -1;

	/* SNMP version */
	switch (version) {
	case 1:
		session.version = SNMP_VERSION_1;
		break;
	case 2:
		session.version = SNMP_VERSION_2c;
		break;
	case 3:
		session.version = SNMP_VERSION_3;
		break;
	default:
		PyErr_Format(PyExc_ValueError, "invalid SNMP version: %d",
		    version);
		return -1;
	}

	/* Fill out session */
	if (community != NULL && community != Py_None) {
		char *ccommunity = NULL;
		if ((ccommunity = PyString_AsString(community)) == NULL)
			goto initerror;
		session.community_len = PyString_Size(community);
		session.community = (u_char *)strdup(ccommunity);
		if (!session.community) goto initoutofmem;
	}
	if (seclevel != NULL && seclevel != Py_None) {
		int cseclevel;
		cseclevel = PyInt_AsLong(seclevel);
		if (PyErr_Occurred()) goto initerror;
		session.securityLevel = cseclevel;
	}
	if (secname != NULL && secname != Py_None) {
		char *csecname = NULL;
		if ((csecname = PyString_AsString(secname)) == NULL)
			goto initerror;
		session.securityNameLen = PyString_Size(secname);
		session.securityName = strdup(csecname);
		if (!session.securityName) goto initoutofmem;
	}
	if (authprotocol != NULL && authprotocol != Py_None) {
		char *cauthprotocol = NULL;
		if ((cauthprotocol = PyString_AsString(authprotocol)) == NULL)
			goto initerror;
		if (!strcasecmp(cauthprotocol, "MD5")) {
			session.securityAuthProto = usmHMACMD5AuthProtocol;
			session.securityAuthProtoLen = USM_AUTH_PROTO_MD5_LEN;
		} else if (!strcasecmp(cauthprotocol, "SHA")) {
			session.securityAuthProto = usmHMACSHA1AuthProtocol;
			session.securityAuthProtoLen = USM_AUTH_PROTO_SHA_LEN;
		} else {
			PyErr_Format(PyExc_ValueError,
				     "invalid authentication protocol: %s",
				     cauthprotocol);
			goto initerror;
		}
	}
	if (authpassword != NULL && authpassword != Py_None) {
		char *cauthpassword = NULL;
		if ((cauthpassword = PyString_AsString(authpassword)) == NULL)
			goto initerror;
		session.securityAuthKeyLen = USM_AUTH_KU_LEN;
		if (session.securityAuthProto == NULL) {
			PyErr_SetString(PyExc_ValueError,
					"can't set an auth password without an auth protocol");
			goto initerror;
		}
		if (generate_Ku(session.securityAuthProto,
				session.securityAuthProtoLen,
				(u_char *) cauthpassword,
				PyString_Size(authpassword),
				session.securityAuthKey,
				&session.securityAuthKeyLen) != SNMPERR_SUCCESS) {
			PyErr_SetString(PyExc_ValueError,
					"unable to compute the master key from auth password");
			goto initerror;
		}
	}
	if (privprotocol != NULL && privprotocol != Py_None) {
		char *cprivprotocol = NULL;
		if ((cprivprotocol = PyString_AsString(privprotocol)) == NULL)
			goto initerror;
		if (!strcasecmp(cprivprotocol, "DES")) {
			session.securityPrivProto = usmDESPrivProtocol;
			session.securityPrivProtoLen = USM_PRIV_PROTO_DES_LEN;
		} else if (!strcasecmp(cprivprotocol, "AES") ||
			   !strcasecmp(cprivprotocol, "AES128")) {
			session.securityPrivProto = usmAESPrivProtocol;
			session.securityPrivProtoLen = USM_PRIV_PROTO_AES_LEN;
		} else {
			PyErr_Format(PyExc_ValueError,
				     "invalid privacy protocol: %s",
				     cprivprotocol);
			goto initerror;
		}
	}
	if (privpassword != NULL && privpassword != Py_None) {
		char *cprivpassword = NULL;
		if ((cprivpassword = PyString_AsString(privpassword)) == NULL)
			goto initerror;
		session.securityPrivKeyLen = USM_PRIV_KU_LEN;
		if (session.securityPrivProto == NULL ||
		    session.securityAuthProto == NULL) {
			PyErr_SetString(PyExc_ValueError,
					"can't set a privacy password without a auth+privacy protocol");
			goto initerror;
		}
		if (generate_Ku(session.securityAuthProto,
				session.securityAuthProtoLen,
				(u_char *) cprivpassword,
				PyString_Size(privpassword),
				session.securityPrivKey,
				&session.securityPrivKeyLen) != SNMPERR_SUCCESS) {
			PyErr_SetString(PyExc_ValueError,
					"unable to compute the master key from privacy password");
			goto initerror;
		}
	}

	session.peername = strdup(chost);
	if (!session.peername) goto initoutofmem;

	/* Open session */
	if ((self->ss = snmp_sess_open(&session)) == NULL) {
		Snmp_raise_error(&session, 1);
		goto initerror;
	}
	return 0;
 initoutofmem:
	PyErr_NoMemory();
 initerror:
	if (session.community) free(session.community);
	if (session.peername) free(session.peername);
	if (session.securityName) free(session.securityName);
	return -1;
}

static PyObject*
Snmp_repr(SnmpObject *self)
{
	PyObject *peer, *rpeer, *result;
	struct snmp_session *sptr = snmp_sess_session(self->ss);
	if ((peer = PyString_FromString(sptr->peername)) == NULL)
		return NULL;
	if ((rpeer = PyObject_Repr(peer)) == NULL) {
		Py_DECREF(peer);
		return NULL;
	}
	result = PyString_FromFormat("%s(host=%s, version=%d)",
	    self->ob_type->tp_name,
	    PyString_AsString(rpeer),
	    (sptr->version == SNMP_VERSION_1)?1:
				     ((sptr->version == SNMP_VERSION_2c)?2:3));
	Py_DECREF(rpeer);
	Py_DECREF(peer);
	return result;
}

static u_char*
Snmp_convert_object(PyObject *obj, int *type, ssize_t *bufsize)
{
	PyObject *BasicType=NULL, *convertor=NULL, *ptype=NULL, *pvalue=NULL;
	u_char *buffer, *result;

	if ((BasicType = PyObject_GetAttrString(TypesModule, "Type")) == NULL)
		return NULL;
	if (!PyObject_IsInstance(obj, BasicType)) {
		PyErr_SetString(SnmpException, "can only set basictypes");
		goto converterr;
	}
	if ((convertor = PyObject_CallMethod(obj, "pack", NULL)) == NULL)
		goto converterr;
	if ((ptype = PyTuple_GetItem(convertor, 0)) == NULL)
		goto converterr;
	if ((pvalue = PyTuple_GetItem(convertor, 1)) == NULL)
		goto converterr;
	*type = (int)PyInt_AsLong(ptype);
	if (PyErr_Occurred()) goto converterr;
	if (PyString_AsStringAndSize(pvalue, (char**)&buffer, bufsize) == -1)
		goto converterr;
	if ((result = (u_char*)malloc(*bufsize)) == NULL) {
		PyErr_NoMemory();
		goto converterr;
	}
	memcpy(result, buffer, *bufsize);
	Py_XDECREF(BasicType);
	Py_XDECREF(convertor);
	return result;
		
converterr:
	Py_XDECREF(BasicType);
	Py_XDECREF(convertor);
	return NULL;
}

static PyObject*
Snmp_op(SnmpObject *self, PyObject *args, int op)
{
	PyObject *roid, *poid, *resultvalue=NULL, *resultoid=NULL,
	    *result=NULL, *results=NULL, *tmp, *setobject;
	struct snmp_pdu *pdu=NULL, *response=NULL;
	struct variable_list *vars;
	oid anOID[MAX_OID_LEN];
	size_t anOID_len = MAX_OID_LEN;
	int i = 0, j = 0, status, type;
	struct ErrorException *e;
	long long counter64;
	u_char* buffer=NULL;
	ssize_t bufsize;

	if (PyTuple_Size(args) < 1) {
		PyErr_SetString(PyExc_TypeError,
		    "not enough arguments");
		return NULL;
	}
	if ((op == SNMP_MSG_SET) && (PyTuple_Size(args)%2 != 0)) {
		PyErr_SetString(PyExc_TypeError,
		    "need an even number of arguments for SET operation");
		return NULL;
	}
	pdu = snmp_pdu_create(op);
	while (j < PyTuple_Size(args)) {
		if ((roid = PyTuple_GetItem(args, j)) == NULL)
			goto operror;
		if (!PyTuple_Check(roid)) {
			PyErr_Format(PyExc_TypeError,
			    "argument %d should be a tuple of integers",
			    j);
			goto operror;
		}
		anOID_len = PyTuple_Size(roid);
		if (anOID_len > MAX_OID_LEN) {
			PyErr_Format(PyExc_ValueError,
			    "OID #%d is too large: %zd > %d",
			    j, anOID_len, MAX_OID_LEN);
			goto operror;
		}
		for (i = 0; i < anOID_len; i++) {
			if ((poid = PyTuple_GetItem(roid, i)) == NULL)
				goto operror;
			if (PyLong_Check(poid))
				anOID[i] = (oid)PyLong_AsUnsignedLong(poid);
			else if (PyInt_Check(poid))
				anOID[i] = (oid)PyInt_AsLong(poid);
			else {
				PyErr_Format(PyExc_TypeError,
				    "element %d of OID #%d is not an integer",
				    i, j);
				goto operror;
			}
		}
		if (op != SNMP_MSG_SET) {
			snmp_add_null_var(pdu, anOID, anOID_len);
			j++;
		} else {
			if ((setobject = PyTuple_GetItem(args, j+1)) == NULL)
				goto operror;
			if ((buffer = Snmp_convert_object(setobject,
				    &type, &bufsize)) == NULL)
				goto operror;
			snmp_pdu_add_variable(pdu, anOID, anOID_len,
			    type, buffer, bufsize); /* There is a copy of all params */
			j += 2;
		}
	}
	Py_BEGIN_ALLOW_THREADS
	status = snmp_sess_synch_response(self->ss, pdu, &response);
	Py_END_ALLOW_THREADS
	free(buffer);
	pdu = NULL;		/* Don't try to free it from now */
	if (status != STAT_SUCCESS) {
		Snmp_raise_error(self->ss, 0);
		goto operror;
	}
	if (response->errstat != SNMP_ERR_NOERROR) {
		for (e = SnmpErrorToException; e->name; e++) {
			if (e->error == response->errstat) {
				PyErr_SetString(e->exception, snmp_errstring(e->error));
				goto operror;
			}
		}
		PyErr_Format(SnmpException, "unknown error %ld", response->errstat);
		goto operror;
	}
	if ((vars = response->variables) == NULL) {
		PyErr_SetString(SnmpException, "answer is empty?");
		goto operror;
	}

	/* Let's handle the value */
	j = 0;
	if ((results = PyTuple_New(PyTuple_Size(args) /
		    ((op == SNMP_MSG_SET)?2:1))) == NULL)
		goto operror;
	do {
		j++;
		if (j > PyTuple_Size(results)) {
			PyErr_SetString(SnmpException,
			    "Received too many answers");
			goto operror;
		}
		switch (vars->type) {
		case SNMP_NOSUCHOBJECT:
			PyErr_SetString(SnmpNoSuchObject, "No such object was found");
			goto operror;
		case SNMP_NOSUCHINSTANCE:
			PyErr_SetString(SnmpNoSuchInstance, "No such instance exists");
			goto operror;
		case SNMP_ENDOFMIBVIEW:
			PyErr_SetString(SnmpEndOfMibView, "End of MIB was reached");
			goto operror;
		case ASN_INTEGER:
			resultvalue = PyLong_FromLong(*vars->val.integer);
			break;
		case ASN_UINTEGER:
		case ASN_TIMETICKS:
		case ASN_GAUGE:
		case ASN_COUNTER:
			resultvalue = PyLong_FromUnsignedLong((unsigned long)*vars->val.integer);
			break;
		case ASN_OCTET_STR:
			resultvalue = PyString_FromStringAndSize((char*)vars->val.string,
			    vars->val_len);
			break;
		case ASN_BIT_STR:
			resultvalue = PyString_FromStringAndSize((char*)vars->val.bitstring,
			    vars->val_len);
			break;
		case ASN_OBJECT_ID:
			if ((resultvalue = PyTuple_New(vars->val_len/sizeof(oid))) == NULL)
				goto operror;
			for (i = 0; i < vars->val_len/sizeof(oid); i++) {
				if ((tmp = PyLong_FromLong(vars->val.objid[i])) == NULL)
					goto operror;
				PyTuple_SetItem(resultvalue, i, tmp);
			}
			break;
		case ASN_IPADDRESS:
			if (vars->val_len < 4) {
				PyErr_Format(SnmpException,
				    "IP address is too short (%zd < 4)",
				    vars->val_len);
				goto operror;
			}
			resultvalue = PyString_FromFormat("%d.%d.%d.%d",
			    vars->val.string[0],
			    vars->val.string[1],
			    vars->val.string[2],
			    vars->val.string[3]);
			break;
		case ASN_COUNTER64:
#ifdef NETSNMP_WITH_OPAQUE_SPECIAL_TYPES
		case ASN_OPAQUE_U64:
		case ASN_OPAQUE_I64:
		case ASN_OPAQUE_COUNTER64:
#endif                          /* NETSNMP_WITH_OPAQUE_SPECIAL_TYPES */
			counter64 = ((unsigned long long)
			    (vars->val.counter64->high) << 32) +
			    (unsigned long long)(vars->val.counter64->low);
			resultvalue = PyLong_FromUnsignedLongLong(counter64);
			break;
#ifdef NETSNMP_WITH_OPAQUE_SPECIAL_TYPES
		case ASN_OPAQUE_FLOAT:
			resultvalue = PyFloat_FromDouble(*vars->val.floatVal);
			break;
		case ASN_OPAQUE_DOUBLE:
			resultvalue = PyFloat_FromDouble(*vars->val.doubleVal);
			break;
#endif                          /* NETSNMP_WITH_OPAQUE_SPECIAL_TYPES */
		default:
			PyErr_Format(SnmpException, "unknown type returned (%d)",
			    vars->type);
			goto operror;
		}
		if (resultvalue == NULL) goto operror;
		
		/* And now, the OID */
		if ((resultoid = PyTuple_New(vars->name_length)) == NULL)
			goto operror;
		for (i = 0; i < vars->name_length; i++) {
			if ((tmp = PyLong_FromLong(vars->name[i])) == NULL)
				goto operror;
			PyTuple_SetItem(resultoid, i, tmp);
		}
		if ((result = PyTuple_Pack(2, resultoid, resultvalue)) == NULL)
			goto operror;
		Py_CLEAR(resultoid);
		Py_CLEAR(resultvalue);
		if (PyTuple_SetItem(results, j-1, result) != 0)
			goto operror;
		result = NULL;	/* Stolen */
	} while ((vars = vars->next_variable));
	snmp_free_pdu(response);
	return results;
	
operror:
	Py_XDECREF(resultvalue);
	Py_XDECREF(resultoid);
	Py_XDECREF(results);
	Py_XDECREF(result);
	if (pdu)
		snmp_free_pdu(pdu);
	if (response)
		snmp_free_pdu(response);
	return NULL;
}

static PyObject*
Snmp_get(PyObject *self, PyObject *args)
{
	return Snmp_op((SnmpObject*)self, args, SNMP_MSG_GET);
}

static PyObject*
Snmp_getnext(PyObject *self, PyObject *args)
{
	return Snmp_op((SnmpObject*)self, args, SNMP_MSG_GETNEXT);
}

static PyObject*
Snmp_set(PyObject *self, PyObject *args)
{
	return Snmp_op((SnmpObject*)self, args, SNMP_MSG_SET);
}

static PyObject*
Snmp_gettimeout(SnmpObject *self, void *closure)
{
	struct snmp_session *sptr = snmp_sess_session(self->ss);
	return PyInt_FromLong(sptr->timeout);
}

static int
Snmp_settimeout(SnmpObject *self, PyObject *value, void *closure)
{
	long timeout;
	struct snmp_session *sptr = snmp_sess_session(self->ss);

	if (value == NULL) {
		PyErr_SetString(PyExc_TypeError,
				"cannot delete timeout");
		return -1;
	}
	if (!PyLong_Check(value) && !PyInt_Check(value)) {
		PyErr_SetString(PyExc_TypeError,
				"timeout is a positive integer");
		return -1;
	}

	timeout = PyLong_AsLong(value);
	if (PyErr_Occurred()) return -1;
	if (timeout <= 0) {
		PyErr_SetString(PyExc_ValueError,
				"timeout is a positive integer");
		return -1;
	}
	sptr->timeout = timeout;
	return 0;
}

static PyObject*
Snmp_getretries(SnmpObject *self, void *closure)
{
	struct snmp_session *sptr = snmp_sess_session(self->ss);
	return PyInt_FromLong(sptr->retries);
}

static int
Snmp_setretries(SnmpObject *self, PyObject *value, void *closure)
{
	int retries;
	struct snmp_session *sptr = snmp_sess_session(self->ss);

	if (value == NULL) {
		PyErr_SetString(PyExc_TypeError,
				"cannot delete retries");
		return -1;
	}
	if (!PyInt_Check(value)) {
		PyErr_SetString(PyExc_TypeError,
				"retries is a non-negative integer");
		return -1;
	}

	retries = PyInt_AsLong(value);
	if (PyErr_Occurred()) return -1;
	if (retries < 0) {
		PyErr_SetString(PyExc_ValueError,
				"retries is a non-negative integer");
		return -1;
	}
	sptr->retries = retries;
	return 0;
}

static PyMethodDef Snmp_methods[] = {
	{"get", Snmp_get,
	 METH_VARARGS, "Retrieve an OID value using GET"},
	{"getnext", Snmp_getnext,
	 METH_VARARGS, "Retrieve an OID value using GETNEXT"},
	{"set", Snmp_set,
	 METH_VARARGS, "Set an OID value using SET"},
	{NULL}  /* Sentinel */
};

static PyGetSetDef Snmp_getseters[] = {
	{"timeout",
	 (getter)Snmp_gettimeout, (setter)Snmp_settimeout,
	 "timeout", NULL},
	{"retries",
	 (getter)Snmp_getretries, (setter)Snmp_setretries,
	 "retries", NULL},
	{NULL}			/* Sentinel */
};

static PyTypeObject SnmpType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"snmp.Session",		   /*tp_name*/
	sizeof(SnmpObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)Snmp_dealloc,  /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	(reprfunc)Snmp_repr,	   /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,			   /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT |
	Py_TPFLAGS_BASETYPE,	   /*tp_flags*/
	"SNMP session",            /*tp_doc*/
	0,			   /* tp_traverse */
	0,			   /* tp_clear */
	0,			   /* tp_richcompare */
	0,			   /* tp_weaklistoffset */
	0,			   /* tp_iter */
	0,			   /* tp_iternext */
	Snmp_methods,		   /* tp_methods */
	0,			   /* tp_members */
	Snmp_getseters,		   /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)Snmp_init,	   /* tp_init */
	0,                         /* tp_alloc */
	Snmp_new,		   /* tp_new */
};

PyDoc_STRVAR(module_doc,
    "simple interface to libnetsnmp");

PyMODINIT_FUNC
initsnmp(void)
{
	PyObject *m, *exc, *c;
	char *name;
	struct ErrorException *e;

	if (PyType_Ready(&SnmpType) < 0) return;

	m = Py_InitModule3("snmp", NULL, module_doc);
	if (m == NULL)
		return;

	/* Exception registration */
#define ADDEXCEPTION(var, name, parent)					\
	if (var == NULL) {						\
	    var = PyErr_NewException("snmp." name, parent, NULL);	\
	    if (var == NULL)						\
		    return;						\
	}								\
	Py_INCREF(var);							\
	PyModule_AddObject(m, name, var)
	ADDEXCEPTION(SnmpException, "SNMPException", NULL);
	ADDEXCEPTION(SnmpNoSuchObject, "SNMPNoSuchObject", SnmpException);
	ADDEXCEPTION(SnmpNoSuchInstance, "SNMPNoSuchInstance", SnmpException);
	ADDEXCEPTION(SnmpEndOfMibView, "SNMPEndOfMibView", SnmpException);
	for (e = SnmpErrorToException; e->name; e++) {
		if (!e->exception) {
			if (asprintf(&name, "snmp.%s", e->name) == -1) {
				PyErr_NoMemory();
				return;
			}
			exc = PyErr_NewException(name, SnmpException, NULL);
			free(name);
			if (exc == NULL) return;
			e->exception = exc;
		}
		Py_INCREF(e->exception);
		PyModule_AddObject(m, e->name, e->exception);
	}

	/* Constants */
#define ADDCONSTANT(x)				\
	if ((c = PyInt_FromLong(x)) == NULL)	\
		return;				\
	PyModule_AddObject(m, #x, c)
	ADDCONSTANT(ASN_BOOLEAN);
	ADDCONSTANT(ASN_INTEGER);
	ADDCONSTANT(ASN_UNSIGNED);
	ADDCONSTANT(ASN_COUNTER64);
	ADDCONSTANT(ASN_BIT_STR);
	ADDCONSTANT(ASN_OCTET_STR);
	ADDCONSTANT(ASN_NULL);
	ADDCONSTANT(ASN_OBJECT_ID);	
	ADDCONSTANT(ASN_IPADDRESS);
	ADDCONSTANT(SNMP_SEC_LEVEL_NOAUTH);
	ADDCONSTANT(SNMP_SEC_LEVEL_AUTHNOPRIV);
	ADDCONSTANT(SNMP_SEC_LEVEL_AUTHPRIV);
	
	Py_INCREF(&SnmpType);
	PyModule_AddObject(m, "Session", (PyObject *)&SnmpType);

	if (TypesModule == NULL)
		if ((TypesModule = PyImport_ImportModule("snimpy.basictypes")) == NULL)
			return;
	Py_INCREF(TypesModule);
	
	/* Try to load as less MIB as possible */
	unsetenv("MIBS");
	setenv("MIBDIRS", "/dev/null", 1);
	/* Disable any logging */
	snmp_disable_log();
        netsnmp_register_loghandler(NETSNMP_LOGHANDLER_NONE, LOG_DEBUG);
	/* Init SNMP */
	init_snmp("snimpy");
}
