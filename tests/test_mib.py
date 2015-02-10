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
                       "snimpyInetAddressTable",
                       "snimpySimpleTable",
                       "snimpyIndexTable"]
        self.tables.sort()
        self.columns = ["snimpyComplexFirstIP",
                        "snimpyComplexSecondIP",
                        "snimpySimpleIndex",
                        "snimpyComplexState",
                        "snimpyInetAddressType",
                        "snimpyInetAddress",
                        "snimpyInetAddressState",
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
                        "snimpyBits",
                        "snimpyNotImplemented",
                        "snimpyOctetString",
                        "snimpyUnicodeString",
                        "snimpyMacAddress"]
        self.scalars.sort()

        self.expected_modules = [u"SNMPv2-SMI",
                                 u"SNMPv2-TC",
                                 u"SNIMPY-MIB",
                                 u"INET-ADDRESS-MIB",
                                 u"IANAifType-MIB"]

    def tearDown(self):
        mib.reset()

    def testGetNodes(self):
        """Test that we can get all nodes"""
        nodes = mib.getNodes('SNIMPY-MIB')
        snodes = sorted([str(a) for a in nodes])
        self.assertEqual(self.nodes,
                         snodes)
        for n in nodes:
            self.assert_(isinstance(n, mib.Node))

    def testGetTables(self):
        """Test that we can get all tables"""
        tables = mib.getTables('SNIMPY-MIB')
        stables = sorted([str(a) for a in tables])
        self.assertEqual(self.tables,
                         stables)
        for n in tables:
            self.assert_(isinstance(n, mib.Table))

    def testGetColumns(self):
        """Test that we can get all columns"""
        columns = mib.getColumns('SNIMPY-MIB')
        scolumns = sorted([str(a) for a in columns])
        self.assertEqual(self.columns,
                         scolumns)
        for n in columns:
            self.assert_(isinstance(n, mib.Column))

    def testGetScalars(self):
        """Test that we can get all scalars"""
        scalars = mib.getScalars('SNIMPY-MIB')
        sscalars = sorted([str(a) for a in scalars])
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

    def testGetByOid(self):
        """Test that we can get all named attributes by OID."""
        for i in self.scalars:
            nodebyname = mib.get('SNIMPY-MIB', i)
            self.assertEqual(str(mib.getByOid(nodebyname.oid)), i)
            self.assert_(isinstance(mib.getByOid(nodebyname.oid), mib.Scalar))
        for i in self.tables:
            nodebyname = mib.get('SNIMPY-MIB', i)
            self.assertEqual(str(mib.getByOid(nodebyname.oid)), i)
            self.assert_(isinstance(mib.getByOid(nodebyname.oid), mib.Table))
        for i in self.columns:
            nodebyname = mib.get('SNIMPY-MIB', i)
            self.assertEqual(str(mib.getByOid(nodebyname.oid)), i)
            self.assert_(isinstance(mib.getByOid(nodebyname.oid), mib.Column))
        for i in self.nodes:
            nodebyname = mib.get('SNIMPY-MIB', i)
            self.assertEqual(str(mib.getByOid(nodebyname.oid)), i)
            self.assert_(isinstance(mib.getByOid(nodebyname.oid), mib.Node))

    def testGetByOid_UnknownOid(self):
        """Test that unknown OIDs raise an exception."""
        self.assertRaises(mib.SMIException, mib.getByOid, (255,))

    def testGetType(self):
        """Test that _getType properly identifies known and unknown types."""
        self.assertEqual(b"PhysAddress",
                         mib.ffi.string(mib._getType("PhysAddress").name))
        self.assertEqual(b"InetAddress",
                         mib.ffi.string(mib._getType(b"InetAddress").name))
        self.assertEqual(None, mib._getType("SomeUnknownType.kjgf"))

    def testTableColumnRelation(self):
        """Test that we can get the column from the table and vice-versa"""
        for i in self.tables:
            table = mib.get('SNIMPY-MIB', i)
            for r in table.columns:
                self.assert_(isinstance(r, mib.Column))
                self.assertEqual(str(r.table), str(i))
                self.assert_(str(r).startswith(str(i).replace("Table", "")))
            columns = sorted([str(rr)
                              for rr in self.columns
                              if str(rr).startswith(str(i).replace("Table",
                                                                   ""))])
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
        tt = {"snimpyIpAddress": basictypes.IpAddress,
              "snimpyString": basictypes.OctetString,
              "snimpyOctetString": basictypes.OctetString,
              "snimpyUnicodeString": basictypes.OctetString,
              "snimpyMacAddress": basictypes.OctetString,
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
              "snimpyComplexState": basictypes.Enum}
        for t in tt:
            self.assertEqual(mib.get('SNIMPY-MIB', t).type, tt[t])

    def testRanges(self):
        tt = {"snimpyIpAddress": 4,
              "snimpyString": (0, 255),
              "snimpyOctetString": None,
              "snimpyInteger": [(6, 18), (20, 23), (27, 1336)],
              "snimpyEnum": None,
              "snimpyObjectId": None,
              "snimpyBoolean": None,
              "snimpyCounter": (0, 4294967295),
              "snimpyGauge": (0, 4294967295),
              "snimpyTimeticks": (0, 4294967295),
              "snimpyCounter64": (0, 18446744073709551615),
              "snimpyBits": None,
              "snimpySimpleIndex": (1, 30),
              "snimpyComplexFirstIP": 4,
              "snimpyComplexSecondIP": 4,
              "snimpyComplexState": None
              }
        for t in tt:
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
        self.assertEqual(
            [str(i) for i in mib.get("SNIMPY-MIB", "snimpySimpleTable").index],
            ["snimpySimpleIndex"])
        self.assertEqual(
            [str(i)
             for i in mib.get("SNIMPY-MIB", "snimpyComplexTable").index],
            ["snimpyComplexFirstIP", "snimpyComplexSecondIP"])
        self.assertEqual(
            [str(i)
             for i in mib.get("SNIMPY-MIB", "snimpyInetAddressTable").index],
            ["snimpyInetAddressType", "snimpyInetAddress"])

    def testImplied(self):
        """Check that we can get implied attribute for a given table"""
        self.assertEqual(
            mib.get("SNIMPY-MIB",
                    'snimpySimpleTable').implied,
            False)
        self.assertEqual(
            mib.get("SNIMPY-MIB",
                    'snimpyComplexTable').implied,
            False)
        self.assertEqual(
            mib.get("SNIMPY-MIB",
                    'snimpyIndexTable').implied,
            True)

    def testOid(self):
        """Test that objects are rooted at the correct OID"""
        oids = {"snimpy": (1, 3, 6, 1, 2, 1, 45121),
                "snimpyScalars": (1, 3, 6, 1, 2, 1, 45121, 1),
                "snimpyString": (1, 3, 6, 1, 2, 1, 45121, 1, 2),
                "snimpyInteger": (1, 3, 6, 1, 2, 1, 45121, 1, 3),
                "snimpyBits": (1, 3, 6, 1, 2, 1, 45121, 1, 11),
                "snimpyTables": (1, 3, 6, 1, 2, 1, 45121, 2),
                "snimpySimpleTable": (1, 3, 6, 1, 2, 1, 45121, 2, 1),
                "snimpySimplePhys": (1, 3, 6, 1, 2, 1, 45121, 2, 1, 1, 4),
                "snimpyComplexTable": (1, 3, 6, 1, 2, 1, 45121, 2, 2),
                "snimpyComplexState": (1, 3, 6, 1, 2, 1, 45121, 2, 2, 1, 3),
                }
        for o in oids:
            self.assertEqual(mib.get('SNIMPY-MIB', o).oid, oids[o])

    def testLoadedMibNames(self):
        """Check that only expected modules were loaded."""
        for module in self.expected_modules:
            self.assertIn(module, list(mib.loadedMibNames()))

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
        self.assertRaises(mib.SMIException, mib.getNodes, "idontexist.kjgf")
        self.assertRaises(mib.SMIException, mib.getScalars, "idontexist.kjgf")
        self.assertRaises(mib.SMIException, mib.getTables, "idontexist.kjgf")
        self.assertRaises(mib.SMIException, mib.getColumns, "idontexist.kjgf")

    def testFmt(self):
        """Check that we get FMT from types"""
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpySimplePhys').fmt, "1x:")
        self.assertEqual(mib.get("SNIMPY-MIB", 'snimpyInteger').fmt, "d-2")

    def testTypeOverrides(self):
        """Check that we can override a type"""
        table = mib.get("SNIMPY-MIB", "snimpyInetAddressTable")
        addrtype_attr = table.index[0]
        addr_attr = table.index[1]

        # Try overriding to IPv4 with a byte string name.
        addrtype = addrtype_attr.type(addrtype_attr, "ipv4")
        self.assertEqual(addrtype, "ipv4")
        addr_attr.typeName = b"InetAddressIPv4"
        ipv4 = u"127.0.0.1"
        ipv4_oid = (4, 127, 0, 0, 1)

        addr = addr_attr.type(addr_attr, ipv4)
        self.assertEqual(str(addr), ipv4)
        self.assertEqual(addr.toOid(), ipv4_oid)

        addr_len, addr = addr_attr.type.fromOid(addr_attr, ipv4_oid)
        self.assertEqual(addr_len, ipv4_oid[0] + 1)
        self.assertEqual(str(addr), ipv4)
        self.assertEqual(addr.toOid(), ipv4_oid)

        # Try both IPv6 and non-bytes name.
        addrtype = addrtype_attr.type(addrtype_attr, "ipv6")
        self.assertEqual(addrtype, "ipv6")
        addr_attr.typeName = u"InetAddressIPv6"
        # Snimpy does not use leading zeroes.
        ipv6 = u'102:304:506:708:90a:b0c:d0e:f01'
        ipv6_oid = (16, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x01)

        addr = addr_attr.type(addr_attr, ipv6)
        self.assertEqual(str(addr), ipv6)
        self.assertEqual(addr.toOid(), ipv6_oid)

        addr_len, addr = addr_attr.type.fromOid(addr_attr, ipv6_oid)
        self.assertEqual(addr_len, ipv6_oid[0] + 1)
        self.assertEqual(str(addr), ipv6)
        self.assertEqual(addr.toOid(), ipv6_oid)

        # Try a type from a different module (chosen because snmpwalk
        # prints IPv6 addresses incorrectly).
        ipv6_1xformat = u'1:2:3:4:5:6:7:8:9:a:b:c:d:e:f:1'
        addr_attr.typeName = "PhysAddress"

        addr = addr_attr.type(addr_attr, ipv6_1xformat)
        self.assertEqual(str(addr), ipv6_1xformat)
        self.assertEqual(addr.toOid(), ipv6_oid)

        # Try overriding back to the default.
        del addr_attr.typeName
        addr_len, addr = addr_attr.type.fromOid(addr_attr, ipv4_oid)
        self.assertEqual(bytes(addr), b"\x7f\0\0\1")

    def testTypeOverrides_Errors(self):
        table = mib.get("SNIMPY-MIB", "snimpyInetAddressTable")
        attr = table.index[1]

        # Value with the wrong type.
        self.assertRaises(AttributeError, setattr, attr, "typeName", None)

        # Unknown type.
        self.assertRaises(mib.SMIException, setattr, attr, "typeName",
                          "SomeUnknownType.kjgf")

        # Incompatible basetype.
        self.assertRaises(mib.SMIException, setattr, attr, "typeName",
                          "InetAddressType")

        # Parse error.
        attr.typeName = "InetAddressIPv4"
        self.assertRaises(ValueError, attr.type, attr, u"01:02:03:04")

    def testTypeName(self):
        """Check that we can get the current declared type name"""
        table = mib.get("SNIMPY-MIB", "snimpyInetAddressTable")
        attr = table.index[1]

        self.assertEqual(attr.typeName, b"InetAddress")

        attr.typeName = b"InetAddressIPv4"
        self.assertEqual(attr.typeName, b"InetAddressIPv4")

        attr.typeName = b"InetAddressIPv6"
        self.assertEqual(attr.typeName, b"InetAddressIPv6")

        attr = mib.get("SNIMPY-MIB", "snimpySimpleIndex")
        self.assertEqual(attr.typeName, b"Integer32")
