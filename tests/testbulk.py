import unittest
from snimpy import manager

class TestBulkParams(unittest.TestCase):

    def setUp(self):
        self.manager1 = manager.Manager('127.0.0.1')
        self.manager2 = manager.Manager('127.0.0.1', version=2)

    def testSettings(self):
        self.assertEqual( len(self.manager2._session.bulk), 2 )
        self.assertIsNone (self.manager1._session.bulk)

        self.manager2._session.bulk = (0, 50)
        non_repeaters, max_repetitions = self.manager2._session.bulk
        self.assertEqual (non_repeaters, 0)
        self.assertEqual (max_repetitions, 50)

    def testToggle(self):
        self.assertTrue(self.manager2._session.use_bulk)
        self.manager2._session.use_bulk = 0
        self.assertFalse(self.manager2._session.use_bulk)
        self.manager2._session.use_bulk = 1
        self.assertTrue(self.manager2._session.use_bulk)


if __name__ == '__main__':
    unittest.main()