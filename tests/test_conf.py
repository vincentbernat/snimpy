import unittest
import os
import tempfile

from snimpy.config import Conf


class TestConf(unittest.TestCase):

    """Test configuration loading"""

    def test_default_configuration(self):
        """Check we can load the default configuration"""
        conf = Conf()
        loaded = conf.load()
        self.assertEqual(conf, loaded)
        self.assertEqual(conf.mibs, [])
        self.assertEqual(conf.ipython, True)
        self.assertEqual(conf.prompt, "\033[1m[snimpy]>\033[0m ")

    def test_inexistent_configuration(self):
        conf = Conf().load("dontexist")
        self.assertEqual(conf.mibs, [])
        self.assertEqual(conf.ipython, True)

    def test_loading_custom_configuration(self):
        conffile = tempfile.NamedTemporaryFile(delete=False)
        try:
            conffile.write("""
mibs = [ "IF-MIB", "LLDP-MIB" ]
ipython = False
unknown = "hey!"
""".encode("ascii"))
            conffile.close()
            conf = Conf().load(conffile.name)
            self.assertEqual(conf.mibs, ["IF-MIB", "LLDP-MIB"])
            self.assertEqual(conf.unknown, "hey!")
            self.assertEqual(conf.ipython, False)
            self.assertEqual(conf.ipythonprofile, None)
        finally:
            os.unlink(conffile.name)
