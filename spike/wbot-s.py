from hub import port, motion_sensor, light_matrix, button, light
import color
from app import display
import color_sensor
import distance_sensor
import motor
import runloop
from math import sin, cos, radians, copysign

import time

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

    def dump(self, path, obj) -> None:
        with open(self.path + path, "w") as f:
            json.dump(obj, f)
        return

    def load(self, path) -> dict:
        with open(self.path + path, "a+") as f:
            return json.load(f)

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
        self.motorMoves = [[], [], [], []]
        return

    def stop(self) -> None:
        for i in self.motors:
            motor.stop(i)

    def clear(self) -> None:
        self.motorMoves = [[], [], [], []]

    def move(self, deg:int, speed:float=1, yaw:int|None=None):
        speed *= 1100
        deg += 45

        yaw = int(yaw/10) if yaw else int(motion_sensor.tilt_angles()[0]/10)
        rad = radians(deg)
        sinMult = sin(rad)
        cosMult = cos(rad)
        motorSpeeds = [-sinMult, cosMult, sinMult, -cosMult] # fL, fR, bR, bL

        # Maximise efficiency
        speedMult = speed/(max([abs(i) for i in motorSpeeds]))
        motorSpeeds = [int(spd * speedMult) for spd in motorSpeeds]

        for i in range(4):
            self.motorMoves[i].append(motorSpeeds[i])

    def yawAdjust(self, speed:float=0.8, yaw:int|None = None, yawThreshold:float=0.1, mult:float=2):
        speed *= 1100
        yaw = (motion_sensor.tilt_angles()[0]//10) if yaw == None else (yaw//10)

        yawAdjust = clamp(-1, (yaw/180)*mult, 1)
        if abs(yawAdjust) >= yawThreshold:
            for i in range(4):
                self.motorMoves[i].append(-yawAdjust*speed)
            return True
        return False

    def tickMotors(self, speed=1100, disabled=False, inverted:bool=False):
        if inverted:
            self.motorMoves = [[-1 * move for move in motor] for motor in self.motorMoves]
        
        multiplier = 1
        if len(self.motorMoves[0]) > 1:
            multiplier = speed // max([sum(i)//len(i) for i in self.motorMoves])
        
        if not disabled:
            motorMoves = []
            for i in self.motorMoves:
                if len(i):
                    motorMoves.append(sum(i)//len(i))

            for i in range(4):
                if not len(self.motorMoves[i]):
                    motor.stop(self.motors[i])
                    continue
                moveDir = sum(self.motorMoves[i])//len(self.motorMoves[i]) * multiplier

                if moveDir:
                    motor.run(self.motors[i], int(moveDir))
                else:
                    motor.stop(self.motors[i])


        self.motorMoves = [[], [], [], []]
        self.dirs = []

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
            light_matrix.show_image(eval("light_matrix.IMAGE_CLOCK" + str(clockDir or 12)))
        else:
            light_matrix.show_image(light_matrix.IMAGE_SQUARE_SMALL)

    def showChar(self, char: str):
        light_matrix.write(char[0])

CENTRE_RADIUS = 20

async def main():
    motion_sensor.reset_yaw(0)
    drive = Drivebase()
    sensors = Sensors()
    hubdisp = HubDisplay()
    fs = FileSystem()

    centre = sensors.getUS()

    settings = fs.load("setup.json")
    print(settings)

    lastPossFail = time.ticks_ms()
    possession = False

    lastUnderFail = time.ticks_ms()
    undershoot = False

    running = False

    while 1:
        if button.pressed(button.LEFT):
            while button.pressed(button.LEFT):
                pass
            running = not running
        if button.pressed(button.RIGHT):
            while button.pressed(button.RIGHT):
                pass
            running = not running
        
        if running:        
            lastIR = 180
            ir, irStr = sensors.getIR()
            us = sensors.getUS()

            movementTexts = []

            if ir:
                lastIR = ir

            # undershoot detection
            undershootConditions = (within_angle(290, ir, 340) or within_angle(20, ir, 70))

            if not undershootConditions:
                lastUnderFail = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), lastPossFail) > 250 and undershootConditions:
                undershoot = True
                light.color(light.CONNECT, color.AZURE)
            else:
                undershoot = False
                light.color(light.CONNECT, color.RED)

            # possession detection
            possessionConditions = (irStr > 75) and (within_angle(330, ir, 30))

            if not possessionConditions:
                lastPossFail = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), lastPossFail) > 500 and possessionConditions:
            # if True:
                possession = True
                light.color(light.POWER, color.AZURE)
            else:
                possession = False
                light.color(light.POWER, color.RED)

            movementTexts.append(str(possession))
            movementTexts.append(str(irStr))
            movementTexts.append(str(ir))

            # add ball movements

            if not ir:
                movementTexts.append("NOBALL")
                drive.move(lastIR)
                # add ultrasonic movements
                if us > centre + CENTRE_RADIUS:
                    drive.move(90)
                elif us < centre - CENTRE_RADIUS:
                    drive.move(-90)
            # elif 330 <= ir <= 360 or 0 < ir < 30:
            elif within_angle(330, ir, 30):
                movementTexts.append("BALLFRONT")
                # avoid undershooting
                if undershoot:
                    drive.move(ir * 2)
                else:
                    drive.move(ir)
            else:
                # Move around the ball
                movementTexts.append("BALLBACK")
                
                sign = copysign(1, 180 - ir)
                direction = int(ir + irStr*sign*(settings.get("strafespd") or 0.7))
                drive.move(direction)

            # goal maneuver
            if possession:
                possessionTime = time.ticks_diff(time.ticks_ms(), lastPossFail)
                drive.clear()
                drive.move(360)
                if us > centre + CENTRE_RADIUS:
                    drive.move(45)
                elif us < centre - CENTRE_RADIUS:
                    drive.move(-45)
                    
            # avoid undershooting
            if undershoot:
                drive.clear()
                drive.move(ir*2)

            # yaw adjustment

            if drive.yawAdjust():
                movementTexts.append("YAWADJUST")
            #display.text(str(int(copysign(90, us - centre))) + " " + str(us) + " " + str(centre))
            #drive.move(int(copysign(90, us - centre)), speed=clamp(-0.3, (us - centre)/100, 0.3))

            # apply movements

            hubdisp.pointDirection(ir)
            drive.tickMotors(inverted=settings.get("inverted", False))

            # output text

            outputText = ""
            for text in movementTexts:
                outputText += text + " "
            display.text(outputText)

runloop.run(main())