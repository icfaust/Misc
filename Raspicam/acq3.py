#!/usr/bin/python
import sys
import subprocess
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg
import RPi.GPIO as GPIO
import MDSplus
# initialize GPIO trigger pin
#GPIO.setmode(GPIO.BOARD)
#GPIO.cleanup()
#GPIO.setup(8,GPIO.IN)

tree=sys.argv[1]
shot=int(sys.argv[2])
path=sys.argv[3]
t = MDSplus.Tree(tree,shot)
head = t.getNode(path)
width = int(head.getNode('width'))
height=int(head.getNode('height'))
pixel_format=int(head.getNode('pixfmt'))
num_frames=int(head.getNode('num_frames'))
exposure=int(head.getNode('exposure'))

p = subprocess.Popen(['/bin/sh'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,shell=False)
p.stdin.write('. /etc/profile.d/mdsplus.sh\n')
p.stdin.write('date\n')
p.stdin.flush()
print "v4l2-ctl --set-fmt-video=width=%d,height=%d,pixelformat=%d\n"%(width, height ,pixel_format,)
p.stdin.write("v4l2-ctl --set-fmt-video=width=%d,height=%d,pixelformat=%d\n"%(width, height ,pixel_format,))
p.stdin.write("echo XXXXXXXXXXXXXXXXX\n")
p.stdin.flush()
p.stdin.write("sudo /home/pi/gpio_check.py")
p.stdin.flush()
# insert GPIO trigger here
#input_state = 0
#GPIO.wait_for_edge(8,GPIO.RISING)
print "v4l2-ctl --stream-mmap=%d --stream-count=%d --stream-to=%d.rgb\n" % (num_frames, num_frames, shot,)
p.stdin.write("v4l2-ctl --set-ctrl=exposure_time_absolute=%d --stream-mmap=%d --stream-count=%d --stream-to=%d.rgb\n" % (exposure, num_frames, num_frames, shot,))
p.stdin.flush()
ans=p.communicate()
img = np.fromfile("%d.rgb"%(shot,), dtype=np.uint8)
img=img.reshape(num_frames, height, width,3)
#ims = []
#for i in range(60):
#  frame = img[i, :, : ,:]
#  im = plt.imshow(frame)
#  ims.append([im])
#
#fig = plt.figure()
#ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True,
#    repeat_delay=1000)
#plt.show()
frames=head.getNode('frames')
frames.record = MDSplus.Signal(img, None, [ 'r' ,'g' , 'b' ], MDSplus.Range(0, width-1), MDSplus.Range(0, height-1), MDSplus.Range(0, num_frames-1))
