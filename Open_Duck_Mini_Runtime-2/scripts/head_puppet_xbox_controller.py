"""
Sets up the robot in init position, you control the head with the xbox controller
"""

import time
import numpy as np

import pygame

from mini_bdx_runtime.rustypot_position_hwi import HWI
from mini_bdx_runtime.eyes import Eyes
from mini_bdx_runtime.antennas import Antennas
from mini_bdx_runtime.projector import Projector

# Import the new controller
from mini_bdx_runtime.xbox_controller import XBoxController

# Initialize hardware
hwi = HWI()
hwi.set_kps([8]*14)
hwi.set_kds([0]*14)
# hwi.turn_on()

eyes = Eyes()
antennas = Antennas()
projector = Projector()

# Create XBoxController with standing=True so it uses head_control_mode
controller = XBoxController(command_freq=60, standing=True)

while True:
    # Grab the latest commands and button states from the XBox controller
    (
        last_commands,
        A_pressed,
        B_pressed,
        X_pressed,
        Y_pressed,
        LB_pressed,
        RB_pressed,
        left_trigger,
        right_trigger,
        up_down
    ) = controller.get_last_command()

    # In head_control_mode, last_commands[3..6] map to neck_pitch, head_pitch, head_yaw, head_roll
    neck_pitch = last_commands[3]
    head_pitch = last_commands[4]
    head_yaw   = last_commands[5]
    head_roll  = last_commands[6]

    # Drive your robot’s head joints. (Here, they’re assumed to accept radians directly.)
    hwi.set_position("neck_pitch", neck_pitch)
    hwi.set_position("head_pitch", head_pitch)
    hwi.set_position("head_yaw", head_yaw)
    hwi.set_position("head_roll", head_roll)

    # Use the triggers to control the antennas
    antennas.set_position_left(right_trigger)
    antennas.set_position_right(left_trigger)

    # Example button usage
    if A_pressed:
        projector.switch()

    time.sleep(1/60)
