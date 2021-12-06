# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 11:53:15 2020

Droplet Train XYZ Motion Controller

@author: Pip Clark
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
# If you are getting an error that could not open port com# then you need to run this line 
#board.exit() # needed to safely close com port communicaton, and if the previous code was interrupted then it didn't close 
#it is also at the the end of the code
#another error could be that the arduino is on a different com port, check in arduino IDE to be sure which # it is on

import pyfirmata
import time
import datetime
from pathlib import Path
import os
import glob

#except ImportError:  # Python 3
import tkinter as tk
import tkinter.font as tkFont
from tkinter import * #imports everything
from tkinter.ttk import Frame, Button, Style
import threading
  

#%% Start connection 
board = pyfirmata.Arduino('COM5') #use ardnuio ide to check COM port # of arduino
#for some reason it makes a pulse when connecting

time.sleep(1) #a short delay might be needed if initial commands are being lost
#board.digital is a list whose elements represent the digital pins of the Arduino. These elements have the methods read() and write()
#%% Setting up pulse and direction pin numbers
dirpin_x = board.get_pin('d:3:o') #digital: pin # on board: output (i for input)
pulpin_x = board.get_pin('d:2:o') #p is PWM for pulse width mod where you can specify duty cycle
enblpin_x = board.get_pin('d:12:o')
enblpin_x.write(0) # enables pin when low, needs to be enabled to fight resitance of bellows* when stationary *the bellows were under ultra high vacuum in my application, you may not have extra resistance in your application but it shouldn't change anything


dirpin_y = board.get_pin('d:5:o') #digital: pin # on board: output (i for input)
pulpin_y = board.get_pin('d:4:o') #p is PWM for pulse width mod where you can specify duty cycle
enblpin_y = board.get_pin('d:11:o')
enblpin_y.write(0) # enables pin when low, needs to be enabled to fight resitance of bellows when stationary

dirpin_z = board.get_pin('d:7:o') #digital: pin # on board: output (i for input)
pulpin_z = board.get_pin('d:6:o') #p is PWM for pulse width mod where you can specify duty cycle
enblpin_z = board.get_pin('d:10:o')
enblpin_z.write(0) # enables pin when low, needs to be enabled to fight resitance of bellows when stationary


#%% Setting up speed and distance settings for motors
pulse_per_rev = 1600 # SET THIS (as set on the driver, eg 400 pulses seems to give about a full term when its set to 400)
mm_per_rev = 1.27 # SET THIS  (on XY screws, 0.05", 20 threads per inch on lead screws)

zpulse_per_rev = 400 # SET THIS these are often different for z 
zmm_per_rev = 1.016 # SET THIS

pulse_per_mm = pulse_per_rev/mm_per_rev # number of steps to drive a mm  put in real values
zpulse_per_mm = zpulse_per_rev/zmm_per_rev

delaytime = 0.01 # in seconds, controls speed of motors, delay inbetween pulses to pulse pin. Fastest is around 10 ms for standard windows clock
i = 0 #setting up i so it can be called globally later
loops_missing = 0 #setting up i so it can be called globally later
#%% Read XYZ positions from previous log file if available

# SET THIS path to a folder you created called XYZ log. This will save the current XYZ positions if you close the GUI and load the most recent when you open the GUI
list_of_files = glob.glob(r'C:\Users\local_admin\Documents\pyfirmata_arduinocode\XYZlog/*.txt') # * means all if need specific format then eg *.txt # change this to your folder path
latest_file = max(list_of_files, key=os.path.getctime)

if os.path.isfile(latest_file): #returns true if file exists
    #read in values from text file
    f = open(latest_file)
    all_lines = f.readlines()
    xpos = float(all_lines[1]) #x position is on the 2nd line
    ypos = float(all_lines[3])
    zpos = float(all_lines[5])
    
    safex = float(all_lines[7]) #safe x position is on the 8th line
    safey = float(all_lines[9])
    safez = float(all_lines[11])
    f.close()
    
else:
    xpos = 0 #setting the current x y and z positions to 0 incase no files in XYZ log
    ypos = 0
    zpos = 0

speed = 0
ToF = 0

#xposstring = StringVar()
xposstring = "current x position = {} mm".format(xpos)
yposstring = "current y position = {} mm".format(ypos)
zposstring = "current z position = {} cm".format(zpos)

speedstring = "speed = {} cm/s".format(speed)
ToFstring = "ToF = {} s".format(ToF)

#%% GUI
class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Droplet Train Movement")
        self.style = Style()
        self.style.theme_use("classic")
        self.grid()
        self.create_widgets()
        
        

    def create_widgets(self): # create buttons in here
        self.customFont = tkFont.Font(family="system", size=16)
        self.customFont2 = tkFont.Font(family="system", size=18)

        self.movebutt = tk.Button(self, font=self.customFont, bg="blue")
        self.movebutt["text"] = "Move!"
        self.movebutt["command"] = lambda :threading.Thread(target=self.movebutton).start()
        self.movebutt.grid(row=0,column=4)
        
        self.stop = tk.Button(self, font=self.customFont, text="Stop!", 
                           command=self.stopfun)
        self.stop.grid(row=0,column=5) 
        self.stop.config(bg="red")
        
        self.quitbutt = tk.Button(self, font=self.customFont, text="QUIT", fg="red",
                              command=self.close)
        self.quitbutt.grid(row=0, column=9)
         
        # speed buttons
        self.Lspeed = tk.Label(self, text="set speed of stepper motors", font=self.customFont)
        self.Lspeed.grid(row=0, column=0, columnspan=3)
        self.slowspeedbutt = tk.Button(self, text="slow", font=self.customFont,
                                      command=self.slowspeed)
        self.slowspeedbutt.grid(row=1, column=0)
        self.slowspeedbutt.config(bg="grey")
        
        self.medspeedbutt = tk.Button(self, text="medium", font=self.customFont,
                                      command=self.medspeed)
        self.medspeedbutt.grid(row=1, column=1)
        self.medspeedbutt.config(bg="red")
        
        self.fastspeedbutt = tk.Button(self, text="fast", font=self.customFont,
                                      command=self.fastspeed)
        self.fastspeedbutt.grid(row=1, column=2)
        self.fastspeedbutt.config(bg="grey")
        
        #XYZ AXIS MOVEMENT
        
        #x axis movement
        self.L1 = Label(self, text="set x position to (mm)", font=self.customFont)
        self.L1.grid(row=2,column =1)
        self.L2 = Label(self, text=xposstring, font=self.customFont)
        self.L2.grid(row=4, column=1) #grid needs to be on separate row to allow updates
        self.E1 = Entry(self, bd =5, font=self.customFont)
        self.E1.grid(row=3, column=1)  #grid needs to be on separate row to allow get to function 
        
        #y axis movement
        self.L3 = Label(self, text="set y position to (mm)", font=self.customFont)
        self.L3.grid(row=5,column =1)
        self.L4 = Label(self, text=yposstring, font=self.customFont)
        self.L4.grid(row=7, column=1) #grid needs to be on separate row to allow updates
        self.E2 = Entry(self, bd =5, font=self.customFont)
        self.E2.grid(row=6, column=1)  #grid needs to be on separate row to allow get to function 
  
        #z axis movement
        self.L5 = Label(self, text="set z position to (cm)", font=self.customFont)
        self.L5.grid(row=8,column =1)
        self.L6 = Label(self, text=zposstring, font=self.customFont)
        self.L6.grid(row=10, column=1) #grid needs to be on separate row to allow updates
        self.E3 = Entry(self, bd =5, font=self.customFont)
        self.E3.grid(row=9, column=1)  #grid needs to be on separate row to allow get to function 
  
 
        
        #SET AS 0 buttons
        self.resetx = tk.Button(self, text="set current x as 0", font=self.customFont,
                                      command=self.resetx)
        self.resetx.grid(row=3, column=4)
        
        self.resety = tk.Button(self, text="set current y as 0", font=self.customFont,
                                      command=self.resety)
        self.resety.grid(row=6, column=4)
        
           
        #Safe place buttons - you can set an XYZ position that is 'safe' ie if something goes wrong you can click on this and it will move back to this position (first in x, then y, then z)
        
        self.setsafeplace = tk.Button(self, text="Set Current position as safe place", font=self.customFont,
                                      command=self.safeplaceset)
        self.setsafeplace.grid(row=11, column=1,columnspan=3)
        
        self.gotosafeplace = tk.Button(self, text="Go to safe place!", font=self.customFont,
                                      command=lambda :threading.Thread(target=self.gotosafe).start())
        self.gotosafeplace.grid(row=11, column=4,columnspan=2)
        self.gotosafeplace.config(bg="green")
        
        #JOG X Y Z Buttons and increment setter
        self.jogsizeL = tk.Label(self, text="jog size (mm)", font=self.customFont).grid(row=1, column=6, columnspan=3)
        self.Ejogsize = tk.Entry(self, bd=5, font=self.customFont)
        self.Ejogsize.grid(row=2, column=6, columnspan=3)
        
        self.jogxleft = tk.Button(self, text="\u2190", font=self.customFont, command=lambda :threading.Thread(target=self.jogxL).start())
        self.jogxleft.grid(row=3, column=6)
        self.jogxlabel = tk.Label(self, text="x", font=self.customFont).grid(row=3,column=7)
        self.jogxright = tk.Button(self, text=u"\u2192", font=self.customFont, command=lambda :threading.Thread(target=self.jogxR).start())
        self.jogxright.grid(row=3, column=8)
        
        self.jogyleft = tk.Button(self, text=u"\u2190", font=self.customFont, command=lambda :threading.Thread(target=self.jogyL).start())
        self.jogyleft.grid(row=6, column=6)
        self.jogylabel = tk.Label(self, text="y", font=self.customFont).grid(row=6,column=7)
        self.jogyright = tk.Button(self, text=u"\u2192", font=self.customFont, command=lambda :threading.Thread(target=self.jogyR).start())
        self.jogyright.grid(row=6, column=8)
        
        self.jogzup = tk.Button(self, text=u"\u2191", font=self.customFont, command=lambda :threading.Thread(target=self.jogzU).start())
        self.jogzup.grid(row=9, column=6)
        self.jogzlabel = tk.Label(self, text="z", font=self.customFont).grid(row=9,column=7)
        self.jogzdown = tk.Button(self, text=u"\u2193", font=self.customFont, command=lambda :threading.Thread(target=self.jogzD).start())
        self.jogzdown.grid(row=9, column=8)

        
        
        
        #fall time for z calculator
        self.ToFcalculator = Label(self, text="Calculate droplet time of flight", font=self.customFont).grid(row=12,column=0,columnspan=3)
        self.P1label = Label(self, text="FF P (mbar)", font=self.customFont).grid(row=13,column=0,columnspan=2)
        self.P1 = Entry(self, bd =5, font=self.customFont,width=6)
        self.P1.grid(row=13, column = 2)
        
        self.P2label = Label(self, text="Chamber P (mbar)", font=self.customFont).grid(row=14,column=0,columnspan=2)
        self.P2 = Entry(self, bd =5, font=self.customFont,width=6)
        self.P2.grid(row=14, column = 2)
        
        self.Zt0label = Label(self, text="Z value at t0 (cm)", font=self.customFont).grid(row=15,column=0,columnspan=2)
        self.Zt0 = Entry(self, bd =5, font=self.customFont,width=6)
        self.Zt0.grid(row=15, column = 2)
        
        self.Calculate = tk.Button(self, text="Calculate!", font=self.customFont, command=lambda :threading.Thread(target=self.Calculator).start())
        self.Calculate.grid(row=13, column = 4)
        
        self.speedlabel = Label(self, text=speedstring, font=self.customFont).grid(row=14,column=4)
        self.ToFlabel = Label(self, text=ToFstring, font=self.customFont).grid(row=15,column=4)
        
    
#%% App functions  

    def movebutton(self):

        self.goodtorun=True #resets this to true incase stop button was used
        self.movebutt.config(text="moving")
        self.movebutt.config(bg="grey")
        #first check for changes in x position input
        newx_str = self.E1.get() #gets a string from the x position GUI input
        if newx_str == "": #checks if there is something in the field
            print("no x value entered")
        else:
            self.movex(newx_str)
        
        #next check for changes in y position input
        newy_str = self.E2.get() #gets a string from the y position GUI input
        if newy_str == "": #checks if there is something in the field
            print("no y value entered")
        else:
            self.movey(newy_str)
            
        #next check for changes in z position input
        newz_str = self.E3.get() #gets a string from the y position GUI input
        if newz_str == "": #checks if there is something in the field
            print("no z value entered")
        else:
            self.movez(newz_str)       
            
        self.movebutt.config(text="Move!")
        self.movebutt.config(bg="blue")
            
    def movex(self,newx_str):
            global xpos, ypos, zpos  #needs to be global to be updated globally later in function
            global xposstring, yposstring, zposstring
            newx = float(newx_str) #converts string to float (number with decimal places)
            if newx != xpos: #if there is a change compared to previous x position
                xdistance_in_mm = newx - xpos #calculates difference
                if xdistance_in_mm < 0:
                    xdirection = 1 #forwards this is different to y and z to make physical sense
                    xdistance_in_mm = -xdistance_in_mm #reverse it so loops is a positive number
                else:
                    xdirection = -1 #backwards
                xloops = round(xdistance_in_mm*pulse_per_mm) #how many pulses to that will be given to motor in move function
                print(xloops)
                
                self.move(xdirection,xloops,dirpin_x,enblpin_x,pulpin_x) #sends number of pulses and direction to arduino pins, move function above
                
                #update the display to show new positions
                distance_missingx = (loops_missing/pulse_per_mm)*xdirection*-1 # as x is physically reversed in reality
                xpos = round(newx - distance_missingx,2) #set the new xposition
                xposstring = "current x position = {} mm".format(xpos)
                self.L2.config(text=xposstring)
            
        #next check for changes in y position input
    def movey(self, newy_str):
            global ypos, yposstring  #needs to be global to be updated globally later in function
          
            newy = float(newy_str) #converts string to float (number with decimal places)
            if newy != ypos: #if there is a change compared to previous y position
                ydistance_in_mm = newy - ypos #calculates difference
                if ydistance_in_mm < 0:
                    ydirection = -1 #backwards
                    ydistance_in_mm = -ydistance_in_mm #reverse it so loops is a positive number
                else:
                    ydirection = 1 #forwards
                yloops = round(ydistance_in_mm*pulse_per_mm) #how many pulses to that will be given to motor in move function
                   
                self.move(ydirection,yloops,dirpin_y,enblpin_y,pulpin_y) #sends number of pulses and direction to arduino pins, move function above
                
                #update the display to show new positions
                distance_missingy = (loops_missing/pulse_per_mm)*ydirection
            
                ypos = round(newy - distance_missingy,2) #set the new xposition
                yposstring = "current y position = {} mm".format(ypos)
                self.L4.config(text=yposstring)
        

    def movez(self,newz_str):
            global zpos, zposstring
            newz = float(newz_str) #converts string to float (number with decimal places)
            if newz > 61:
                print("This value exceeds Z limit")
            elif newz < 0:
                print("This value exceeds Z limit")
            else:
                if newz != zpos: #if there is a change compared to previous y position
                    zdistance_in_mm = (newz - zpos)*10 #calculates difference
                    if zdistance_in_mm < 0:
                        zdirection = 1 #upwards (lower number)
                        zdistance_in_mm = -zdistance_in_mm #reverse it so loops is a positive number
                    else:
                        zdirection = -1 #downwards ()
                    zloops = round(zdistance_in_mm*zpulse_per_mm) #NOTE DIFFERENT FOR THE Z DRIVE how many pulses to that will be given to motor in move function
                       
                    self.move(zdirection,zloops,dirpin_z,enblpin_z,pulpin_z) #sends number of pulses and direction to arduino pins, move function above
                    
                    #update the display to show new positions
                    distance_missingz = (loops_missing/zpulse_per_mm)*zdirection*-1
                    zpos = round(newz  - (distance_missingz/10),2)#set the new xposition
                    zposstring = "current z position = {} cm".format(zpos)
                    self.L6.config(text=zposstring)
        
       
#%% 
    #movement function for stepper motor
    def move(self,dirn,loops,dirpin,enblpin,pulpin):
        if dirn == 1:
            dirpin.write(1)
            #print('forwards')
        else:
            dirpin.write(0)
            #print('backwards')
        global i
        i=0
        self.moveloop(loops,pulpin)
        #enblpin.write(0) #enables x to move when low (0) make a condition for this
    
    # how to get it to be able to be interuppted?
    def moveloop(self,loops,pulpin):
        global i
        global loops_missing
        
        while self.goodtorun and i < loops: #if equals true (ie stop not hit) keep running
            pulpin.write(0)
            pulpin.write(1)
            print(i)    
            i +=1
            time.sleep(delaytime)
         
        if self.goodtorun == False:
            print('movement interreupted by user')
            loops_missing = loops - i #number of loops not completed  
            i=0           

        if i == loops:
            i = 0 #resets counter
            print('movement completed')
            loops_missing = 0
            

 
#%% Close GUI function     
    def close(self):
        #write a new file to save the xyz positions with date and time of closure as name        
        timestr = '/'+ time.strftime("%Y%m%d-%H%M%S") +".txt"
        XYZlogfilepath = Path(r'C:\Users\local_admin\Documents\pyfirmata_arduinocode\XYZlog' + timestr)
        f= open(XYZlogfilepath,"w+") #creates new txt file
        f.write("X position\n" +str(xpos) + "\nY position \n" + str(ypos) + "\nZ position \n" + str(zpos) +
                "\nsafe X \n" + str(safex) + "\nsafe Y \n" + str(safey) + "\nsafe Z \n" + str(safez))
        
        f.close()
        self.master.destroy(),board.exit()
        return
    
#%% Interuppt / stop button
    def stopfun(self):
        self.goodtorun=False
        #print('fudge')
    
#%%    
    # speed of motor functions 
    # you can change the delay times to change the length of pulses going to the stepper. You can also set 0 if 0.0001 is not fast enough
    # note that another way to make it faster is to decrease pulse_per_rev on your driver (and in the code) but at the cost of precision
    def slowspeed(self):
        global delaytime
        delaytime = 0.03
        #then update the BG color so this one is red and the others normal
        self.slowspeedbutt.config(bg="red")
        self.medspeedbutt.config(bg="grey")
        self.fastspeedbutt.config(bg="grey")
        return
    def medspeed(self):
        global delaytime
        delaytime = 0.01 #about as fast as possible with an actual delay time value
        self.slowspeedbutt.config(bg="grey")
        self.medspeedbutt.config(bg="red")
        self.fastspeedbutt.config(bg="grey")
        return
    def fastspeed(self):
        global delaytime
        delaytime = 0.0001 #as fast as possible but its quite fast!
        # setting to 0 is faster but can make the gui crash... no rush ;) 
        self.slowspeedbutt.config(bg="grey")
        self.medspeedbutt.config(bg="grey")
        self.fastspeedbutt.config(bg="red")
        return
    
    #reset functions
    def resetx(self):
        global xpos
        global oldxpos
        oldxpos = ("x position before reset {} mm").format(xpos)
        print(oldxpos)
        xpos = 0
        xposstring = "current x position = {} mm".format(xpos)
        self.L2.config(text=xposstring)

    
    def resety(self):
        global ypos
        global oldypos
        oldypos = ("y position before reset {} mm").format(ypos)
        print(oldypos)
        ypos = 0
        yposstring = "current y position = {} mm".format(ypos)
        self.L4.config(text=yposstring)

    
    def resetz(self):
        global zpos
        global oldzpos
        oldzpos = ("z position before reset {} mm").format(zpos)
        print(oldzpos)
        zpos = 0
        zposstring = "current z position = {} mm".format(zpos)
        self.L6.config(text=zposstring)

    
    def safeplaceset(self):
        global safex, safey, safez
        safex = xpos
        safey = ypos
        safez = zpos
        
    def gotosafe(self): #basically a copy of the movebutton except it gets the new positions from the stored save place
        self.goodtorun=True #resets this to true incase stop button was used
        
        #first check for changes in x position input
        newx_str = str(safex) #gets a string from the x position GUI input
        if newx_str == "": #checks if there is something in the field
            print("no safe place stored")
        else:
            self.movex(newx_str)
        
        #next check for changes in y position input
        newy_str = str(safey) #gets a string from the y position GUI input
        if newy_str == "": #checks if there is something in the field
            print("no safe place stored")
        else:
            self.movey(newy_str)
            
        #next check for changes in z position input
        newz_str = str(safez) #gets a string from the y position GUI input
        if newz_str == "": #checks if there is something in the field
            print("no safe place stored")
        else:
            self.movez(newz_str)

    def jogxL(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newx_str = str(xpos-float(jogsize)) # note here it is minus jogsize
            self.movex(newx_str)
            
    def jogxR(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newx_str = str(xpos+float(jogsize)) #and here it is positive
            self.movex(newx_str)
            
    def jogyL(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newy_str = str(ypos-float(jogsize)) # note here it is minus jogsize
            self.movey(newy_str)
            
    def jogyR(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newy_str = str(ypos+float(jogsize)) #and here it is positive
            self.movey(newy_str)
            
    def jogzU(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newz_str = str(zpos-float(jogsize)/10) # note here it is plus jogsize
            self.movez(newz_str)
            
    def jogzD(self):
        self.goodtorun=True
        jogsize = self.Ejogsize.get()
        if jogsize == "":
            print("jog size not set")
        else:            
            newz_str = str(zpos+float(jogsize)/10) #and here it is negative
            self.movez(newz_str)
            
    def Calculator(self):
        P1 = self.P1.get()
        P2 = self.P2.get()
        Zt0 = self.Zt0.get()
        if P1 == "" or P2 == "" or Zt0 == "":
            print("Values missing, can not caculate")
        else:
            deltaP = float(P1)-float(P2)
            speed = 43.3884*deltaP**0.5 # in cm/s
            zdistance = -zpos + float(Zt0) # in cm
            tof = zdistance/speed # assumes droplets are falling straight down 
            print(speed)
            print(tof)
            speedstring = "speed = {} cm/s".format(speed)
            ToFstring = "ToF = {} s".format(tof)
            #self.speedlabel.config(text=speedstring)
            #self.ToFlabel.config(text=ToFstring)
            self.speedlabel.config(text=speedstring)
            
            
#%% Last part runs the GUI

root = tk.Tk()
app = Application(master=root)
app.mainloop()

    
#%% end
board.exit() # needed to safely close com port communicaton
    
      