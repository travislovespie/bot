"""Test cases for wheel_gun module."""

import time
import unittest

import tests.test_bot as test_bot
import hardware.wheel_gun as wgun_mod


class TestWheelGun(test_bot.TestBot):

    """Test wheel-based gun functions.

    Note that this is meant to be a superclass.

    """

    def dummy_sleep(self, duration):
        """This will replace time.sleep to make tests run quickly."""
        # Call actual sleep, in case test depends on it
        self.real_sleep(0.001)

    def setUp(self):
        """Setup test hardware files and create WheelGun instance."""
        # Run general bot test setup
        super(TestWheelGun, self).setUp()

        # Remap time.sleep to a dummy sleep function so that tests run fast
        self.real_sleep = time.sleep
        time.sleep = self.dummy_sleep

        # Build WheelGun
        self.gun = wgun_mod.WheelGun()

    def tearDown(self):
        """Restore testing flag in config, restore sleep function."""
        # Restore real time.sleep function
        time.sleep = self.real_sleep

        # Run general bot test tear down
        super(TestWheelGun, self).tearDown()


class TestLaser(TestWheelGun):

    """Test cases related to the WheelGun laser."""

    def setUp(self):
        """Call parent setUp to build test hardware and WheelGun instance."""
        super(TestLaser, self).setUp()

    def tearDown(self):
        """Call parent tearDown to restore testing flag and sleep function."""
        super(TestLaser, self).tearDown()

    def check_laser_gpio(self, value):
        """Helper function for checks used repeatedly.

        :param value: Value that the laser's GPIO should equal.

        """
        read_value = int(self.get_gpio(
            self.config['gun']['laser_gpio'])['value'])
        assert read_value == value, "{} != {}".format(read_value, value)

    def test_laser_on(self):
        """Turn laser on, check result."""
        self.gun.laser = 1
        self.check_laser_gpio(1)

        # Test laser getter
        assert self.gun.laser == 1

    def test_laser_off(self):
        """Turn laser off, check result."""
        self.gun.laser = 0
        self.check_laser_gpio(0)

        # Test laser getter
        assert self.gun.laser == 0

    def test_laser_invalid(self):
        """Set laser to invalid value."""
        orig_value = self.gun.laser
        assert orig_value == 0 or orig_value == 1

        # Test -1
        self.gun.laser = -1
        self.check_laser_gpio(orig_value)

        # Test laser getter
        assert self.gun.laser == orig_value

        # Test 2
        self.gun.laser = 2
        self.check_laser_gpio(orig_value)

        # Test laser getter
        assert self.gun.laser == orig_value


class TestSpin(TestWheelGun):

    """Test setting the gun wheels spin/not spin using a GPIO."""

    def setUp(self):
        """Call parent setUp to make simulated hardware and build WheelGun."""
        super(TestSpin, self).setUp()

    def tearDown(self):
        """Call parent tearDown to restore testing flag in config."""
        super(TestSpin, self).tearDown()

    def check_motor_gpios(self, value):
        """Helper method for checking gun motor GPIO values.

        :param value: Value that the GPIOs should be set to.

        """
        assert int(self.get_gpio(
            self.config['gun']['motor_gpios']['left'])['value']) == value
        assert int(self.get_gpio(
            self.config['gun']['motor_gpios']['right'])['value']) == value

    def test_spin_on(self):
        """Test spinning the gun motors up."""
        # Test spin ON (1)
        self.gun.spin = 1
        self.check_motor_gpios(1)

        # Test getter
        assert self.gun.spin == 1

    def test_spin_off(self):
        """Test spinning the gun motors down."""
        # Test spin OFF (0)
        self.gun.spin = 0
        self.check_motor_gpios(0)

        # Test getter
        assert self.gun.spin == 0

    def test_spin_invalid(self):
        """Test giving invalid values to the gun motors."""
        orig_value = self.gun.spin
        assert orig_value == 0 or orig_value == 1

        # Test invalid spin state (-1)
        self.gun.spin = -1
        self.check_motor_gpios(orig_value)

        assert self.gun.spin == orig_value

        # Test invalid spin state (2)
        self.gun.spin = 2
        self.check_motor_gpios(orig_value)

        assert self.gun.spin == orig_value


class TestFire(TestWheelGun):

    """Test function for firing the WheelGun."""

    def setUp(self):
        """Call parent to build simulation hardware and WheelGun."""
        super(TestFire, self).setUp()

    def tearDown(self):
        """Call parent to restore testing flag in config."""
        super(TestFire, self).tearDown()

    def check_trigger_gpios(self, value):
        """Helper method to check trigger GPIO values.

        :param value: Value that GPIOs should be set to.

        """
        assert int(self.get_gpio(
            self.config['gun']['trigger_gpios']['retract'])
            ['value']) == value
        assert int(self.get_gpio(
            self.config['gun']['trigger_gpios']['advance'])
            ['value']) == value

    def test_fire_normal(self):
        """Test firing function with default params."""
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        result = self.gun.fire()
        assert result is True
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)

    def test_fire_invalid_trigger_duration(self):
        """Test invalid time to advance/retract trigger."""
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        # Test invalid trigger duration (negative)
        result = self.gun.fire(advance_duration=-0.5)
        assert result is False
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)

        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        # Test excessive trigger duration (more than max)
        result = self.gun.fire(retract_duration=(
            float(self.config['gun']['max_trigger_duration']) + 1.0))
        assert result is True  # should still work with clamped duration
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)

    def test_fire_invalid_delay(self):
        """Test invalid delay (between advancing/retracting trigger)."""
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        # Test invalid delay (negative)
        result = self.gun.fire(delay=-3.0)
        assert result is False
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)


class TestFireBurst(TestWheelGun):

    """Test method for firing a burst of darts."""

    def setUp(self):
        """Call parent to build simulation hardware and WheelGun."""
        super(TestFireBurst, self).setUp()

    def tearDown(self):
        """Call parent to restore testing flag in config."""
        super(TestFireBurst, self).tearDown()

    def check_trigger_gpios(self, value):
        """Helper method to check trigger GPIO values.

        :param value: Value that GPIOs should be set to.

        """
        assert int(self.get_gpio(
            self.config['gun']['trigger_gpios']['retract'])
            ['value']) == value
        assert int(self.get_gpio(
            self.config['gun']['trigger_gpios']['advance'])
            ['value']) == value

    def test_fire_burst_normal(self):
        """Test firing burst of darts with default params."""
        result = self.gun.fire_burst()
        assert result is True

    def test_fire_burst_invalid(self):
        """Test firing a burst of darts with invalid params."""
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        # Test invalid count (negative)
        result = self.gun.fire_burst(count=-2)
        assert result is False
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)

        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)
        # Test invalid delay (negative)
        result = self.gun.fire(delay=-1.0)
        assert result is False
        # GPIOs should be zero before/after firing
        self.check_trigger_gpios(0)


@unittest.skip("Not yet implemented")
class TestWheelSpeed(test_bot.TestBot):

    """Test updating wheel rotation speed."""

    def setUp(self):
        """Setup test hardware files and build wheel gunner object."""
        # Run general bot test setup
        super(TestUpdateRotateSpeed, self).setUp()

        # Build wheel gunner
        self.wg = wg_mod.WheelGunner()

    def tearDown(self):
        """Restore testing flag state in config file."""
        # Run general bot test tear down
        super(TestUpdateRotateSpeed, self).tearDown()

    def test_off(self):
        """Test zero wheel rotation."""
        self.wg.wheel_speed = 0
        assert self.wg.wheel_speed == 0

    def test_full(self):
        """Test turning the wheels to 100% duty cycle."""
        self.wg.wheel_speed = 100
        assert self.wg.wheel_speed == 100

    def test_half(self):
        """Test the wheels at half speed."""
        self.wg.wheel_speed = 50
        assert self.wg.wheel_speed == 50

    def test_accel(self):
        """Test a series of increasing speeds."""
        for speed in range(0, 100, 10):
            self.wg.wheel_speed = speed
            assert self.wg.wheel_speed == speed

    def test_manually_confirm(self):
        """Test a series of random speeds, read the simulated HW to confirm."""
        # TODO: Update to work with capes
        return

    def test_over_max(self):
        """Test speed over max speed. Should use maximum."""
        with self.assertRaises(AssertionError):
            self.wg.wheel_speed = 101

    def test_under_min(self):
        """Test speed under minimum speed. Should use minimum."""
        with self.assertRaises(AssertionError):
            self.wg.wheel_speed = -1