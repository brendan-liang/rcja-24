#!/usr/bin/env micropython

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, list_motors
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4, list_sensors
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.button import Button
from ev3dev2.led import Leds
from ev3dev2.console import Console
from math import sin, cos, radians
from json import load
from time import sleep

# == Functions ==
def threshold(l:int|float, num:int|float) -> bool:
    for i in l:
        if i >= num:
            return True
    return False

def within_angle(start:int|float, angle:int|float, end:int|float) -> bool: # Only values from 0 to 360
    angle = angle or 360
    start = start or 360
    end = end or 360
    if start < end:
        return start <= angle <= end
    else:   
        return not (end < angle < start)
    
def clamp(low:int|float, n:int|float, high:int|float) -> int|float:
    return min(high, max(low, n))
# == Classes ==

class Interface:

    BTN_UP = "up"
    BTN_DOWN = "down"
    BTN_LEFT = "left"
    BTN_RIGHT = "right"
    BTN_ENTER = "enter"
    BTN_BACKSPACE = "backspace"


    '''Button and display interaction handler'''
    def __init__(self) -> None:
        self.buttons = Button()
        self.console = Console()

    def hasPressed(self, button:str) -> None:
        if getattr(self.buttons, button):
            while getattr(self.buttons, button):
                pass
            return True
        return False
    
    def waitForButton(self) -> None:
        while not self.buttons.any():
            pass
        while self.buttons.any():
            pass
        return

    def err(self, msg:str, ext=False) -> None:
        print(msg)
        self.waitForButton()
        if ext:
            exit()
        return
        
class DriveBase:
    '''Motor interaction handler'''
    def __init__(self, interface:Interface, check:bool) -> None:
        '''(bool) `check`: Sends a warning if there is an incorrect number of motors connected'''
        self.interface = interface
        # Check motors connected
        if check:
            if sum(1 for _ in list_motors()) != 4:
                self.interface.err("Invalid number of motors: " + str(sum(1 for _ in list_motors())) + "/4")
        # Connect motors + create "movement queue"
        self.motors = [MediumMotor(OUTPUT_D),MediumMotor(OUTPUT_A),MediumMotor(OUTPUT_B),MediumMotor(OUTPUT_C)]
        self.motorMoves = [[],[],[],[]]
        # Load config
        # with open("config.json", "r") as f:
        #     self.config = load(f).get("motors", [1, 1, 1, 1])
        self.config = [1, 1, 1, 1]

    def _legacyMove(self, deg:int, speed:int=100) -> None:
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

        self.motorMoves[0].append(speed*-1*sinMult*self.config[0])
        self.motorMoves[1].append(speed*-1*cosMult*self.config[1])
        self.motorMoves[2].append(speed*sinMult*self.config[2])
        self.motorMoves[3].append(speed*cosMult*self.config[3])
    
    def move(self, deg:int, yaw:int=0, speed:int=100) -> None:
        yaw = int(yaw/10)
        deg += 45
        rad = radians(deg)
        sinMult = sin(rad)
        cosMult = cos(rad)
        motorSpeeds = [-sinMult, cosMult, sinMult, -cosMult] # fL, fR, bR, bL

        yawAdjustDivisor = 150
        yawAdjustMax = 0.5
        yawAdjust = clamp(-yawAdjustMax, yaw/yawAdjustDivisor, yawAdjustMax)
        if yawAdjust:
            motorSpeeds = [spd - yawAdjust for spd in motorSpeeds]

        speedMult = speed/(max([abs(i) for i in motorSpeeds]))
        motorSpeeds = [int(spd * speedMult) for spd in motorSpeeds]

        for i in range(4):
            self.motorMoves[i].append(motorSpeeds[i])
    
    def tickMotors(self) -> None:
        for i in range(4):
            self.motors[i].on_for_seconds(round(sum(self.motorMoves[i]) / len(self.motorMoves[i])), 1, block=False)
            self.motorMoves[i] = []

class SmoothSensor:
    '''Sensor wrapper with outlier reduction'''
    alt = {
        "us": {
            "create": UltrasonicSensor,
            "read": lambda x: x.distance_centimeters
        }
    }
    def __init__(self, port:str, sensor:str, mode:str=None, smooth_amount:int=5) -> None:
        if sensor in self.alt.keys():
            self.sensor = self.alt[sensor]["create"](port)
            return
        self.sensor = Sensor(port, driver_name=sensor)
        self.type = sensor
        self.values = {}
        self.smooth_amount = smooth_amount
        if mode:
            self.sensor.mode = mode

    def read(self, value:int=0) -> None:
        if self.type in self.alt.keys():
            self.values.append(self.alt["us"]["read"](self.sensor))

        if not self.values.get(value, None):
            self.values[value] = [0] * self.smooth_amount
        self.values[value].append(self.sensor.value(value))
        self.values[value].pop(0)
        return sorted(self.values[value])[int(self.smooth_amount/2)]
        
class Sensors:
    '''Sensor collection'''
    def __init__(self, *args):
        '''To load specific sensors, parse them as tuples: `(name, SmoothSensor(...))`'''
        if args:
            for sensor in args:
                self.__setattr__(sensor[0], sensor[1])
                return
        self.irB = SmoothSensor(INPUT_1, "ht-nxt-ir-seek-v2", "AC-ALL")
        self.irF = SmoothSensor(INPUT_2, "ht-nxt-ir-seek-v2", "AC-ALL")
        self.compass = SmoothSensor(INPUT_3, "ht-nxt-compass")
        return
    
    def readIR(self):
        THRESH = 2
        valL = (24*self.irB.read(0)-120)+180
        valR = (24*self.irF.read(0)-120)
        strL = self._irStr(self.irB)
        strR = self._irStr(self.irF)
        if strR < THRESH and strL < THRESH:
            return 0
        if strR > strL:
            return valR % 360 or 360
        else:
            return valL % 360 or 360
        
    def _irStr(self, sensor:SmoothSensor):
        return sum((sensor.read(1),sensor.read(2),sensor.read(3),sensor.read(4),sensor.read(5)))
    
    def readIRStr(self) -> int:
        return min(max((self._irStr(self.irF), self._irStr(self.irB))), 3000)
        
    def resetCompass(self) -> None:
        self.compass.sensor.command = "BEGIN-CAL"
        self.compass.sensor.command = "END-CAL"

        self.straight = self.compass.read()
    
    def readCompass(self) -> int:
        return (self.compass.read() - self.straight) % 360