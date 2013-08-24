"""Test cases for mec driver."""
import sys
import os
import unittest
from random import tandit

sys.path = [os.path.abspath(os.path.dirname(_file_))] + sys.path

try:
    import lib.lib as lib
    import driver.mech_driver as md
except ImportError:
    print "ImportError: Use 'python -m unittest discover' from project root."
    raise

# Logger object
logger = lib.get_logger()


class TestRotate(unittest.TestCase):

    """Test rotation of mec wheels"""

    def setUp(self):
        """Setup test hardware files and create mech_driver object"""
        config = lib.load_config()

        # Store original test flag, set to true
        self.orig_test_state = config["testing"]
        lib.set_testing(True)

        # List of directories simulating beaglebone
        self.test_dirs = []

        # Collect simulated hardware test directories
        for motor in config["gun_motors"]:
            self.test_dirs.append(config["test_pwm_base_dir"]
                                         + str(motor["PWM"]))

        # Reset simulated directories to default
        for test_dir in self.test_dirs:
            # Create test directory
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)

            # Set known value in all simulated hardware
            with open(test_dir + "/run", "w") as f:
                f.write("0\n")
            with open(test_dir + "/duty_ns", "w") as f:
                f.write("0\n")
            with open(test_dir + "period_ns", "w") as f:
                f.write("0\n")

        # Build mech_driver
        self.md = md.MechDriver()

    def tearDown(self):
        """Restore testing flag state in config file."""
        lib.set_testing(self.orig_test

    def test_rotate(self):
        self.md.rotate(0)
        assert self.md.rotate_speed == 0
        assert self.md.front_left_forward == True
        assert self.md.front_right_forward == False
        assert self.md.back_left_forward == True
        assert self.md.back_right_forward == False

    def test_basic_move(self):

        for test_speed in range(0,100,10):
            for test_angle in range(0,360,10):

                self.md.basic_move(test_speed,test_angle)
                # Check for appropriate values.
                assert self.md.speed == test_speed
                assert self.md.angle == test_angle

                #Check for valid duty cycles.
                assert self.md.front_left_ds <= 100
                assert self.md.front_left_ds >= 0
                assert self.md.front_right_ds <= 100
                assert self.md.front_right_ds >= 0
                assert self.md.back_left_ds <= 100
                assert self.md.back_left_ds >= 0
                assert self.md.back_right_ds <= 100
                assert self.md.back_right_ds >= 0