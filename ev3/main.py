#!/usr/bin/env micropython

from robot import Sensors, SmoothSensor, DriveBase, Interface
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4

from time import sleep

interface = Interface()
drive = DriveBase(interface, True)
sensors = Sensors()

while True:
    ball = sensors.readIR()
    if ball:
        drive.move(ball)
    # drive.tickMotors()