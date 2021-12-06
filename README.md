# Controlling-Stepper-Motors-with-Arduino-NEMA-
A python script and GUI for controlling stepper motors in 3 directions (XYZ) from an arduino (I was using nema 23 but it should work for others in general, maybe with some small changes)

I used an Arduino uno with usb connection, using pyfirmata to control it from python, the arduino pins (details below) were fed into 3 DM542 microstep drivers (powered with 24 V power supplies), and the outputs from the drivers were connected to the NEMA23 stepper motors through 3x custom (5-pin) XLR cables (using 4 of the connections).

For X, Y and Z directions I set up the pins as follows (but you can change it easily in the code)
X
direction pin - 3
pulse pin - 2
enable pin - 12
Y
direction pin - 5
pulse pin - 4
enable pin - 11
Z
direction pin - 7
pulse pin - 6
enable pin - 10

brief explanation of the functions
direction - high (5V) or low (0V) depending on whether you want to drive forwards or backwards
pulse - pulses between high and low, the driver will then interpret this (depending on the driver settings) as e.g. 400 pulses need to rotate the stepper drive one full rotation. So if this pin goes high to low 400 times your driver will rotate 360 degrees in this example.
enable pin - when high this will block the driver from taking action when recieving pulses. In the end I didn't experience much push back so I left this low all the time but you can edit to set it high and then only low when the move loop is activated if you experience unwanted movement.

The GUI is quite basic, made using tkinter. I recommend first time you run it putting x,y and z in your e.g. 0 positions and saving those positions as 0. Note #1 that they can go to negative values. Note #2 that z is set up in cm and running backwards (ie higher up is a lower value) because this is how my physical z drive was set up, but changing that should be fairly straight forward! Here you can either set a position for x/y/z (or all 3) and start the system moving there. The positions text will update once they arrive in position. You can also set a jog size and then move either x y or z in those steps. There's a stop button in case of emergencies. If you hit stop the positions text will update to the position they reached when you hit stop. There's also the buttons 'set safe place' - the system will the current position, and if you later hit 'go to safe place' it will move there. Note that the system will always move first in x, then y, and last z. If you want to change the order just switch the order x y and z are checked and acted on at line 255 in the def movebutton. You can also set the speed in the GUI between fast, medium and slow, this just changes the sleep time between pulses sent to the drivers. You can change them easily. If fast is still not fast enough then decrease you drivers pulses per revolution settings if possible. 

There are a few places in the code where you will need to set things specific to your setup (the pins, driver and thread settings, and the file directory for storing positions between uses if you want this). 
Elaborating on that last point, line 76, set a path to a folder you created called XYZ log. This will save the current XYZ positions (in a text file) if you close the GUI and load the most recent when you open the GUI.

I'll upload some photos of the setup and a wiring diagram. I hope this is useful for someone else that is sick of trying to get labview to do what they want. Happy stepping!
