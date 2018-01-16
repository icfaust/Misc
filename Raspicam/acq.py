#!/usr/bin/env python

import sys
import time
import picamera
import MDSplus
import scipy
import RPi.GPIO as GPIO
from subprocess import call

loc = 'raspicam' + str(sys.argv[1]) + '.h264'
eventout = 'raspi_acq'
input = 'out.yuv'
output = '/home/pi/out' + str(sys.argv[1]) + '.dat'
output2 = '/home/mdsplus/'

#GPIO will be used for interfacing with a trigger
print('shot: '+str(sys.argv[1])+' '+str(sys.argv[2]))

# this section will have MDSplus data grabs for resolution, frame rate
# and time, for now hardcoded
# Settings will be loaded from MDSplus, but are hardcoded for now, 640x480
# 90 fps for 3 seconds

res = (640, 480)
framerate = 90
time = 3
points = res[0]*res[1]

# initialize GPIO trigger pin
GPIO.setmode(GPIO.BOARD)
GPIO.cleanup()
GPIO.setup(8,GPIO.IN)

# initialize raspberry pi camera
camera = picamera.PiCamera()
camera.resolution = res
camera.framerate = framerate

#set brightness and quality
camera.exposure_mode = 'fixedfps'


print('camera intialized')

# insert GPIO trigger here
input_state = 0
GPIO.wait_for_edge(8,GPIO.RISING)

#begin recording immediately
camera.start_recording(loc, format='h264')
camera.wait_recording(time)
camera.stop_recording()

print('shot acquired, exctract brightness')
#generate yuv file from .h264 file
call(['avconv','-i',loc,
      '-vcodec','rawvideo',
      '-pix_fmt','yuvj420p',
      input])

#extract luma values for storage in tree
file = open(input,'rb')
pfile = open(output,'wb')

for i in xrange(time*framerate): #do analysis in chunks
    pfile.write(file.read(points))
    file.read(points/2)
pfile.close()
#delete unnecessary data

#the raspi memory is too small to efficiently handle the data.
#its going to have to pass it off on another machine.
print('brightness extraction complete')
call(['rm',input])
call(['chmod','777',output])
call(['sudo','mv',output,output2])


if int(sys.argv[2]) == 0:
    call(['rm',loc])

MDSplus.Event.setevent(eventout)

#if this program fails before exchanging data, it will preserve shot video
#modify permissions to allow deletion by mdsplus user no matter what
