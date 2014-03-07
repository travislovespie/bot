"""Logic for line following."""

import sys
from time import time
import numpy as np

import lib.lib as lib
import hardware.ir_hub as ir_hub_mod
import driver.mec_driver as mec_driver_mod
import pid as pid_mod


class Follower(object):

    """Follows a line, detects intersections and stop conditions."""

    def __init__(self):
        # Build logger
        self.logger = lib.get_logger()

        # Build subsystems
        self.ir_hub = ir_hub_mod.IRHub()
        self.driver = mec_driver_mod.MecDriver()

        # Build PIDs
        self.front_pid = pid_mod.PID()
        self.front_error = 0.0
        self.back_pid = pid_mod.PID()
        self.back_error = 0.0
        self.error = 0.0

        # Initialize other members
        # IR position values, e.g. [-8.0, -7.0 ..., 8.0]
        self.ir_pos = dict()
        # IR aggregate values = sum(ir_pos * readings) / sum(readings)
        self.ir_agg = dict()
        for name, reading in self.ir_hub.reading.iteritems():
            self.ir_pos[name] = np.float32(np.linspace(
                -(len(reading) / 2), (len(reading) / 2), len(reading)))
            # TODO(napratin,3/4): Ensure proper ordering?
            self.ir_agg[name] = None  # None when no unit is lit
            self.logger.debug("ir_pos['{}'] = {}"
                .format(name, self.ir_pos[name]))

        self.intersection = False
        self.lost_line = False
        self.timeLastUpdated = -1.0

    @lib.api_call
    def update(self):
        """Read IR values, compute aggregates."""
        ir_readings = self.ir_hub.read_binary(60)
        for name, reading in ir_readings.iteritems():
            reading_arr = np.int_(reading)  # convert readings to numpy array
            reading_sum = np.sum(np_reading)  # = no. of units lit
            if reading_sum > 0:
                self.ir_agg[name] = (np.sum(self.ir_pos * reading_arr)
                                    / reading_sum)
            else:
                self.ir_agg[name] = None
        self.timeLastUpdated = time.time()
    
    @lib.api_call
    def get_ir_agg(self):
        """Return IR aggregates, i.e. sum(pos * readings) / sum(readings)."""
        return self.ir_agg

    @lib.api_call
    def get_front_error(self):
        return self.front_error

    @lib.api_call
    def get_back_error(self):
        return self.back_error

    @lib.api_call
    def is_start(self):
        return True  # TODO: Use color sensor

    @lib.api_call
    def is_on_line(self):
        return (not self.lost_line)  # TODO: Use IR sensors to perform check

    @lib.api_call
    def is_on_x(self):
        return self.intersection  # TODO: Use IR sensors to perform check

    @lib.api_call
    def is_on_blue(self):
        return True  # TODO: Use color sensor

    @lib.api_call
    def is_on_red(self):
        return True  # TODO: Use color sensor

    @lib.api_call
    def is_end_of_line(self):
        return False  # TODO: Use IR sensors (only one array sees the line?)

    @lib.api_call
    def follow(self, heading):
        """Follow line along given heading"""
        # Get the initial condition
        previous_time = time()
        # Init front_PID
        self.front_pid.set_k_values(1, 0, 0)
        # Inti back_PID
        self.back_pid.set_k_values(1, 0, 0)
        # Get current heading
        self.heading = heading
        # Continue until an error condition
        while True:
            # Assign the current states to the correct heading
            self.logger.info("time in {}").format(time()))
            self.assign_states()
            self.logger.info("time out {}".format(time()))
            # Check for error conditions
            if self.error != 0:
                self.update_exit_state()
                self.logger.warning(self.error)
                self.logger.warning(self.front_state)
                self.logger.warning(self.back_state)
                self.driver.move(0,0)
                return
            # Get the current time of the CPU
            current_time = time()
            # Call front PID
            self.sampling_time = current_time - previous_time
            # Call front PID
            self.front_error = self.front_pid.pid(
                0, self.front_state, self.sampling_time)
            # Call back PID
            self.back_error = self.back_pid.pid(
                0, self.back_state, self.sampling_time)
            # Update motors
            self.motors(self.front_error, self.back_error)
            # Take the current time set it equal to the previous time
            previous_time = current_time

    @lib.api_call
    def center_on_x(self):
        return True  # TODO: Actually center on intersection

    @lib.api_call
    def center_on_blue(self):
        return True  # TODO: Actually center on blue block

    @lib.api_call
    def center_on_red(self):
        return True  # TODO: Actually center on red_block

    @lib.api_call
    def oscillate(self, heading, osc_time=1):
        """Oscillate sideways, increasing in amplitude until line is found"""

        # Time in seconds for which bot oscillates in each direction.
        # Speed at which the bot is oscillating.
        # Increase in speed after each oscillation cycle.
        # Todo(Ahmed): Find reasonable constants.
        osc_speed = 10
        osc_increment = 10

        # The oscillation directions, perpendicular to parameter "heading"
        angle1 = heading + 90
        angle2 = heading - 90
        self.logger.debug(
            "Pre-correction angles: angle1: {}, angle2: {}".format(
                angle1, angle2))

        # Correct angles to fit bounds.
        angle1 %= self.driver.max_angle
        angle2 %= self.driver.max_angle
        self.logger.debug(
            "Post-correction angles: angle1: {}, angle2: {}".format(
                angle1, angle2))

        # Test headings for valid 0,360 values.
        assert 0 <= angle1 <= 360, "angle1 is {}".format(angle1)
        assert 0 <= angle2 <= 360, "angle2 is {}".format(angle2)

        # Todo: Consider making this a function call.
        line_not_found = True
        while line_not_found:

            # Drives in each direction.
            self.driver.move(osc_speed, angle1)
            # Passes control to find line, which moves
            # until it finds line or runs out of time.
            # Note: watch_for_line returns "line_found"
            # (bool) and "time_elapsed" (int)
            results = self.watch_for_line(osc_time)
            self.driver.move(0, 0)

            if results["line_found"]:
                line_not_found = False

            # Search in other direction.
            self.driver.move(osc_speed, angle2)

            # "time elapsed" is used as max_time for more precise movements.
            results = self.watch_for_line(results["time_elapsed"] * 2)
            self.logger.debug(
                "Oscillation direction 1: osc_speed: {}, heading: {}".format(
                    osc_speed, heading))
            self.driver.move(0, 0)

            if results["line_found"]:
                line_not_found = False

            # If line is not found, Continue looping until line is found.
            # For now, stop when max speed is hit.
            osc_speed += 90
            if osc_speed >= self.driver.max_speed:
                line_not_found = False

    def reading_contains_pattern(self, pattern, reading):
        """Search the given reading for the given pattern.

        :param pattern: Pattern to search reading for.
        For example, [1, 1] for a pair of consecutive ones.
        :type pattern: list
        :param reading: IR array reading to search for the
        given pattern. Should contain only 0s and 1s.
        :type reading: list
        :returns: True if the pattern is in the reading, False otherwise.

        """
        return "".join(map(str, pattern)) in "".join(map(str, reading))

    def watch_for_line(self, max_time):
        """Recieves time period for which to continuously watch for line.
        Returns True when line is found.
        Returns False if line is not found before time is hit.
        """
        start_time = time()
        while True:
            reading = self.ir_hub.read_all()
            for name, array in reading.iteritems():
                if self.reading_contains_pattern([1, 1], array):
                    return {"line_found": True,
                            "time_elapsed": time() - start_time}
                if time() - start_time > max_time:
                    return {"line_found": False,
                            "time_elapsed": time() - start_time}

    def assign_states(self, current_ir_reading=None):
        """Take 4x16 bit arrays and assigns the array to proper orientations.

        Note that the proper orientations are front, back, left and right.

        """
        # Get the current IR readings
        if current_ir_reading is None:
            current_ir_reading = self.ir_hub.read_binary(60)
        # Heading west
        if self.heading == 0:
            # Forward is on the left side
            self.front_state = self.get_position_lr(
                current_ir_reading["left"])
            # Back is on the right side
            self.back_state = self.get_position_rl(
                current_ir_reading["right"])
            # Left is on the back
            self.left_state = self.get_position_lr(
                current_ir_reading["back"])
            # Right is on the front
            self.right_state = self.get_position_rl(
                current_ir_reading["front"])
        # Heading east
        elif self.heading == 180:
            # Forward is on the right side
            self.front_state = self.get_position_lr(
                current_ir_reading["right"])
            # Back is on the left side
            self.back_state = self.get_position_rl(
                current_ir_reading["left"])
            # Left is on the front
            self.left_state = self.get_position_lr(
                current_ir_reading["front"])
            # Right is on the back
            self.right_state = self.get_position_rl(
                current_ir_reading["back"])
        # Heading south
        elif self.heading == 270:
            # Forward is on the front side
            self.front_state = self.get_position_lr(
                current_ir_reading["front"])
            # Back is on the back side
            self.back_state = self.get_position_rl(
                current_ir_reading["back"])
            # Left is on the left
            self.left_state = self.get_position_lr(
                current_ir_reading["left"])
            # right is on the right
            self.right_state = self.get_position_rl(
                current_ir_reading["right"])
            # Heading north
        elif self.heading == 90:
            # Forward is on the right side
            self.front_state = self.get_position_lr(
                current_ir_reading["back"])
            # Back is on the left side
            self.back_state = self.get_position_rl(
                current_ir_reading["front"])
            # Left is on the front
            self.left_state = self.get_position_lr(
                current_ir_reading["right"])
            # Right is on the back
            self.right_state = self.get_position_rl(
                current_ir_reading["left"])
        if((self.front_state > 15) or (self.back_state > 15) or
            (self.right_state < 16) or (self.left_state < 16)):
            if((self.right_state < 16) or (self.left_state < 16) or 
                (self.front_state == 17) or (self.back_state == 17)):
                # Found Intersection
                self.error = 1
            elif((self.back_state == 18) or (self.front_state == 18)):
                # at high angle
                self.error = 5
            elif((self.front_state == 16) and (self.back_state == 16)):
                # Front and back lost line
                self.error = 2
            elif(self.front_state == 16):
                # Front lost line
                self.error = 3
            elif(self.back_state == 16):
                # Back lost line
                self.error = 4
        else:
            self.error = 0

    def update_exit_state(self):
        if(self.error == 1):
            self.intersection = True
        elif(self.error == 2):
            self.lost_line = True
        elif(self.error == 3):
            self.lost_line = True
        elif(self.error == 4):
            self.lost_line = True
        elif(self.error == 5):
            self.lost_line = True

    def get_position_lr(self, readings):
        """Reading the IR sensors from left to right.

        Calculates the current state in reference to center from 
        left to right. States go form -15 to 15.

        """
        self.hit_position = []
        state = 0.0
        for index, value in enumerate(readings):
            if(value == 1):
               self.hit_position.append(index)
        if len(self.hit_position) > 4:
            # Error: Intersection detected
            return 17
        if len(self.hit_position) == 0:
            # Error: No line detected
            return 16
        if len(self.hit_position) == 4:
            # Error: Bot at large error
            return 18
        state = self.hit_position[0] * 2
        if len(self.hit_position) > 1:
            if self.hit_position[1] > 0:
                state = state + 1
            if abs(self.hit_position[0] - self.hit_position[1]) > 1:
                # Error: Discontinuity in sensors
                return 19
        state = state - 15
        return state

    def get_position_rl(self, readings):
        """Reading the IR sensors from right to left.

        Calculates the current state in reference to center from 
        right to left. States go form -15 to 15.

        """
        self.hit_position = []
        state = 0.0
        for index, value in enumerate(readings):
            if(value == 1):
               self.hit_position.append(index)
        if len(self.hit_position) > 4:
            # Error: Intersection detected
            return 17
        if len(self.hit_position) == 0:
            # Error: No line detected
            return 16
        if len(self.hit_position) == 4:
            # Error: Bot at large error
            return 18
        state = self.hit_position[0] * 2
        if len(self.hit_position) > 1:
            if(self.hit_position[1] > 0):
                state = state + 1
            if(abs(self.hit_position[0] - self.hit_position[1]) > 1):
                # Error: Discontinuity in sensors
                return 19
        state = (state - 15) * -1
        return state

    @lib.api_call
    def motors(self, front_error, back_error):
        """Used to update the motors speed and angular motion."""
        # Calculate translate_speed
        # MAX speed - error in the front sensor / total number
        # of states
        translate_speed =  80 - ( front_error / 16 )
        # Calculate rotate_speed
        # Max speed - Translate speed
        rotate_speed = 100 - translate_speed
        # Calculate translate_angle
        translate_angle = back_error * (180 / 16)
        self.logger.info("pre translate_angle = {}, time {}  ".format(translate_angle,time()))
        if translate_angle < 0:
            # Swift to the left
            translate_angle = 360 + translate_angle
        else:
            # swift to the right
            translate_angle = translate_angle   
        if translate_speed > 100:
            # If translate_speed is greater than 100 set to 100
            translate_speed = 100
        elif translate_speed < 0:
            # If translate_speed is greater than 100 set to 100
            translate_speed = 0
        if rotate_speed > 100:
            # If rotate_speed is greater than 100 set to 100
            rotate_speed = 100
        elif rotate_speed < 0:
            # If rotate_speed is greater than 100 set to 100
            rotate_speed = 0
        # Adjust motor speeds
        self.logger.info("post translate_angle = {}  ".format(translate_angle))
        self.driver.move(translate_speed, translate_angle) 
        #self.driver.compound_move(
        #    translate_speed, translate_angle, rotate_speed)
