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

/* Simple interface to libsmi */

#include <Python.h>
#include <smi.h>

/* Exceptions */
static PyObject *SmiException;

/* Types */
static PyObject *TypesModule;

/* MIB objects:

 Entity
  |
  +--- Scalar
  +--- Table
  +--- Column
  \--- Node
*/
typedef struct {
	PyObject_HEAD
	SmiNode *node;
} EntityObject;
typedef struct {
	EntityObject entity;
} ScalarObject;
typedef struct {
	EntityObject entity;
} TableObject;
typedef struct {
	EntityObject entity;
} ColumnObject;
typedef struct {
	EntityObject entity;
} NodeObject;

static PyObject* entity_gettype(EntityObject *, void *);
static PyObject* entity_getoid(EntityObject *, void *);
static PyObject* entity_getfmt(EntityObject *, void *);
static PyObject* entity_getranges(EntityObject *, void *);
static PyObject* entity_getenum(EntityObject *, void *);
static PyObject* table_getcolumns(EntityObject *, void *);
static PyObject* table_getindex(EntityObject *, void *);
static PyObject* table_isimplied(EntityObject *, void *);
static PyObject* column_gettable(EntityObject *, void *);
static PyGetSetDef entity_getseters[] = {
	{"type",
	 (getter)entity_gettype, NULL,
	 "entity type", NULL},
	{"oid",
	 (getter)entity_getoid, NULL,
	 "entity oid", NULL},
	{"fmt",
	 (getter)entity_getfmt, NULL,
	 "entity fmt", NULL},
	{"ranges",
	 (getter)entity_getranges, NULL,
	 "entity type ranges", NULL},
	{"enum",
	 (getter)entity_getenum, NULL,
	 "entity enum values", NULL},
	{NULL}  /* Sentinel */
};
static PyGetSetDef table_getseters[] = {
	{"columns",
	 (getter)table_getcolumns, NULL,
	 "table columns", NULL},
	{"implied",
	 (getter)table_isimplied, NULL,
	 "is the last index implied?", NULL},
	{"index",
	 (getter)table_getindex, NULL,
	 "table index(es)", NULL},
	{NULL}  /* Sentinel */
};
static PyGetSetDef column_getseters[] = {
	{"table",
	 (getter)column_gettable, NULL,
	 "table columns", NULL},
	{NULL}  /* Sentinel */
};


static PyObject* entity_repr(EntityObject *);
static PyObject* entity_str(EntityObject *);
static PyTypeObject EntityType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"mib.Entity",              /*tp_name*/
	sizeof(EntityObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	(reprfunc)entity_repr,	   /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	(reprfunc)entity_str,	   /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT |
	Py_TPFLAGS_BASETYPE,	   /*tp_flags*/
	"MIB entity",              /*tp_doc*/
	0,			   /* tp_traverse */
	0,			   /* tp_clear */
	0,			   /* tp_richcompare */
	0,			   /* tp_weaklistoffset */
	0,			   /* tp_iter */
	0,			   /* tp_iternext */
	0,			   /* tp_methods */
	0,			   /* tp_members */
	entity_getseters,	   /* tp_getset */
};
static PyTypeObject ScalarType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"mib.Scalar",		   /*tp_name*/
	sizeof(ScalarObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,        /*tp_flags*/
	"MIB scalar entity",	   /*tp_doc*/
};
static PyTypeObject TableType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"mib.Table",		   /*tp_name*/
	sizeof(TableObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,        /*tp_flags*/
	"MIB table entity",	   /*tp_doc*/
	0,			   /* tp_traverse */
	0,			   /* tp_clear */
	0,			   /* tp_richcompare */
	0,			   /* tp_weaklistoffset */
	0,			   /* tp_iter */
	0,			   /* tp_iternext */
	0,			   /* tp_methods */
	0,			   /* tp_members */
	table_getseters,	   /* tp_getset */
};
static PyTypeObject ColumnType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"mib.Column",		   /*tp_name*/
	sizeof(ColumnObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,        /*tp_flags*/
	"MIB column entity",	   /*tp_doc*/
	0,			   /* tp_traverse */
	0,			   /* tp_clear */
	0,			   /* tp_richcompare */
	0,			   /* tp_weaklistoffset */
	0,			   /* tp_iter */
	0,			   /* tp_iternext */
	0,			   /* tp_methods */
	0,			   /* tp_members */
	column_getseters,	   /* tp_getset */
};
static PyTypeObject NodeType = {
	PyObject_HEAD_INIT(NULL)
	0,			   /*ob_size*/
	"mib.Node",		   /*tp_name*/
	sizeof(NodeObject),	   /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	0,                         /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,        /*tp_flags*/
	"MIB node entity",	   /*tp_doc*/
};

static PyObject*
column_gettable(EntityObject *self, void *closure)
{
	SmiNode *parent;
	EntityObject *table;

	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	parent = smiGetParentNode(self->node);
	if (!parent || (parent->nodekind != SMI_NODEKIND_ROW)) {
		PyErr_Format(SmiException, "parent %s of %s is not a row",
		    parent->name, self->node->name);
		return NULL;
	}
	if ((parent = smiGetParentNode(parent)) == NULL) {
		PyErr_Format(SmiException, "unable to get parent of %s",
		    self->node->name);
		return NULL;
	}
	if (parent->nodekind != SMI_NODEKIND_TABLE) {
		PyErr_Format(SmiException, "parent %s of %s is not a table",
		    parent->name, self->node->name);
		return NULL;
	}
	if ((table = (EntityObject*)PyObject_CallObject((PyObject*)&TableType,
		    NULL)) == NULL) {
		PyErr_Format(SmiException, "unable to create table object for %s",
		    parent->name);
		return NULL;
	}
	table->node = parent;
	return (PyObject*)table;
}

static PyObject*
table_getcolumns(EntityObject *self, void *closure)
{
	SmiNode *child;
	EntityObject *column;
	PyObject *lcolumns;

	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	child = smiGetFirstChildNode(self->node);
	if (!child || (child->nodekind != SMI_NODEKIND_ROW)) {
		PyErr_Format(SmiException, "child %s of %s is not a row",
		    child->name, self->node->name);
		return NULL;
	}
	if ((lcolumns = PyList_New(0)) == NULL)
		return NULL;
	child = smiGetFirstChildNode(child);
	while (child != NULL) {
		if (child->nodekind != SMI_NODEKIND_COLUMN) {
			PyErr_Format(SmiException, "child %s of %s is not a column",
			    child->name, self->node->name);
			Py_DECREF(lcolumns);
			return NULL;
		}
		if ((column = (EntityObject*)PyObject_CallObject((PyObject*)&ColumnType,
			    NULL)) == NULL) {
			PyErr_Format(SmiException, "unable to create column object for %s",
			    child->name);
			Py_DECREF(lcolumns);
			return NULL;
		}
		column->node = child;
		if (PyList_Append(lcolumns, (PyObject*)column) != 0) {
			Py_DECREF(lcolumns);
			Py_DECREF((PyObject*)column);
			return NULL;
		}
		Py_DECREF((PyObject*)column);
		child = smiGetNextChildNode(child);
	}
	return lcolumns;
}

static SmiNode*
table_getrow(EntityObject *self, void *closure)
{
	SmiNode *child;
	child = smiGetFirstChildNode(self->node);
	if (child && (child->indexkind == SMI_INDEX_AUGMENT)) {
		child = smiGetRelatedNode(child);
		if (!child) {
			PyErr_Format(SmiException,
			    "AUGMENT index for %s but unable to retrieve it",
			    self->node->name);
			return NULL;
		}
	}
	if (!child || (child->nodekind != SMI_NODEKIND_ROW)) {
		PyErr_Format(SmiException, "child %s of %s is not a row",
		    child->name, self->node->name);
		return NULL;
	}
	if (child->indexkind != SMI_INDEX_INDEX) {
		PyErr_Format(SmiException,
		    "child %s of %s has an unhandled kind of index",
		    child->name, self->node->name);
		return NULL;
	}
	return child;
}

static PyObject*
table_isimplied(EntityObject *self, void *closure)
{
	SmiNode *child;
	if (self->node == NULL) {
		Py_INCREF(Py_False);
		return Py_False;
	}
	if ((child = table_getrow(self, closure)) == NULL)
		return NULL;
	if (child->implied) {
		Py_INCREF(Py_True);
		return Py_True;
	}
	Py_INCREF(Py_False);
	return Py_False;
}

static PyObject*
table_getindex(EntityObject *self, void *closure)
{
	SmiElement *element;
	SmiNode *nelement, *child;
	PyObject *lindex;
	EntityObject *index;

	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	if ((child = table_getrow(self, closure)) == NULL)
		return NULL;

	element = smiGetFirstElement(child);
	if ((lindex= PyList_New(0)) == NULL)
		return NULL;
	while (element != NULL) {
		if ((nelement = smiGetElementNode(element)) == NULL) {
			PyErr_Format(SmiException, "cannot get index associated with %s",
			    self->node->name);
			Py_DECREF(lindex);
			return NULL;
		}
		if (nelement->nodekind != SMI_NODEKIND_COLUMN) {
			PyErr_Format(SmiException, "index %s for %s is not a column",
			    nelement->name, self->node->name);
			Py_DECREF(lindex);
			return NULL;
		}
		if ((index = (EntityObject*)PyObject_CallObject((PyObject*)&ColumnType,
			    NULL)) == NULL) {
			PyErr_Format(SmiException, "unable to create column object for %s",
			    index->node->name);
			Py_DECREF(lindex);
			return NULL;
		}
		index->node = nelement;
		if (PyList_Append(lindex, (PyObject*)index) != 0) {
			Py_DECREF((PyObject*)index);
			Py_DECREF(lindex);
			return NULL;
		}
		Py_DECREF((PyObject*)index);
		element = smiGetNextElement(element);
	}
	return lindex;
}

static PyObject*
entity_getoid(EntityObject *self, void *closure)
{
	PyObject *tuple, *integer;
	int i;

	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	if ((tuple = PyTuple_New(self->node->oidlen)) == NULL)
		return NULL;
	for (i = 0; i < self->node->oidlen; i++) {
		integer = PyInt_FromLong(self->node->oid[i]);
		if (PyTuple_SetItem(tuple, i, integer) != 0) {
			Py_DECREF(integer);
			return NULL;
		}
	}
	return tuple;
}

struct typeConversion {
	int   type;
	char *name;
	char *target;
};
static struct typeConversion typeToPython[] = {
	{ SMI_BASETYPE_INTEGER32, NULL, "Integer" },
	{ SMI_BASETYPE_INTEGER64, NULL, "Integer" },
	{ SMI_BASETYPE_UNSIGNED32, "TimeTicks", "Timeticks" },
	{ SMI_BASETYPE_UNSIGNED32, NULL, "Unsigned32" },
	{ SMI_BASETYPE_UNSIGNED64, NULL, "Unsigned64" },
	{ SMI_BASETYPE_OCTETSTRING, "IpAddress", "IpAddress" },
	{ SMI_BASETYPE_OCTETSTRING, NULL, "String" },
	{ SMI_BASETYPE_OBJECTIDENTIFIER, NULL, "Oid" },
	{ SMI_BASETYPE_ENUM, "TruthValue", "Boolean" },
	{ SMI_BASETYPE_ENUM, NULL, "Enum" },
	{ SMI_BASETYPE_BITS, NULL, "Bits" },
	{ 0, NULL, NULL }
};
static PyObject*
entity_gettype(EntityObject *self, void *closure)
{
	SmiType *type;
	PyObject *result = NULL;
	int i = 0;

	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	if ((type = smiGetNodeType(self->node)) == NULL) {
		PyErr_SetString(SmiException, "unable to retrieve type");
		return NULL;
	}
	
	while (typeToPython[i].target != NULL) {
		if ((type->basetype == typeToPython[i].type) &&
		    ((typeToPython[i].name == NULL) ||
			(type->name && !strcmp(type->name, typeToPython[i].name)))) {
			result = PyObject_GetAttrString(TypesModule, typeToPython[i].target);
			break;
		}
		i++;
	}
	if ((result == NULL) && (!PyErr_Occurred()))
		PyErr_Format(SmiException, "unable to convert type of %s",
		    self->node->name);
	return result;
}

static PyObject*
entity_getfmt(EntityObject *self, void *closure)
{
	SmiType *type;

	if ((self->node == NULL) ||
	    ((type = smiGetNodeType(self->node)) == NULL) ||
	    (!type->format)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return PyString_FromString(type->format);
}

static PyObject*
entity_getranges(EntityObject *self, void *closure)
{
	SmiType *type;
	SmiRange *range;
	SmiValue *value;
	PyObject *cur, *min, *max, *list, *couple;
	int result;

	if ((self->node == NULL) ||
	    ((type = smiGetNodeType(self->node)) == NULL) ||
	    ((range = smiGetFirstRange(type)) == NULL)) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	if ((list = PyList_New(0)) == NULL)
		return NULL;
	while (range) {
		min = max = cur = NULL;
		value = &range->minValue;
		do {
			switch (value->basetype) {
			case SMI_BASETYPE_INTEGER32:
				cur = PyInt_FromLong(value->value.integer32);
				break;
			case SMI_BASETYPE_UNSIGNED32:
				cur = PyLong_FromUnsignedLong(value->value.unsigned32);
				break;
			case SMI_BASETYPE_INTEGER64:
				cur = PyLong_FromLongLong(value->value.integer64);
				break;
			case SMI_BASETYPE_UNSIGNED64:
				cur = PyLong_FromUnsignedLongLong(value->value.unsigned64);
				break;
			default:
				cur = NULL;
				break;
			}
			if (value == &range->minValue)
				min = cur;
			else
				max = cur;
			value++;
		} while (value == &range->maxValue);
		if (!min || !max) {
			Py_XDECREF(min);
			Py_XDECREF(max);
			continue;
		}
		if ((PyObject_Cmp(min, max, &result) == -1) || (result != 0)) {
			couple = PyTuple_Pack(2, min, max);
			Py_DECREF(min);
			Py_DECREF(max);
			if (!couple) return NULL;
		} else {
			couple = min;
			Py_DECREF(max);
		}
		if (PyList_Append(list, couple) == -1) {
			Py_DECREF(couple);
			return NULL;
		}
		Py_DECREF(couple);
		range = smiGetNextRange(range);
	}

	if (PyList_Size(list) <= 0) {
		Py_DECREF(list);
		Py_INCREF(Py_None);
		return Py_None;
	}
	if (PyList_Size(list) == 1) {
		if ((couple = PyList_GetItem(list, 0)) == NULL) {
			Py_DECREF(list);
			return NULL;
		}
		Py_INCREF(couple);
		Py_DECREF(list);
		return couple;
	}	
	return list;
}

static PyObject*
entity_getenum(EntityObject *self, void *closure)
{
	SmiType *type;
	SmiNamedNumber *element;
	PyObject *dict, *key, *value;

	if ((self->node == NULL) ||
	    ((type = smiGetNodeType(self->node)) == NULL) ||
	    ((type->basetype != SMI_BASETYPE_ENUM) &&
		(type->basetype != SMI_BASETYPE_BITS))) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	if ((dict = PyDict_New()) == NULL) return NULL;
	element = smiGetFirstNamedNumber(type);
	while (element != NULL) {
		if ((element->value.basetype != SMI_BASETYPE_UNSIGNED32) &&
		    (element->value.basetype != SMI_BASETYPE_INTEGER32)) {
			PyErr_Format(SmiException, "unhandled member for enumeration of %s (%d)",
			    self->node->name, element->value.basetype);
			Py_DECREF(dict);
			return NULL;
		}
		if ((key = PyInt_FromLong(element->value.value.integer32)) == NULL) {
			Py_DECREF(dict);
			return NULL;
		}
		if ((value = PyString_FromString(element->name)) == NULL) {
			Py_DECREF(dict);
			Py_DECREF(key);
			return NULL;
		}
		if (PyDict_SetItem(dict, key, value) != 0) {
			Py_DECREF(dict);
			Py_DECREF(key);
			Py_DECREF(value);
			return NULL;
		}
		Py_DECREF(key);
		Py_DECREF(value);
		element = smiGetNextNamedNumber(element);
	}
	return dict;
}

static PyObject*
entity_str(EntityObject *self)
{
	if (self->node == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	return PyString_FromString(self->node->name);
}

static PyObject*
entity_repr(EntityObject *self)
{
	char *repr;
	PyObject *result;
	SmiModule *module;
	if ((self->node == NULL) ||
	    (repr = smiRenderNode(self->node, SMI_RENDER_ALL)) == NULL)
		return PyString_FromFormat("<uninitialized %s object at %p>",
		    self->ob_type->tp_name, self);
	if ((module = smiGetNodeModule(self->node)) == NULL) {
		PyErr_SetString(SmiException, "unable to guess module");
		free(repr);
		return NULL;
	}
	result = PyString_FromFormat("<%s %s from '%s'>",
	    self->ob_type->tp_name, repr,
	    module->name);
	free(repr);
	return result;
}

static PyObject*
mib_reset(PyObject *self)
{
	smiExit();
	if (smiInit("snimpy") != 0) {
		PyErr_SetString(SmiException,
		    "unable to init libsmi");
		return NULL;
	}
	smiSetErrorLevel(0);
	smiSetFlags(SMI_FLAG_ERRORS | SMI_FLAG_RECURSIVE);

	Py_INCREF(Py_None);
	return Py_None;
}

/* Check if a module exists and is conform. It should be used instead
   of smiGetModule */
static SmiModule*
mib_get_module(const char *modulename)
{
	SmiModule *m;
	if (((m = smiGetModule(modulename)) == NULL) ||
	    ((m->conformance) && (m->conformance <= 1)))
		return NULL;
	return m;
}

static PyObject*
mib_load(PyObject *self, PyObject *args)
{
	const char *module;
	char *modulename;

	if (!PyArg_ParseTuple(args, "s", &module))
		return NULL;
	if ((modulename = smiLoadModule(module)) == NULL) {
		PyErr_Format(SmiException, "unable to load %s", module);
		return NULL;
	}
	if (!mib_get_module(modulename)) {
		PyErr_Format(SmiException,
			     "%s contains major SMI errors (check with smilint -s -l1)",
			     module);
		return NULL;
	}
	return PyString_FromString(modulename);
}

static PyObject*
mib_get_kind(PyObject *self, PyObject *args, int kind, PyObject *ObjectType)
{
	const char *mib;
	SmiModule *module;
	SmiNode *node;
	EntityObject *pnode;
	PyObject *lnode;
	if (!PyArg_ParseTuple(args, "s", &mib))
		return NULL;
	if ((module = mib_get_module(mib)) == NULL) {
		PyErr_Format(SmiException, "no module named %s", mib);
		return NULL;
	}
	if ((lnode = PyList_New(0)) == NULL)
		return NULL;
	node = smiGetFirstNode(module, kind);
	while (node != NULL) {
		if ((pnode = (EntityObject*)PyObject_CallObject(ObjectType,
			    NULL)) == NULL) {
			PyErr_Format(SmiException, "unable to create entity object for %s",
			    node->name);
			Py_DECREF(lnode);
			return NULL;
		}
		pnode->node = node;
		if (PyList_Append(lnode, (PyObject*)pnode) != 0) {
			Py_DECREF((PyObject*)pnode);
			Py_DECREF(lnode);
			return NULL;
		}
		Py_DECREF((PyObject*)pnode);
		node = smiGetNextNode(node, kind);
	}
	return lnode;
}

static PyObject*
mib_get_nodes(PyObject* self, PyObject *args)
{
	return mib_get_kind(self, args, SMI_NODEKIND_NODE, (PyObject *)&NodeType);
}

static PyObject*
mib_get_scalars(PyObject* self, PyObject *args)
{
	return mib_get_kind(self, args, SMI_NODEKIND_SCALAR, (PyObject *)&ScalarType);
}

static PyObject*
mib_get_tables(PyObject* self, PyObject *args)
{
	return mib_get_kind(self, args, SMI_NODEKIND_TABLE, (PyObject *)&TableType);
}

static PyObject*
mib_get_columns(PyObject* self, PyObject *args)
{
	return mib_get_kind(self, args, SMI_NODEKIND_COLUMN, (PyObject *)&ColumnType);
}

static PyObject*
mib_get(PyObject* self, PyObject *args)
{
	const char *mib;
	const char *name;
	SmiModule *module;
	SmiNode *node;
	EntityObject *pnode;

	if (!PyArg_ParseTuple(args, "ss", &mib, &name))
		return NULL;
	if ((module = mib_get_module(mib)) == NULL) {
		PyErr_Format(SmiException, "no module named %s", mib);
		return NULL;
	}
	if ((node = smiGetNode(module, name)) == NULL) {
		PyErr_Format(SmiException, "in %s, no node named %s", mib, name);
		return NULL;
	}
	switch (node->nodekind) {
	case SMI_NODEKIND_NODE:
		pnode = (EntityObject*)PyObject_CallObject((PyObject*)&NodeType,
		    NULL);
		break;
	case SMI_NODEKIND_SCALAR:
		pnode = (EntityObject*)PyObject_CallObject((PyObject*)&ScalarType,
		    NULL);
		break;
	case SMI_NODEKIND_TABLE:
		pnode = (EntityObject*)PyObject_CallObject((PyObject*)&TableType,
		    NULL);
		break;
	case SMI_NODEKIND_COLUMN:
		pnode = (EntityObject*)PyObject_CallObject((PyObject*)&ColumnType,
		    NULL);
		break;
	default:
		pnode = (EntityObject*)PyObject_CallObject((PyObject*)&EntityType,
		    NULL);
		break;
	}
	if (!pnode) {
		PyErr_Format(SmiException, "unable to create object for %s", node->name);
		return NULL;
	}
	pnode->node = node;
	return (PyObject*)pnode;
}

static PyMethodDef mib_methods[] = {
	{"reset",       (PyCFunction)mib_reset,
	 METH_NOARGS,  "Reset libsmi to its initial state" },
	{"load",        mib_load,
	 METH_VARARGS,  "Load a MIB into the library" },
	{"getNodes",    mib_get_nodes,
	 METH_VARARGS,  "Get all node objects" },
	{"getScalars",  mib_get_scalars,
	 METH_VARARGS,  "Get all scalar objects" },
	{"getTables",   mib_get_tables,
	 METH_VARARGS,  "Get all table objects" },
	{"getColumns",  mib_get_columns,
	 METH_VARARGS,  "Get all column objects" },
	{"get",         mib_get,
	 METH_VARARGS,  "Get a node by its name" },
	{NULL,		NULL}		/* sentinel */
};

PyDoc_STRVAR(module_doc,
    "simple interface to libsmi");

PyMODINIT_FUNC
initmib(void)
{
	PyObject *m;

	EntityType.tp_new = PyType_GenericNew;
	ScalarType.tp_base = &EntityType;
	TableType.tp_base = &EntityType;
	ColumnType.tp_base = &EntityType;
	NodeType.tp_base = &EntityType;
	if (PyType_Ready(&EntityType) < 0) return;
	if (PyType_Ready(&ScalarType) < 0) return;
	if (PyType_Ready(&TableType) < 0) return;
	if (PyType_Ready(&ColumnType) < 0) return;
	if (PyType_Ready(&NodeType) < 0) return;

	m = Py_InitModule3("mib", mib_methods, module_doc);
	if (m == NULL)
		return;

	/* Add some symbolic constants to the module */
	if (SmiException == NULL) {
		SmiException = PyErr_NewException("mib.SMIException", NULL, NULL);
		if (SmiException == NULL)
			return;
	}
	Py_INCREF(SmiException);
	PyModule_AddObject(m, "SMIException", SmiException);
	Py_INCREF(&EntityType);
	PyModule_AddObject(m, "Entity", (PyObject *)&EntityType);
	Py_INCREF(&ScalarType);
	PyModule_AddObject(m, "Scalar", (PyObject *)&ScalarType);
	Py_INCREF(&TableType);
	PyModule_AddObject(m, "Table", (PyObject *)&TableType);
	Py_INCREF(&ColumnType);
	PyModule_AddObject(m, "Column", (PyObject *)&ColumnType);
	Py_INCREF(&NodeType);
	PyModule_AddObject(m, "Node", (PyObject *)&NodeType);

	if (TypesModule == NULL)
		if ((TypesModule = PyImport_ImportModule("snimpy.basictypes")) == NULL)
			return;
	Py_INCREF(TypesModule);

	Py_XDECREF(mib_reset(NULL));
}
