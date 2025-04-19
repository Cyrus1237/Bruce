from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ACCELEROMETER
from adafruit_bno08x import BNO_REPORT_GYROSCOPE
import board
import busio
import numpy as np
import os
import pickle

from queue import Queue
from threading import Thread
import time


# TODO filter spikes
class Imu:
    def __init__(
        self, sampling_freq, calibrate=True, upside_down=True, user_pitch_bias=0
    ):
        self.sampling_freq = sampling_freq
        self.calibrate = calibrate

        i2c = busio.I2C(board.SCL, board.SDA)
        self.imu = BNO08X_I2C(i2c, address=0x4B)

        self.imu.enable_feature(BNO_REPORT_ACCELEROMETER)
        self.imu.enable_feature(BNO_REPORT_GYROSCOPE)

        if self.calibrate:
            self.imu.begin_calibration()

        self.last_imu_data = [0, 0, 0, 0]
        self.last_imu_data = {
            "gyro": [0, 0, 0],
            "accelero": [0, 0, 0],
        }
        self.imu_queue = Queue(maxsize=1)
        Thread(target=self.imu_worker, daemon=True).start()

    def imu_worker(self):
        while True:
            s = time.time()
            try:
                gyro = np.array(self.imu.gyro).copy()
                accelero = np.array(self.imu.acceleration).copy()
            except Exception as e:
                print("[IMU]:", e)
                continue

            if gyro is None or accelero is None:
                continue

            if gyro.any() is None or accelero.any() is None:
                continue

            data = {
                "gyro": gyro,
                "accelero": accelero,
            }

            self.imu_queue.put(data)
            took = time.time() - s
            time.sleep(max(0, 1 / self.sampling_freq - took))

    def get_data(self):
        try:
            self.last_imu_data = self.imu_queue.get(False)  # non blocking
        except Exception:
            pass

        return self.last_imu_data


if __name__ == "__main__":
    imu = Imu(50, upside_down=False)
    while True:
        data = imu.get_data()
        # print(data)
        print("gyro", np.around(data["gyro"], 3))
        print("accelero", np.around(data["accelero"], 3))
        print("---")
        time.sleep(1 / 25)