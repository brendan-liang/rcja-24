from hub import port, motion_sensor
from app import display
import color_sensor
import distance_sensor
import motor
import runloop
from math import sin, cos, radians

import os
import json
import time

class FileSystem:
    def __init__(self, path="../../config/wbot"):
        self.path = path
        return

    def dump(self, path, obj):
        json.dump(obj, self.path + path)

    def load(self, path):
        json.load(self.path + path)

class Sensors:
    def __init__(self):
        self.ir = port.E
        self.usR = port.B
        return

    def getIR(self):
        vals = color_sensor.rgbi(self.ir)
        if not vals[0]:
            return 0
        ir = vals[2]
        return ir if ir else 360

    def getUS(self):
        """Get Ultrasonic distance in millimetres"""
        return distance_sensor.distance(self.usR)

clamp = lambda low, x, high: max(low, min(x, high))
class Drivebase:
    def __init__(self):
        self.fL = port.C
        self.fR = port.A
        self.bR = port.D
        self.bL = port.F
        self.motors = [port.C, port.A, port.D, port.F]
        return

    def move(self, deg:int, speed:int=1110, yaw:int|None=None):
        yaw = int(yaw/10) if yaw else int(motion_sensor.tilt_angles()[0]/10)
        deg += 45
        rad = radians(deg)
        sinMult = sin(rad)
        cosMult = cos(rad)
        motorSpeeds = [-sinMult, cosMult, sinMult, -cosMult] # fL, fR, bR, bL

        # Maximise efficiency
        speedMult = speed/(max([abs(i) for i in motorSpeeds]))
        motorSpeeds = [int(spd * speedMult) for spd in motorSpeeds]
        # Add yaw adjustment (orientation correction)

        yawAdjustDivisor = 200
        yawAdjustMax = 0.3
        yawAdjust = clamp(-yawAdjustMax, yaw/yawAdjustDivisor, yawAdjustMax)
        display.text(str(yawAdjust))
        # Maximise and apply yaw adjustment if bot is not facing forward

        if abs(yawAdjust) >= 0.025:
            motorSpeeds = [int(spd - yawAdjust*(speed/(2*yawAdjustMax))) for spd in motorSpeeds]
        # Apply movements

        for i in range(4):
            motor.run(self.motors[i], motorSpeeds[i])
async def main():
    drive = Drivebase()
    sensors = Sensors()
    fs = FileSystem()

    while 1:
        ir = sensors.getIR()
        if ir:
            drive.move(ir)
        else:
            # return to goal
            drive.move(180)
            # recentre

runloop.run(main())
