from hub import port, motion_sensor
import color_sensor
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

class Drivebase:
    def __init__(self):
        self.fL = port.C
        self.fR = port.A
        self.bR = port.D
        self.bL = port.F
        return

    def move(self, deg:int, speed:int=1110):
        deg += 45
        rad = radians(deg)
        sinMult = sin(rad)
        cosMult = cos(rad)
        intensityMult = 1/max(abs(sinMult), abs(cosMult))
        sinMult = sinMult*intensityMult
        cosMult = cosMult*intensityMult

        if sinMult > 1:
            sinMult = 1
        if cosMult > 1:
            cosMult = 1
        if sinMult < -1:
            sinMult = -1
        if cosMult < -1:
            cosMult = -1

        sinMult = round(sinMult, 4)
        cosMult = round(cosMult, 4)

        motor.run(self.fL, int(speed*-1*sinMult))
        motor.run(self.fR, int(speed*cosMult))
        motor.run(self.bR, int(speed*sinMult))
        motor.run(self.bL, int(speed*-1*cosMult))
        
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
        
        runloop.sleep_ms(10)
            

runloop.run(main())
