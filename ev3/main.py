#!/usr/bin/env micropython

from robot import Sensors, SmoothSensor, DriveBase, Interface, within_angle
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from math import copysign

from time import sleep

interface = Interface()
drive = DriveBase(interface, True)
sensors = Sensors()

run = False

print("Ready to run!")
sensors.resetCompass()
while True:
    # = Toggle button =
    if interface.hasPressed(interface.BTN_ENTER):
        run = not run
        sensors.resetCompass()
    if run:
        # = Read Sensors = 
        ball = sensors.readIR()
        ballStr = sensors.readIRStr() * 10
        facing = sensors.readCompass()

        # = Logic =
        #   ==> If no sight of ball
        if not ball:
            drive.move(180)
        #   ==> If ball is forwards
        elif within_angle(330, ball, 30):
            drive.move(ball*2)
        else:
        #   ==> If ball is behind
            drive.move(int(ball + copysign(ballStr, 180 - ball)*0.01))

        # = Move motors =
        drive.tickMotors()