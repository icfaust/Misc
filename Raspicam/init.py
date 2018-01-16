#!/usr/bin/env python

import MDSplus
import struct
from subprocess import call

event=r'raspi_init'

while True:
	rawshot = MDSplus.Event.wfeventRaw(event)
	#shot number is a 32-bit unsigned integer passed as 4 uint8s
	shot = struct.unpack('I',struct.pack(str(len(rawshot))+'B',*rawshot))[0]
	call(['sudo','./acq.py',str(shot),'1'])

