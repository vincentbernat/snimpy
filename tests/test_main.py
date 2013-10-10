import unittest
import os
import tempfile
import code  # nopep8
import mock
from snimpy.main import interact
from multiprocessing import Process
import agent


class TestMain(unittest.TestCase):

    """Test the main shell"""

    @classmethod
    def setUpClass(cls):
        cls.agent = agent.TestAgent()

    @classmethod
    def tearDownClass(cls):
        cls.agent.terminate()

    def test_loadfile(self):
        script = tempfile.NamedTemporaryFile(delete=False)
        try:
            script.write("""
load("IF-MIB")
m = M(host="127.0.0.1:{0}",
      community="public",
      version=2)
assert(m.ifDescr[1] == "lo")
""".format(self.agent.port).encode("ascii"))
            script.close()
            with mock.patch("code.InteractiveInterpreter.write"):
                p = Process(target=interact, args=((script.name,),))
                p.start()
                p.join()
                self.assertEqual(p.exitcode, 0)
        finally:
            os.unlink(script.name)
