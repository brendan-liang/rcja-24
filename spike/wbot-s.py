from hub import port, motion_sensor, light_matrix
from app import display
import color_sensor
import distance_sensor
import motor
import runloop
from math import sin, cos, radians, copysign

import os
import json
import time

def within_angle(start, angle, end): # Only values from 0 to 360
    angle = angle or 360
    start = start or 360
    end = end or 360
    if start < end:
        return start <= angle <= end
    else:
        return not (end < angle < start)

class FileSystem:
    def __init__(self, path="../../config/wbot"):
        self.path = path
        return

    def dump(self, path, obj):
        json.dump(obj, self.path + path)

    def load(self, path):
        json.load(self.path + path)

class Sensors:
    def __init__(self, lenPrev:int = 6):
        self.ir = port.D
        self.usR = port.E
        # Sensor smoothing (store previous values)
        self.lenPrev = lenPrev
        self.prevIRdirs = [0] * lenPrev
        self.prevIRstrs = [0] * lenPrev
        return

    def addToStack(self, val, stack:list, max_len:int|None=None):
        max_len = max_len or self.lenPrev
        stack.append(val)
        if len(stack) > max_len:
            stack.pop(0)
        return stack

    def getIR(self):
        vals = color_sensor.rgbi(self.ir)

        # # Sensor smoothing IR DIR
        # self.prevIRdirs = self.addToStack(vals[2], self.prevIRdirs)
        # irDir = sum(sorted(self.prevIRdirs)[4:6])//2
        irDir = vals[2]

        # Sensor smoothing IR STR
        self.prevIRstrs = self.addToStack(vals[0], self.prevIRstrs)
        irStr = sum(sorted(self.prevIRstrs)[4:6])//2

        # Calculate return value
        if not irStr:
            return (0, 0)
        return (irDir or 360, irStr)

    def getUS(self):
        """Get Ultrasonic distance in millimetres"""
        return distance_sensor.distance(self.usR)

clamp = lambda low, x, high: max(low, min(x, high))
class Drivebase:
    def __init__(self):
        self.fL = port.B
        self.fR = port.A
        self.bR = port.C
        self.bL = port.F
        self.motors = [self.fL, self.fR, self.bR, self.bL]
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
        # Maximise and apply yaw adjustment if bot is not facing forward

        if abs(yawAdjust) >= 0.025:
            motorSpeeds = [int(spd - yawAdjust*(speed/(2*yawAdjustMax))) for spd in motorSpeeds]
        # Apply movements

        for i in range(4):
            motor.run(self.motors[i], motorSpeeds[i])

class HubDisplay: # May add to?
    clockDirImages = {
        0: light_matrix.IMAGE_SQUARE_SMALL,
        1: light_matrix.IMAGE_CLOCK5,
        2: light_matrix.IMAGE_CLOCK7,
        3: light_matrix.IMAGE_ARROW_SW,
        4: light_matrix.IMAGE_CLOCK8,
        5: light_matrix.IMAGE_CLOCK10,
        6: light_matrix.IMAGE_ARROW_NW,
        7: light_matrix.IMAGE_CLOCK11,
        8: light_matrix.IMAGE_CLOCK1,
        9: light_matrix.IMAGE_ARROW_NE,
        10: light_matrix.IMAGE_CLOCK2,
        11: light_matrix.IMAGE_CLOCK4,
        12: light_matrix.IMAGE_ARROW_SE,
    }

    def pointDirection(self, dir: int):
        clockDir = dir // 30
        if dir:
            light_matrix.show_image(eval("light_matrix.IMAGE_CLOCK" + str(clockDir)))
        else:
            light_matrix.show_image(light_matrix.IMAGE_SQUARE_SMALL)

    def showChar(self, char: str):
        light_matrix.write(char[0])

async def main():
    motion_sensor.reset_yaw(0)
    drive = Drivebase()
    sensors = Sensors()
    hubdisp = HubDisplay()
    fs = FileSystem()

    while 1:
        ir, irStr = sensors.getIR()
        display.text(str(ir) + " " + str(irStr))
        if not ir:
            drive.move(180)
            hubdisp.pointDirection(0)
        # elif 330 <= ir <= 360 or 0 < ir < 30:
        elif within_angle(330, ir, 30):
            drive.move(ir*2)
            hubdisp.pointDirection(ir)
        else:
            direction = int(ir + copysign(irStr, 180 - ir)*0.3)
            drive.move(direction)
            hubdisp.pointDirection(direction)
            #drive.move(int(ir + copysign(max(1.066**irStr - 0.28, 0), 180 - ir)*0.5))

runloop.run(main())