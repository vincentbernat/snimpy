import unittest
import os
from snimpy import mib, basictypes

class TestMibSnimpy(unittest.TestCase):

    def setUp(self):
        mib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "SNIMPY-MIB.mib"))
        self.nodes = ["snimpy",
                      "snimpyScalars",
                      "snimpyTables"]
        self.nodes.sort()
        self.tables = ["snimpyComplexTable",
                       "snimpySimpleTable",
                       "snimpyIndexTable"]
        self.tables.sort()
        self.columns = ["snimpyComplexFirstIP",
                        "snimpyComplexSecondIP",
                        "snimpySimpleIndex",
                        "snimpyComplexState",
                        "snimpySimpleDescr",
                        "snimpySimplePhys",
                        "snimpySimpleType",
                        "snimpyIndexVarLen",
                        "snimpyIndexIntIndex",
                        "snimpyIndexOidVarLen",
                        "snimpyIndexFixedLen",
                        "snimpyIndexImplied",
                        "snimpyIndexInt",
                        ]
        self.columns.sort()
        self.scalars = ["snimpyIpAddress",
                        "snimpyString",
                        "snimpyInteger",
                        "snimpyEnum",
                        "snimpyObjectId",
                        "snimpyBoolean",
                        "snimpyCounter",
                        "snimpyGauge",
                        "snimpyTimeticks",
                        "snimpyCounter64",
                        "snimpyBits"]
        self.scalars.sort()

    def tearDown(self):
        mib.reset()

    def testGetNodes(self):
        """Test that we can get all nodes"""
        nodes = mib.getNodes('SNIMPY-MIB')
        snodes = [str(a) for a in nodes]
        snodes.sort()
        self.assertEqual(self.nodes,
                         snodes)
        for n in nodes:
            self.assert_(isinstance(n, mib.Node))

    def testGetTables(self):
        """Test that we can get all tables"""
        tables = mib.getTables('SNIMPY-MIB')
        stables = [str(a) for a in tables]
        stables.sort()
        self.assertEqual(self.tables,
                         stables)
        for n in tables:
            self.assert_(isinstance(n, mib.Table))

    def testGetColumns(self):
        """Test that we can get all columns"""
        columns = mib.getColumns('SNIMPY-MIB')
        scolumns = [str(a) for a in columns]
        scolumns.sort()
        self.assertEqual(self.columns,
                         scolumns)
        for n in columns:
            self.assert_(isinstance(n, mib.Column))

    def testGetScalars(self):
        """Test that we can get all scalars"""
        scalars = mib.getScalars('SNIMPY-MIB')
        sscalars = [str(a) for a in scalars]
        sscalars.sort()
        self.assertEqual(self.scalars, sscalars)
        for n in scalars:
            self.assert_(isinstance(n, mib.Scalar))

    def testGet(self):
        """Test that we can get all named attributes"""
        for i in self.scalars:
            self.assertEqual(str(mib.get('SNIMPY-MIB', i)), i)
            self.assert_(isinstance(mib.get('SNIMPY-MIB', i), mib.Scalar))
        for i in self.tables:
            self.assertEqual(str(mib.get('SNIMPY-MIB', i)), i)
            self.assert_(isinstance(mib.get('SNIMPY-MIB', i), mib.Table))
        for i in self.columns:
            self.assertEqual(str(mib.get('SNIMPY-MIB', i)), i)
            self.assert_(isinstance(mib.get('SNIMPY-MIB', i), mib.Column))
        for i in self.nodes:
            self.assertEqual(str(mib.get('SNIMPY-MIB', i)), i)
            self.assert_(isinstance(mib.get('SNIMPY-MIB', i), mib.Node))

    def testTableColumnRelation(self):
        """Test that we can get the column from the table and vice-versa"""
        for i in self.tables:
            table = mib.get('SNIMPY-MIB', i)
            for r in table.columns:
                self.assert_(isinstance(r, mib.Column))
                self.assertEqual(str(r.table), str(i))
                self.assert_(str(r).startswith(str(i).replace("Table", "")))
            columns = [str(rr) for rr in self.columns
                    if str(rr).startswith(str(i).replace("Table", ""))]
            columns.sort()
            tcolumns = [str(rr) for rr in table.columns]
            tcolumns.sort()
            self.assertEqual(columns, tcolumns)
        for r in self.columns:
            column = mib.get('SNIMPY-MIB', r)
            table = column.table
            self.assert_(isinstance(table, mib.Table))
            prefix = str(table).replace("Table", "")
            self.assertEqual(prefix, str(r)[:len(prefix)])

    def testTypes(self):
        """Test that we get the correct types"""
        tt = { "snimpyIpAddress": basictypes.IpAddress,
               "snimpyString": basictypes.String,
               "snimpyInteger": basictypes.Integer,
               "snimpyEnum": basictypes.Enum,
               "snimpyObjectId": basictypes.Oid,
               "snimpyBoolean": basictypes.Boolean,
               "snimpyCounter": basictypes.Unsigned32,
               "snimpyGauge": basictypes.Unsigned32,
               "snimpyTimeticks": basictypes.Timeticks,
               "snimpyCounter64": basictypes.Unsigned64,
               "snimpyBits": basictypes.Bits,
               "snimpySimpleIndex": basictypes.Integer,
               "snimpyComplexFirstIP": basictypes.IpAddress,
               "snimpyComplexSecondIP": basictypes.IpAddress,
               "snimpyComplexState": basictypes.Enum }
        for t in tt:
            self.assertEqual(mib.get('SNIMPY-MIB', t).type, tt[t])

    def testRanges(self):
        tt = { "snimpyIpAddress": 4,
               "snimpyString": (0,255),
               "snimpyInteger": [(6,18),(20,23),(27,1336)],
               "snimpyEnum": None,
               "snimpyObjectId": None,
               "snimpyBoolean": None,
               "snimpyCounter": (0,4294967295L),
               "snimpyGauge": (0,4294967295L),
               "snimpyTimeticks": (0,4294967295L),
               "snimpyCounter64": (0,18446744073709551615L),
               "snimpyBits": None,
               "snimpySimpleIndex": (1,30),
               "snimpyComplexFirstIP": 4,
               "snimpyComplexSecondIP": 4,
               "snimpyComplexState": None
               }
        for t in tt:
            print t
            self.assertEqual(mib.get('SNIMPY-MIB', t).ranges, tt[t])

    def testEnums(self):
        """Test that we got the enum values correctly"""
        self.assertEqual(mib.get('SNIMPY-MIB', "snimpyInteger").enum, None)
        self.assertEqual(mib.get("SNIMPY-MIB", "snimpyEnum").enum,
                         {1: "up",
                          2: "down",
                          3: "testing"})
        self.assertEqual(mib.get("SNIMPY-MIB", "snimpyBits").enum,
                         {0: "first",
                          1: "second",
                          2: "third",
                          7: "last"})

    def testIndexes(self):
        """Test that we can retrieve correctly the index of tables"""
        self.assertEqual([str(i) for i in mib.get("SNIMPY-MIB", "snimpySimpleTable").index],
                         ["snimpySimpleIndex"])
        self.assertEqual([str(i) for i in mib.get("SNIMPY-MIB", "snimpyComplexTable").index],
                         ["snimpyComplexFirstIP", "snimpyComplexSecondIP"])

    def testImplied(self):
        """Check that we can get implied attribute for a given table"""
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpySimpleTable').implied, False)
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpyComplexTable').implied, False)
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpyIndexTable').implied, True)

    def testOid(self):
        """Test that objects are rooted at the correct OID"""
        oids = { "snimpy": (1,3,6,1,2,1,45121),
                 "snimpyScalars": (1,3,6,1,2,1,45121,1),
                 "snimpyString": (1,3,6,1,2,1,45121,1,2),
                 "snimpyInteger": (1,3,6,1,2,1,45121,1,3),
                 "snimpyBits": (1,3,6,1,2,1,45121,1,11),
                 "snimpyTables": (1,3,6,1,2,1,45121,2),
                 "snimpySimpleTable": (1,3,6,1,2,1,45121,2,1),
                 "snimpySimplePhys": (1,3,6,1,2,1,45121,2,1,1,4),
                 "snimpyComplexTable": (1,3,6,1,2,1,45121,2,2),
                 "snimpyComplexState": (1,3,6,1,2,1,45121,2,2,1,3),
                 }
        for o in oids:
            self.assertEqual(mib.get('SNIMPY-MIB', o).oid, oids[o])

    def testLoadInexistantModule(self):
        """Check that we get an exception when loading an inexistant module"""
        self.assertRaises(mib.SMIException, mib.load, "idontexist.gfdgfdg")

    def testLoadInvalidModule(self):
        """Check that an obviously invalid module cannot be loaded"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "SNIMPY-INVALID-MIB.mib")
        self.assertRaises(mib.SMIException, mib.load, path)
        self.assertRaises(mib.SMIException, mib.getNodes, "SNIMPY-INVALID-MIB")
        self.assertRaises(mib.SMIException, mib.get,
                          "SNIMPY-INVALID-MIB", "invalidSnimpyNode")

    def testAccesInexistantModule(self):
        """Check that we get an exception when querying inexistant module"""
        self.assertRaises(mib.SMIException, mib.getNodes, "idontexist.kjgf");
        self.assertRaises(mib.SMIException, mib.getScalars, "idontexist.kjgf");
        self.assertRaises(mib.SMIException, mib.getTables, "idontexist.kjgf");
        self.assertRaises(mib.SMIException, mib.getColumns, "idontexist.kjgf");
    
    def testFmt(self):
        """Check that we get FMT from types"""
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpySimplePhys').fmt, "1x:")
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpyInteger').fmt, "d-2")
