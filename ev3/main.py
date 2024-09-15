#!/usr/bin/env micropython

from robot import Sensors, SmoothSensor, DriveBase, Interface, within_angle
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from math import copysign

from time import sleep

interface = Interface()
drive = DriveBase(interface, True)
sensors = Sensors()

run = False

mult = 1
front = 60

print("Ready to run!")
sensors.resetCompass()
while True:
    # = Toggle button =
    if interface.hasPressed(interface.BTN_ENTER):
        sensors.resetCompass()
        run = not run
    if run:
        # = Read Sensors = 
        facing = sensors.readCompass()
        ball = sensors.readIR()
        ballStr = sensors.readIRStr() * 10
        print(facing)
        if not ball:
            drive._legacyMove((180 + facing) % 360)
        else:
            drive._legacyMove(ball % 360)

        # = Logic =
        #   ==> If no sight of ball
        # if not ball:
        #     drive._legacyMove((180 + facing) % 360)
        # #   ==> If ball is forwards
        # elif within_angle((360 - front) % 360, (ball + facing) % 360, front):
        #     drive._legacyMove(ball*mult)
        # else:
        # #   ==> If ball is behind
        #     drive._legacyMove(int(ball + copysign(ballStr, 180 - ball)*0.01))

        # = Move motors =
        drive.tickMotors()