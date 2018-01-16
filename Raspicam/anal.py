#!/usr/bin/env python

import scipy
import pickle
import sys
from subprocess import call

input = 'out.yuv'
output = 'out.dat'

#generate yuv file from .h264 file
call(['avconv','-i','raspicam' + str(sys.argv[1]) + '.h264',
      '-vcodec','rawvideo',
      '-pix_fmt','yuvj420p',
      input]) 

#open tree and find frame rate and acquisition time (hardcoded to start)
res = (640,480)
time = 3
framerate = 90
points = res[0]*res[1]


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
call(['rm','out.yuv'])
