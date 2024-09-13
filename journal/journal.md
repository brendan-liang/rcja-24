# Robotics Journal

# Previous Work

![image.png](Robotics%20Journal%2018df3f47f479495d863a6d4a721dfdd0/image.png)

## Movement

We came in with a function that we wrote last year for the EV3 platform, that, given a bot built with 4 omni wheels at 90 degrees to each other, would take an angle in degrees and calculate the strength each wheel would need to rotate at to move the bot in that direction. 

```python
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
```

- We add 45 degrees to the angle before calculating, as the actual front of the bot/sensors is offset by 45 degrees from the motors. This helps in creating a nice catching area in the front of the bot.
- Our calculations use trigonometry and principles of the unit circle, similar to how you would get the coordinates of a point on the unit circle when given an angle (using `sin()` and `cos()`) .

## EV3 Design
The design of our EV3 robot was inspired by the ones we have seen online and in some of the other workspaces of our seniors. The design consists of the 2 motors parallel to each other at the bottom, connecting themselves with the main brick, moving the wheels. While we have the other 2 mortors ontop of the bottom ones creating a hashtag shape, also connecting to the main brick and the wheels. 

To fortify the wheels to the brick and to help them not get stuck to other robots, we decided on building shields infront of the wheels and connecting them around the wheels to make sure that they are safe in all directions, while making sure it still fits within the size limit. The shields for the wheels are connected to the main brick so make sure that when they are bumped, they dont move and dont interrupt the wheels movement. 

We have the compass sensor placed up high on the side of the robot to make sure that there is nothing blocking its view and to avoid magnetic interference. We placed the IR sensor on the diagonal of the main brick so that the front of the robot fits between the wheels and won't clash between it. It also works as a practical use of making the robot go faster when going forwards, as moving diagonally makes the movement utilise the power of 4 motors instead of 2.

As for the wire management, we have many of the wires wrapped up inbetween lodges in the lego to make sure they don't interfere with the wheels or any other part of the robot. Even though it seems chaotic, it won't interfere with the robots performance. 

## Spike Design
Our Spike robot's design is extremely simliar to our EV3.

The motors are all at the bottom of the robot, in the shape of a windmill, all interconnected and connecting themsevles with the main brick, compass sesnor and wheels. Same as the EV3 build, we also have shields which protext the wheels from getting disrupted or stuck. The shields are interconnected with one another, connecting themselves with the main brick as well. 

The IR sensor is also on the diagonal o the motors, which makes the robot move more effictively by utilising all 4 motors when moving forward. The IR sensor is connected between the main body and the motors, making it extremely secure and almost impossible to remove unless you break the entire robot. 

The wires on the robot are much easier managed, with them also being lodged between places in the lego, keeping them out of the way of the wheels.
# Week 2

## Disclaimer!

The previous 2 terms of work were undocumented, as it consisted mostly of recreating the work we had done last year. The main things our group finished were:

- Designing + building robots
- Some basic code to move the bot, etc.

## Progress

We were able to focus in today on working on the code for Spike Prime. First, we reformatted the code we had to utilise classes for readability, and grouping functions together with devices. For example, we created a `Drivebase` class that was responsible for handling motor interactions, such as a `move(degrees)` function. 

```python
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

```python
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

```python
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

```python
class FileSystem:
    def __init__(self, path="../../config/wbot"):
        self.path = path
        return

    def dump(self, path, obj):
        json.dump(obj, self.path + path)

    def load(self, path):
        json.load(self.path + path)
```

# Week 3

## Progress

We focused on implementing an algorithm for the Spike Prime bot to reorientate itself when it was facing the wrong way, while not disrupting its movement. We achieved this through what we called “Yaw Adjustment”, where the inverse of the yaw rotation offset (basically just rotation parallel to the ground) was split among multiple iterations, and the rotation was added to the motor speeds, in order to slowly rotate to yaw=0 (facing forward). 

Since the dividing calculation was done each iteration, it made it so that the amount it rotated would get gradually smaller at an exponential rate, which made the rotations larger if there was a large offset, and smaller if there was a small offset. 

```python
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

```

