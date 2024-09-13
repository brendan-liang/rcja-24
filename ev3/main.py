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
    if interface.hasPressed(interface.BTN_ENTER):
        run = not run
        sensors.resetCompass()
    if run:
        ball = sensors.readIR()
        ballStr = sensors.readIRStr() * 10
        if not ball:
            drive.move(180)
        elif within_angle(330, ball, 30):
            drive.move(ball)
        else:
            drive.move(int(ball + copysign(ballStr, 180 - ball)*0.01))
        drive.tickMotors()