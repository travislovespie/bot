import time

import bot.lib.lib as lib
import bot.hardware.servo as servo_mod
import bbb.gpio as gpio_mod

    
START_POSITION = 210
SOLVE_POSITION = 17
CLAMP_TIME = 3.7 
HALF_CLAMP = int(CLAMP_TIME/2)

class RubiksSolver(object):
    
    
    def __init__(self):
        
        self.config = lib.get_config()
        self.logger = lib.get_logger()

        self.servo_pwm = self.config["rubiks"]["servo_pwm"]
        
        self.rev_num   = self.config["rubiks"]["GPIO"]["REV"]
        self.fwd_num   = self.config["rubiks"]["GPIO"]["FWD"]
        self.pwr_num   = self.config["rubiks"]["GPIO"]["PWR"]
        
        # Build servo that controlls gripper that turns cube.
        self.gripper = servo_mod.Servo(self.servo_pwm)

        # Set to starting position
        self.gripper.position = START_POSITION

        # gpio's that control motors of gripper.
        # Note: we're not using motor.py, it assumes strange hardware.
        # TODO(AhmedSamara): update motor.py to update standard hardware.
        self.rev = gpio_mod.GPIO(self.rev_num)
        self.fwd = gpio_mod.GPIO(self.fwd_num)
        self.pwr = gpio_mod.GPIO(self.pwr_num)
       
        # set directions
        self.pwr.output()
        self.fwd.output()
        self.rev.output()
         
        # set initial value
        self.pwr.set_value(0)
        self.fwd.set_value(0)
        self.rev.set_value(0)
         
    @lib.api_call
    def open_clamp(self):
        self.set_motor("rev")
        time.sleep(HALF_CLAMP)
        self.set_motor("off")

    @lib.api_call
    def close_clamp(self):
        """Turns both gpio's into "forward" position to close arm.
        
        Gripper is attached to L298N H-bridge controller. with I1, I2

        So when fwd=high, rev=low, moves forward.
        """

        
        self.set_motor("fwd")
        # pause while grippers close
        time.sleep(HALF_CLAMP)
        self.set_motor("off")        

    @lib.api_call
    def set_motor(self, dir="off"):
        """H bridge truth table
        fwd rev  direction
        0   0    off (stall?)
        0   1    reverse
        1   0    forward
        1   1    off (stall? short ckt?)
        """
        
        self.pwr.set_value(1)
              
        if dir=="fwd":
            self.fwd.set_value(1)
            self.rev.set_value(0)
            self.pwr.set_value(1)
        elif dir=="rev":
            self.fwd.set_value(0)
            self.rev.set_value(1)
            self.pwr.set_value(1)
        elif dir=="stall":
            # Note: not sure if this is safe.
            self.fwd.set_value(1)
            self.rev.set_value(1)
        elif dir=="off":
            self.fwd.set_value(0)
            self.rev.set_value(0)
            self.pwr.set_value(0)


    @lib.api_call
    def move_arm(self, position):
        """exists only to expose servo fncts to API"""
        self.gripper.position = position

    @lib.api_call
    def rubiks_test(self):
        self.gripper.test()

    @lib.api_call
    def solve(self):
        self.close_clamp()
        time.sleep(1)
        self.move_arm(SOLVE_POSITION)
        time.sleep(1)
        self.open_clamp()

    @lib.api_call
    def reset(self):
        self.open_clamp()
        self.move_arm(START_POSITION)
