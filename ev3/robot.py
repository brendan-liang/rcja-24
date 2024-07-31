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
def threshold(l, num):
    for i in l:
        if i >= num:
            return True
    return False
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
        self.motors = [MediumMotor(OUTPUT_A),MediumMotor(OUTPUT_B),MediumMotor(OUTPUT_C),MediumMotor(OUTPUT_D)]
        self.motorMoves = [[],[],[],[]]
        # Load config
        # with open("config.json", "r") as f:
        #     self.config = load(f).get("motors", [1, 1, 1, 1])
        self.config = [1, 1, 1, 1]
    
    def move(self, deg:int, speed:int=100) -> None:
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
    def __init__(self, port:str, sensor:str, mode:str=None) -> None:
        if sensor in self.alt.keys():
            self.sensor = self.alt[sensor]["create"](port)
            return
        self.sensor = Sensor(port, driver_name=sensor)
        self.type = sensor
        if mode:
            self.sensor.mode = mode

    def read(self, value=0) -> None:
        if self.type in self.alt.keys():
            return self.alt["us"]["read"](self.sensor)
        return self.sensor.value(value)
            

        
class Sensors:
    '''Sensor collection'''
    def __init__(self, *args):
        '''To load specific sensors, parse them as tuples: `(name, SmoothSensor(...))`'''
        if args:
            for sensor in args:
                self.__setattr__(sensor[0], sensor[1])
                return
        self.irL = SmoothSensor(INPUT_1, "ht-nxt-ir-seek-v2", "AC-ALL")
        self.irR = SmoothSensor(INPUT_2, "ht-nxt-ir-seek-v2", "AC-ALL")
        return
    
    def readIR(self):
        vals = [self.irL.read(i) for i in range(1, 6)]
        valsB = [self.irR.read(i) for i in range(1, 6)]
        subsT = []
        subsF = []
        subsB = []

        if not (threshold(vals, 3) or threshold(valsB, 3)):
            return False
        
        if sum(vals):
            subsF = [vals[i-1] * [][i - 1] for i in range(1, 6)]
        if sum(valsB):
            subsB = [valsB[i-1] * [84, 132, 180, -132, -84][i - 1] for i in range(1, 6)]
        if len(subsF) and len(subsB):
            subsT = [(subsF[0] + subsB[-1])/2, (subsF[-1] + subsB[0])/2]
            subsF.pop()
            subsF.pop(0)
            subsB.pop()
            subsB.pop(0)

            subsT.extend(subsF)
            subsT.extend(subsB)
            
            if sum(vals) + sum(valsB) and len(subsT) and len(vals) and len(valsB):
                return (sum(subsT)/(sum(vals) + sum(valsB))) % 360
            else:
                return
        return dir % 360 or 360
