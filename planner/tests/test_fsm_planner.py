"""Test cases for FSM planner."""
import sys
import os
import unittest

sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

try:
    import lib.lib as lib
    import planner.fsm_planner as fsm_mod
    import tests.test_bot as test_bot
except ImportError:
    print "ImportError: Use 'python -m unittest discover' from project root."
    raise

# Logger object
logger = lib.get_logger()


class TestFSM(test_bot.TestBot):

    """"""

    def setUp(self):
        """Setup test hardware files and create mec_driver object"""
        # Run general bot test setup
        super(TestFSM, self).setUp()

        # Build fsm_planner
        self.fsm = fsm_mod.Robot()

    def tearDown(self):
        """Restore testing flag state in config file."""
        # Run general bot test tear down
        super(TestFSM, self).tearDown()
        lib.set_testing(self.orig_test_state)

    def testBaseCase(self):
        """"""
        self.fsm.run()