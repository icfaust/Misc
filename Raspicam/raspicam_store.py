#!/usr/bin/env python

import scipy
from subprocess import call
import sys
import MDSplus
import time

shot=int(sys.argv[1])
loc ='/usr/local/cmod/codes/spectroscopy/video/'
node = '.video_daq.raspicam'
complete = 'rasipcam_complete'

print('accessing spectroscopy tree')
tree = MDSplus.Tree('spectroscopy',shot)

try:
   res = (tree.getNode(node+':width').data(),
          tree.getNode(node+':height').data())
except:
   res = (640, 480)

try:
    framerate = tree.getNode(node+':frame_rate').data()
except:
    framerate = 90

try:
    frames = tree.getNode(node+':max_frames').data()
except:
    frames = 180

try:
    start = tree.getNode(node+':trigger').data()
except:
    start = 0.


#pull file
time.sleep(10)
print('pulling file')
call(['scp',
      'mdsplus@raspicam4:/home/mdsplus/out' + str(shot) + '.dat',
      loc + 'out.dat'])

call(['chmod','777',loc+'out.dat'])
print('removing file from raspicam')
call(['ssh','mdsplus@raspicam4','rm','/home/mdsplus/out'+str(shot)+'.dat'])


# load and unpack .dat file 
data = scipy.memmap(loc+'out.dat',
                    dtype='uint8',
                    shape=(frames,res[1],res[0]))

#data2 = scipy.transpose(data,(1,2,0)) #reorder data for use in mdsplus
#this call makes me sad, because its in a great form to begin with...

timebase = scipy.linspace(0,frames/framerate,frames) + start

# upload to tree using putdata 
dummy = MDSplus.Data.compile('build_signal($,*,$)',data,timebase)
tree.getNode(node+':frames').putData(dummy)
MDSplus.Event.seteven(complete)

# cleanup
print('cleaning temporary files')
call(['rm',loc+'out.dat'])
