from abc import update_abstractmethods
import pygame
from threading import Thread
from queue import Queue
import time
import numpy as np

X_RANGE = [-0.15, 0.15]
Y_RANGE = [-0.2, 0.2]
YAW_RANGE = [-1.0, 1.0]

# rads
NECK_PITCH_RANGE = [-0.8, 0.07]
HEAD_PITCH_RANGE = [-1.4, 0.8]
HEAD_YAW_RANGE = [-1.1, 1.1]
HEAD_ROLL_RANGE = [-0.45, 0.45]

# How quickly joystick movement accumulates in radians
# Tweak these for faster/slower relative changes
NECK_PITCH_SPEED = 0.02
HEAD_PITCH_SPEED = 0.02
HEAD_YAW_SPEED   = 0.02
HEAD_ROLL_SPEED  = 0.02

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def apply_deadzone(value, threshold=0.05):
    return value if abs(value) > threshold else 0.0

class XBoxController:
    def __init__(self, command_freq, standing=False):
        self.command_freq = command_freq
        self.standing = standing
        self.head_control_mode = self.standing

        # For walking: [vx, vy, omega], for head: [neck_pitch, head_pitch, head_yaw, head_roll]
        self.last_commands = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Keep track of each head joint angle *internally* for relative control
        self.neck_pitch = -0.4  # Start roughly mid-range, e.g. ~0.7 rad
        self.head_pitch = -0.7
        self.head_yaw   = 0.0
        self.head_roll  = 0.0

        self.last_left_trigger = 0.0
        self.last_right_trigger = 0.0
        pygame.init()
        self.p1 = pygame.joystick.Joystick(0)
        self.p1.init()
        print(f"Loaded joystick with {self.p1.get_numaxes()} axes.")
        self.cmd_queue = Queue(maxsize=1)

        self.A_pressed = False
        self.B_pressed = False
        self.X_pressed = False
        self.Y_pressed = False
        self.LB_pressed = False
        self.RB_pressed = False

        Thread(target=self.commands_worker, daemon=True).start()

    def commands_worker(self):
        while True:
            self.cmd_queue.put(self.get_commands())
            time.sleep(1 / self.command_freq)

    def get_commands(self):
        last_commands = self.last_commands
        left_trigger = self.last_left_trigger
        right_trigger = self.last_right_trigger

        # Read raw joystick axes
        l_x = -1 * self.p1.get_axis(0)
        l_y = -1 * self.p1.get_axis(1)
        r_x = -1 * self.p1.get_axis(2)
        r_y = -1 * self.p1.get_axis(3)

        # Read triggers
        right_trigger = np.around((self.p1.get_axis(4) + 1) / 2, 3)
        left_trigger  = np.around((self.p1.get_axis(5) + 1) / 2, 3)
        if left_trigger < 0.1:
            left_trigger = 0
        if right_trigger < 0.1:
            right_trigger = 0

        if not self.head_control_mode:
            # Normal walking mode
            lin_vel_y = l_x
            lin_vel_x = l_y
            ang_vel   = r_x

            # Scale by X/Y/Yaw range
            lin_vel_x *= np.abs(X_RANGE[1] if lin_vel_x >= 0 else X_RANGE[0])
            lin_vel_y *= np.abs(Y_RANGE[1] if lin_vel_y >= 0 else Y_RANGE[0])
            ang_vel   *= np.abs(YAW_RANGE[1] if ang_vel >= 0 else YAW_RANGE[0])

            last_commands[0] = lin_vel_x
            last_commands[1] = lin_vel_y
            last_commands[2] = ang_vel


        else:
            # Head control mode =>  zero out walking
            last_commands[0] = 0.0
            last_commands[1] = 0.0
            last_commands[2] = 0.0
            last_commands[3] = 0.0

            # Instead of directly setting angles from the joystick, we *add*
            # small increments or decrements. This is what makes it "relative."
            self.neck_pitch += apply_deadzone(-r_y) * NECK_PITCH_SPEED
            self.head_pitch += apply_deadzone(l_y) * HEAD_PITCH_SPEED
            self.head_yaw   += apply_deadzone(-l_x) * HEAD_YAW_SPEED
            self.head_roll  += apply_deadzone(r_x) * HEAD_ROLL_SPEED

            # Clamp each angle to its allowed range
            self.neck_pitch = clamp(self.neck_pitch, NECK_PITCH_RANGE[0], NECK_PITCH_RANGE[1])
            self.head_pitch = clamp(self.head_pitch, HEAD_PITCH_RANGE[0], HEAD_PITCH_RANGE[1])
            self.head_yaw   = clamp(self.head_yaw,   HEAD_YAW_RANGE[0],   HEAD_YAW_RANGE[1])
            self.head_roll  = clamp(self.head_roll,  HEAD_ROLL_RANGE[0],  HEAD_ROLL_RANGE[1])

            # Now fill them into last_commands so downstream code sees them
            last_commands[3] = self.neck_pitch
            last_commands[4] = self.head_pitch
            last_commands[5] = self.head_yaw
            last_commands[6] = self.head_roll

        # Handle button events
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if self.p1.get_button(0):  # A
                    self.A_pressed = True
                if self.p1.get_button(1):  # B
                    self.B_pressed = True
                if self.p1.get_button(3):  # X
                    self.X_pressed = True
                if self.p1.get_button(4):  # Y
                    self.Y_pressed = True
                    self.head_control_mode = not self.head_control_mode
                if self.p1.get_button(6):  # LB
                    self.LB_pressed = True
                if self.p1.get_button(7):  # RB
                    self.RB_pressed = True

            if event.type == pygame.JOYBUTTONUP:
                self.A_pressed = False
                self.B_pressed = False
                self.X_pressed = False
                self.Y_pressed = False
                self.LB_pressed = False
                self.RB_pressed = False

        up_down = self.p1.get_hat(0)[1]
        pygame.event.pump()  # process event queue

        return (
            np.around(last_commands, 3),
            self.A_pressed,
            self.B_pressed,
            self.X_pressed,
            self.Y_pressed,
            self.LB_pressed,
            self.RB_pressed,
            left_trigger,
            right_trigger,
            up_down
        )

    def get_last_command(self):
        # Non-blocking queue read
        A_pressed = False
        B_pressed = False
        X_pressed = False
        Y_pressed = False
        LB_pressed = False
        RB_pressed = False
        up_down = 0

        try:
            (
                self.last_commands,
                A_pressed,
                B_pressed,
                X_pressed,
                Y_pressed,
                LB_pressed,
                RB_pressed,
                self.last_left_trigger,
                self.last_right_trigger,
                up_down
            ) = self.cmd_queue.get(False)  # non-blocking
        except Exception:
            pass

        return (
            self.last_commands,
            A_pressed,
            B_pressed,
            X_pressed,
            Y_pressed,
            LB_pressed,
            RB_pressed,
            self.last_left_trigger,
            self.last_right_trigger,
            up_down
        )


if __name__ == "__main__":
    controller = XBoxController(20, standing=True)
    while True:
        print(controller.get_last_command())
        time.sleep(0.05)
