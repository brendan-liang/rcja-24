# Robotics Journal

# Week 2

## Disclaimer!

The previous 2 terms of work were undocumented, as it consisted mostly of recreating the work we had done last year. The main things our group finished were:

- Designing + building robots
- Some basic code to move the bot, etc.

## Progress

We were able to focus in today on working on the code for Spike Prime. First, we reformatted the code we had to utilise classes for readability, and grouping functions together with devices. For example, we created a `Drivebase` class that was responsible for handling motor interactions, such as a `move(degrees)` function. 

```py
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
```
```py
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
```

This makes the main code overall much easier to read.

```py
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
```

We also attempted to write and read config files, so that minor adjustments could be made more easily on the day of a competition. We attempted simply using `open("file.txt" ...)` and `read("file.txt")`, but we kept getting an error saying that the file did not exist when we attempted to read

To test if the files were actually being created, we used `os.listdir()`. After playing around a bit, we figured that while the files were being created, they were being deleted after the script finished running.

We later discovered, using `os.listdir("../")` to find the parent folder and `os.listdir("../../")`to find the root folder, that the scripts were run in isolated environments that would be reset after the script finished.

To fix this, we realised that we could read and write to the root directory, as files there were not reset in between script executions. From this, we developed a class to write/read JSON files for configuration.

```py
class FileSystem:
    def __init__(self, path="../../config/wbot"):
        self.path = path
        return

    def dump(self, path, obj):
        json.dump(obj, self.path + path)

    def load(self, path):
        json.load(self.path + path)
```
