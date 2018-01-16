"""Object-oriented, high-level interface for Andor cameras (SDK2), written in Cython. 

.. Note::
   
   - This is not a stand-alone driver. Andor's proprietary drivers must be installed.
     The setup script expects to find ``libandor.so`` in ``/usr/local/lib/``
     (the driver's default installation directory).
   
   - Andor provides a low-level, :mod:`ctypes` wrapper on their SDK, called ``atcmd``.
     If available, it will be imported as :attr:`Andor._sdk`.
     
   - This documentation should be read along Andor's Software Development Kit manual.
   
   - **To build the extension**::
   
     $ python2.7 setup_extension.py build_ext --inplace

.. Warning::
   This module is not thread-safe. If :func:`AcqMode.wait` is blocking a
   background thread, and another function call is made from the main thread,
   the main thread will block too.

-----------------------------

:Usage:

The camera is controlled via the top-level class :class:`Andor`:

>>> from andor2 import Andor
>>> cam = Andor()

The :class:`Andor` instance is just a container for other objects
that control various aspect of the camera:

* :class:`Info` : camera information and available features
* :class:`Temperature` : cooler control
* :class:`Shutter` : shutter control
* :class:`EM`: electron-multiplying gain control
* :class:`Detector`: CCD control, including:

  - :class:`VSS`: vertical shift speed
  - :class:`HSS`: horizontal shift speed
  - :class:`ADC`: analog-to-digital converter
  - :class:`OutputAmp`: the output amplifier
  - :class:`PreAmp`: pre-amplifier control

* :class:`ReadMode`: select the CCD read-out mode (full frame, vertical binning, tracks, etc.)
* :class:`Acquire <AcqMode>`: control the acquisition mode (single shot, video, accumulate, kinetic)

:Examples:

>>> from andor2 import Andor
>>> cam = Andor()
>>> cam.Temperature.setpoint = -74  # start cooling
>>> cam.Temperature.cooler = True  
>>> cam.Detector.OutputAmp(1)       # use conventional CCD amplifier instead of electron multiplying
>>> cam.PreAmp(2)                   # set pre-amplifier gain to 4.9
>>> cam.exposure = 10               # set exposure time to 10 ms
>>> cam.ReadMode.SingleTrack(590,5) # set readout mode: single track, 5 pixels wide, centered at 590 pixels

>>> cam.Acquire.Video()             # set acquisition mode to video (continuous)
>>> data = cam.Acquire.Newest(10)   # collect latest 10 images as numpy array
>>> cam.Acquire.stop()

>>> cam.Acquire.Kinetic(10, 0.1, 5, 0.01)    # set up kinetic sequence of 10 images every 100ms
                                             # with each image being an accumulation of 5 images
                                             # taken 10ms apart
>>> cam.Acquire.start()                      # start acquiring
>>> cam.Acquire.wait()                       # block until acquisition terminates
>>> data = cam.Acquire.GetAcquiredData()     # collect all data

-----------

"""

# When compile, we get a 'warning: #warning "Using deprecated NumPy API"'
# This is a Cython issue, see https://mail.python.org/pipermail/cython-devel/2014-June/004048.html
 
import numpy as np
import ctypes
#cimport numpy as np
#np.import_array()

import time
try:
  import tkinter
except ImportError: #python2
  import Tkinter as tkinter

#import h5py

#cimport cython
#cimport atmcdLXd as sdk   # Andor SDK definition file

import andorSDK as sdk

# Try importing Andor's own python wrapper
try:
  import atmcd
  WITH_ATMCD = True
except ImportError:
  WITH_ATMCD = False
  
def _initialize(library_path = None):# "/usr/local/etc/andor/"):
  sdk.Initialize(library_path)
  
def _shutdown():
  sdk.ShutDown()
    
def AvailableCameras():
  """Return the total number of Andor cameras currently installed.
  
  It is possible to call this function before any of the cameras are initialized.
  """
  totalCameras = ctypes.c_int32(0)
  sdk.GetAvailableCameras(ctypes.byref(totalCameras))
  return totalCameras.value
  
def while_acquiring(func):
  """Decorator that allows calling SDK functions while the camera is
  acquiring in Video mode (acquisition will stopped and restarted).
  """
  def decorated_function(*args, **kwargs):
    self = args[0]
    try:
      output = func(*args, **kwargs)
    except sdk.AndorError as error:
      print(error)
      if error.error is 20072 and self._cam.Acquire._name is 'Video':
        sdk.AbortAcquisition()
        func(*args, **kwargs)
        sdk.StartAcquisition()
      else:
        raise error
  return decorated_function
  
def rollover(func):
  """ Decorator that correct for the ADC roll-over by replacing zeros
  with 2**n-1 in image data.
  """
  def inner(*args, **kwargs):
    self = args[0]
    data = func(*args, **kwargs)
    if self.rollover:
      dynamic_range = 2**self._cam.Detector.bit_depth - 1
      data[data==0] = dynamic_range
    return data
  return inner
  
class Andor(object):
  """High-level, object-oriented interface for Andor cameras (SDK v2).
  
  :Usage: 
   
  The UI contains the following objects, most of which are self-explanatory:
  
  - :class:`Info` : camera information and available features
  - :class:`Temperature` : cooler control
  - :class:`Shutter` : shutter control
  - :class:`EM`: electron-multiplying gain control
  - :class:`Detector`: CCD control, including:
  
    - :class:`VSS`: vertical shift speed
    - :class:`HSS`: horizontal shift speed
    - :class:`ADC`: analog-to-digital converter
    - :class:`OutputAmp`: the output amplifier
    - :class:`PreAmp`: pre-amplifier control
    
  - :class:`ReadMode`: select the CCD read-out mode (full frame, vertical binning, tracks, etc.)
  - :class:`Acquire <AcqMode>`: control the acquisition mode (single shot, video, accumulate, kinetic)
    
  Upon initialisation, the camera is set by default to:
    - Acquisition mode: single shot
    - Readout mode: full image
    - EM gain: off
    - Vertical shift speed: maximum recommended
    - Horizontal shift speed: second fastest.
  """
  
  def __init__(self, init=True, lib=None):#"/usr/local/etc/andor/"):
    """Initialize the camera and returns a user-friendly interface. 
    
    :param bool init:  set to False to skip the camera initialisation
                       (if it has been initialised already).
    :param lib: location of the Andor library.
    """
    if init:
      sdk.Initialize(lib)
    self._cam = self
    self.Info = Info()
    self.Temperature = Temperature(self)
    try:
      self.Shutter = Shutter(self)
    except sdk.AndorError:
      self.Shutter = None
      
    self.EM = EM(self)
    self.Detector = Detector()
    self.ReadMode = ReadModes(self.Info.capabilities._ReadModes, {"_cam": self})
    self._AcqMode = AcqModes(self.Info.capabilities._AcqModes, {"_cam": self})
    self._TriggerMode = TriggerModes(self.Info.capabilities._TriggerModes, {"_cam": self})

    self.TriggerMode = self._TriggerMode.External #External
    self.TriggerMode()
    # Set up default modes: Single Acq, Image
    self.ReadMode.Image()
    self.Acquire = self._AcqMode.Single
    self.Acquire()#start=False)
    
    
  def __del__(self):
    self.Acquire.stop()
    try:
      self.Shutter.Close()
    except AttributeError:
      pass
    sdk.ShutDown()
  
  @property
  def exposure(self):
    """Query or set the exposure time, in ms."""
    t = self.acquisitionTimings
    return t['exposure'] * 1000.0
  @exposure.setter
  @while_acquiring
  def exposure(self, value):
      sdk.SetExposureTime(ctypes.c_float(value/1000.0))

  @property 
  def acquisitionTimings(self):
    """Returns the actual exposure, accumulation and kinetic cycle times, in seconds."""
    exp = ctypes.c_float()
    acc = ctypes.c_float()
    kin = ctypes.c_float()
    sdk.GetAcquisitionTimings(ctypes.byref(exp), ctypes.byref(acc), ctypes.byref(kin))
    return {'exposure': exp.value, 'accumulate': acc.value, 'kinetic': kin.value}
  
  def _gui(self, tkcanvas):
    """ add options to a frame for the spectrometer, which are the temperature, acquisition time and read mode """
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}
    
    # for exposure
    self.frames += [tkinter.LabelFrame(self.frames[0],text='exposure')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1
    
    temp = tkinter.Label(self.frames[-1], text='Exposure [ms]')
    temp.grid(row=0, column=0)
    self.text += [temp]

    self.inp['exposure'] = tkinter.DoubleVar()
    self.inp['exposure'].set(self.exposure)
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['exposure'])
    temp.grid(row=0, column=1)
    self.text += [temp]

    # radio for read mode
    self.frames += [tkinter.LabelFrame(self.frames[0],text='ReadMode')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    #find all the necessary values based off of the _AddCapability object
    temp = [i for i in self.ReadMode.__dict__ if i != 'current']
    readmode = [i for i in temp if self.ReadMode.__dict__['current'] is self.ReadMode.__dict__[i]][0]
    # current is the currently selected (used for instantiation of the radio)
    self.inp['readmode'] = tkinter.StringVar()
    self.inp['readmode'].set(readmode)

    for text in temp:
      self.text += [tkinter.Radiobutton(self.frames[-1],
                                        text=text,
                                        variable = self.inp['readmode'],
                                        value=text,
                                        command=lambda text=text:self.ReadMode.__dict__[text]._gui(tkinter.Toplevel()))]
      self.text[-1].pack(anchor=tkinter.W)

    #self.ReadMode.__dict__[self.inp['readmode'].get()]._gui(tk.Toplevel())
    
    # radio for acq mode
    self.frames += [tkinter.LabelFrame(self.frames[0],text='AcqMode')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1
    
    temp = [i for i in self._AcqMode.__dict__ if i != 'current']
    acqmode = [i for i in temp if self._AcqMode.__dict__['current'] is self._AcqMode.__dict__[i]][0]
    self.inp['acqmode'] = tkinter.StringVar()
    self.inp['acqmode'].set(acqmode)
    for text in temp:
      self.text += [tkinter.Radiobutton(self.frames[-1],
                                        text=text,
                                        variable = self.inp['acqmode'],
                                        value=text)]
      self.text[-1].pack(anchor=tkinter.W)

    self.Acquire = self._AcqMode.__dict__[self.inp['acqmode'].get()]
    #self.Acquire._gui(tinterk.Toplevel())

    self.frames[0].pack()
    
class Info(object):
  """Information about the camera.
  
  Includes:
     - serial number
     - controller card model
     - capabilities (see :class:`Capabilities` for details)
  """
  def __init__(self):
    serial = ctypes.c_int32()
    sdk.GetCameraSerialNumber(ctypes.byref(serial))
    self.serial_number = serial.value
    
    controllerCardModel = ctypes.create_string_buffer(b"          ")
    sdk.GetControllerCardModel(controllerCardModel)
    head = ctypes.create_string_buffer(256)
    sdk.GetHeadModel(head)

    self.head_model = head.value
    self.controller_card = controllerCardModel.value
    self.capabilities = Capabilities()
    #... more to come
    
  def __repr__(self):
    return "<Andor %s %s camera, serial number: %d>" % (self.capabilities.CameraType, self.head_model, self.serial_number)

  def _gui(self, tkcanvas):
    """Display attributes"""
    self.frames = [tkinter.Label(tkcanvas,text=self.__repr__())]
    self.frames[0].pack()
  
class OutputAmp(object):
  """The output amplifier.
  
  Some cameras have a conventional CCD amplifier in addition to the EMCCD amplifier, 
  although often the EMCCD amplifier is used even with the gain switched off, 
  as it is faster.
  """
  def __init__(self):
    self._active = 0
    self.__call__(0)
  
  def __repr__(self):
    return "<Currently active amplifier: " + self.description()+ ". Number of available amplifiers: "+ str(self.number)+'>'
  
  @property
  def number(self):
    """Returns the number of available amplifiers."""
    noAmp = ctypes.c_int32()
    sdk.GetNumberAmp(ctypes.byref(noAmp))
    return noAmp.value

  @property
  def max_speed(self):
    """ Maximum available horizontal shift speed for the amplifier currently selected."""
    speed = ctypes.c_int32()
    sdk.GetAmpMaxSpeed(self._active, ctypes.byref(speed))
    return speed.value
  
  def __call__(self, amp):
    """Set the output amplifier
    0: Standard EMCCD (default)
    1: Conventional CCD (if available)
    """
    amp = ctypes.c_int32(amp)
    sdk.SetOutputAmplifier(amp)
    self._active = amp.value
    
  @property
  def active(self):
    """Return the index of the current output amplifier."""
    return self._active

  def description(self, index=None):
    """ Return a string with the description of the currently selected amplifier.
    
    Options:
    - index: select a different amplifier
    """
    length = 21
    name = ctypes.create_string_buffer(length) # init char with length 21
    if index == None: 
      index = self._active
    sdk.GetAmpDesc(index, name, length) #UPDATE?
    print(name)
    return name.value.decode('ascii')   

  def _gui(self, tkcanvas):
    
    """ add options to a frame for the spectrometer, sets the amplifier via a button"""
    self.frames = []
    self.frames += tkinter.LabelFrame(tkcanvas, text='OutputAmp')
    self.text = []
    self.inp = {}
    self.row = 0

    if self.number != 1:
      text1 = 'Standard EMCCD'
      text0 = 'Conventional CCD (default)'
      self.inp['outputamp'] = tkinter.DoubleVar()
      self.inp['outputamp'] = self._active
      
      self.text += [tkinter.Radiobutton(self.frames[0],
                                        text=text0,
                                        variable = self.inp['outputamp'],
                                        value=0)]
      self.text[-1].pack(anchor=tkinter.W)
      self.row += 1
      self.text += [tkinter.Radiobutton(self.frames[0],
                                        text=text1,
                                        variable = self.inp['outputamp'],
                                        value=1)]
      self.text[-1].pack(anchor=tkinter.W)
      self.row += 1

      self.Acquire = self._AcqMode.__dict__[self.inp['acqmode'].get()]
      self.Acquire._gui(tk.Toplevel())

    else:
      self.text += [tkinter.Label(self.frames[0], text='Only one amplifier available')]
      self.text[-1].pack()
    self.frames[0].pack(fill=tkinter.X)
    

class HSS(object):
  """Controls the horizontal shift speed.  
  
  The HSS depends on the *output amplifier* (which must be passed to the constructor)
  and on the analog-to-digital converters (which is created within the HSS object).
  
  :Usage:
  
  >>> print hss.speeds  # query available settings
  >>> hss(0)            # set speed to hss.speeds[0]
  
  """
  # might be a good idea to not call the SDK functions every time...
  def __init__(self, OutAmp):
    """:param OutAmp: :class:`OutputAmp` instance."""
    self.ADC = ADC(self)
    self.OutputAmp = OutAmp
    self.__call__(0) # default to second fastest speed.
    self.choose = self.__call__
    self.list_settings = []
    self.ADC.ADConverters = self.ADC.list_ADConverters()
    
  @property 
  def info(self):
    return self.__repr__()
 
  @property
  def number(self):
    """Return the number of HS speeds available."""
    noHSSpeed = ctypes.c_int32()
    sdk.GetNumberHSSpeeds(self.ADC.channel, self.OutputAmp.active, ctypes.byref(noHSSpeed))
    return noHSSpeed.value
  
  @property
  def speeds(self):
    """Return a dictionary of available speeds {index: speed (MHz),... }."""
    speed = ctypes.c_float()
    HSSpeeds = {}
    for index in range(self.number):
      sdk.GetHSSpeed(self.ADC.channel, self.OutputAmp.active, index, ctypes.byref(speed))
      HSSpeeds[index] = speed.value
    return HSSpeeds
      
  def __repr__(self):
    return "<Horizontal shift speed value: %fMHz. Possible values: %s>" % (self.current, self.speeds)
      
  def __call__(self, index=None):
    """Set the speed to that given by the index, or let the user choose from menu."""
    if index is None:
      print("Select horizontal shift speed values from: ")
      print(self.speeds)
      choice = input('> ')
    else:
      choice = index
    sdk.SetHSSpeed(self.OutputAmp.active, choice)
    self.current = self.speeds[choice]

    
  def _gui(self, tkcanvas):
    """ add options to a frame for the spectrometer, which which sets a radio button for the horizontal shift speed"""
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas, text='HSS')]
    self.text = []
    self.inp = {}
    self.row = 0

    self.inp['speeds'] = tkinter.IntVar()
    temp = [(str(self.speeds[i]),i) for i in self.speeds]
    
    self.inp['speeds'].set([i for i in range(len(self.speeds)) if self.speeds[i] == self.current][0])
    
    for text, mode in temp:
      self.text += [tkinter.Radiobutton(self.frames[0],
                                        text=text,
                                        variable = self.inp['speeds'],
                                        value=mode,
                                        command=lambda mode=mode: self(mode))]
      self.text[-1].pack(anchor=tkinter.W)
      self.row += 1

    #print(self.inp['speeds'].get())
    #self.__call__(self.inp['speeds'].get())
    

    self.frames[0].pack(fill=tkinter.X)

class VSS(object):
  """Controls the vertical shift speed (VSS).
  
  Upon initialisation, it defaults to the fastest recommended speed.
  Call the class with no arguments to select a different speed.
  
  :Usage:
  
  >>> vss.speeds      # Available settings
  >>> vss(7)          # Set speed to no 7 (fastest)
  >>> vss.voltage = 4 # Increase clock voltage to redude CIC noise at high speed.
  
  """
  def __init__(self):
    noVSSpeed = ctypes.c_int32()
    sdk.GetNumberVSSpeeds(ctypes.byref(noVSSpeed))
    #: Number of available settings
    self.number = noVSSpeed.value
    #: Available settings
    self.speeds = {}
    speed = ctypes.c_float()
    for index in range(noVSSpeed.value):
      sdk.GetVSSpeed(index, ctypes.byref(speed))
      self.speeds[index] = speed.value
    self._fastestRecommended = self.fastestRecommended
    self.__call__(index=self._fastestRecommended["index"])
    self.choose = self.__call__
    self._voltage = 0
      
  def __repr__(self):
    return "<Current vertical shift speed: "+ str(self.current) + "us. \nPossible values : " + str(self.speeds) + "\nMax Recommended: "+str(self.fastestRecommended)+'>'
    
  @property 
  def info(self):
    return self.__repr__()
    
  def __call__(self, index=None):
    """Set the speed to that given by the *index*, or choose from a menu."""
    if index is None:
      print("Select vertical shift speed values (in us) from: ")
      print(self.speeds)
      choice = input('> ')
    else:
      choice = index

    sdk.SetVSSpeed(choice)
    self.current = self.speeds[choice]
  
  @property
  def fastestRecommended(self):
    """Query the fastest recommended speed (in us)."""
    index = ctypes.c_int32()
    speed = ctypes.c_float()
    sdk.GetFastestRecommendedVSSpeed(ctypes.byref(index), ctypes.byref(speed))
    return {"index": index.value, "speed": speed.value}
  
  @property
  def voltage(self):
    """Set or query the vertical clock voltage.
    
    If you choose a high readout speed (a low readout time), then you should also consider
    increasing the amplitude of the Vertical Clock Voltage.
    There are five levels of amplitude available for you to choose from:
    Normal (0); +1, +2, +3, +4.
    Exercise caution when increasing the amplitude of the vertical clock voltage, since higher
    clocking voltages may result in increased clock-induced charge (noise) in your signal. In
    general, only the very highest vertical clocking speeds are likely to benefit from an
    increased vertical clock voltage amplitude.
    """
    return self._voltage
  
  @voltage.setter
  def voltage(self, v):
    sdk.SetVSAmplitude(v)
    self._voltage = v

  def _gui(self, tkcanvas):
    
    """ add options to a frame for the spectrometer, which sets a radio button for the vertical shift speed"""
    self.frames += [tkinter.LabelFrame(tkcanvas, text='VSS')]
    self.text = []
    self.inp = {}

    self.inp['speeds'] = tkinter.DoubleVar(self.current)
    temp = [(str(self.speeds[i]),i) for i in self.speeds]
    
    for text, mode in temp:
      self.text += [tkinter.Radiobutton(self.frames[0],
                                        text=text,
                                        variable = self.inp['speeds'],
                                        value=mode)]
      self.text[-1].pack(anchor=tkinter.W)

    #ADD VOLTAGE SETTING EVENTUALLY

    self(self.inp['speeds'].get())
    
    self.frames[0].pack(fill=tkinter.X)
   
         
class ADC(object):
  """The analog-to-digital converter.
  
  Some cameras have more than one ADC with a different dynamic range (e.g. 14 and 16 bits). 
  The choice of ADC will affect the allowed horizontal shift speeds: see the ADConverters
  property for a list of valid comninations.
  
  :Usage:
  
  >>> adc.bit_depth   # dynamic range with current setting
  >>> adc.channel     # currently selected ADC
  >>> adc.channel = 1 # select other ADC
  """
  def __init__(self, HSS=None):
    self.HSS = HSS
    self.channel = 0
    # Don't finalise initialisation here as HSS.__init__() may not have completed yet!
  
  def list_ADConverters(self):
    adc = []
    current_channel = self.channel
    for i in range(self.number):
      self.channel = i
      if self.HSS is None:
        adc.append({"index": i, "bit_depth": self.bit_depth})
      else:
        adc.append({"index": i, "bit_depth": self.bit_depth, "HSSpeeds": self.HSS.speeds})
    self.channel = current_channel
    return adc
      
  @property
  def number(self):
    """Returns the number of analog-to-digital converters."""
    chans = ctypes.c_int32()
    sdk.GetNumberADChannels(ctypes.byref(chans))
    return chans.value    
  
  @property
  def channel(self):
    """Set or query the currently selected AD converter."""
    return self._channel

  @channel.setter
  def channel(self, chan):
    sdk.SetADChannel(chan)
    self._channel = chan
    
  @property
  def bit_depth(self):
    """Returns the dynamic range of the currently selected AD converter."""
    depth = ctypes.c_int32()
    sdk.GetBitDepth(self._channel, ctypes.byref(depth))
    return depth.value
    
  def __repr__(self):
    return "Currently selected A/D converter: "+ str(self.channel) +" ("+str(self.bit_depth) + " bits).\nPossible settings are: " + str(self.ADConverters)

  def _gui(self, tkcanvas):        
    """ add options to a frame for the spectrometer, which addresses the ADC level"""
    self.frames += [tkinter.LabelFrame(tkcanvas, text='ADC')]
    self.text = []
    self.inp = {}

    if self.number > 1:
      self.inp['ADC'] = tkinter.IntVar(self.channel)
      temp = [(str(i['bit_depth']),i['index']) for i in self.list_ADConverters()]
      for text, mode in range(temp):
        self.text += [tkinter.Radiobutton(self.frames[0],
                                          text=text,
                                          variable = self.inp['ADC'],
                                          value=mode)]
        self.text[-1].pack(anchor=tkinter.W)
      
        self.channel(self.inp['ADC'].get())

    else:
      self.text += [tkinter.Label(self.frames[0],text='Bit depth value fixed:'+str(self.bit_depth)+ ' bit')]  
      
    self.frames[0].pack(fill=tkinter.X)
                    
class EM(object):
  """ Controls the electron multiplying gain.
  
  :Usage:
  
  >>> EMGain.on()       # Turn EM gain on 
  >>> EMGain.gain = 123 # Set gain
  >>> EMGain.off()       # Turn EM gain off
  
  **Note:** setting the gain to 0 is the same as switching it off.
  """
  def __init__(self, cam):
    self._cam = cam
    current = self._read_gain_from_camera(readonly=False) # read current setting and set software parameters
    self.modes = {"default": 0, "extended": 1, "linear": 2, "real": 3}
    self._mode = self.modes["default"]
  
  @property
  def range(self):
    """Query the range of valid EM gains."""
    low = ctypes.c_int32()
    high = ctypes.c_int32()
    sdk.GetEMGainRange(ctypes.byref(low), ctypes.byref(high))
    return (low.value, high.value)

  def _read_gain_from_camera(self, readonly = True):
    value = ctypes.c_int32()
    sdk.GetEMCCDGain(ctypes.byref(value))
    if not readonly: 
      # reset software value of sensor gain
      self._switch = (value.value > 0)
      self._gain = value.value
    return value.value
    
  @property
  def gain(self):
    """Set or query the current setting."""
    return self._gain

  @gain.setter
  @while_acquiring
  def gain(self, value):
    self._gain = value
    # only update the sensor gain if EM gain is ON:
    if self._switch:
      sdk.SetEMCCDGain(value)
  
  def __call__(self, gain=None):
    """Set or query the current setting."""
    if gain is None:
      return self.gain
    else:
      self.gain = gain
  
  @while_acquiring  
  def on(self):
    """Turn on the EM gain."""
    sdk.SetEMCCDGain(self._gain)
    self._switch = True
  
  @while_acquiring  
  def off(self):
    """Turn off the EM gain."""
    sdk.SetEMCCDGain(0)
    self._switch = False
    
  @property
  def is_on(self):
    """Query whether the EM gain is on."""
    return self._switch

  @is_on.setter
  def is_on(self, state):
    if state:
      self.on()
    else:
      self.off()
    
  def __repr__(self):
    if self._switch:
      return "EMCCD gain is ON, gain value: " + str(self.gain) + "."
    else:
      return "EMCCD gain is OFF."
  
  @property
  def status(self):
    return self.__repr__()
    
  @property
  def advanced(self):
    """Turns on and off access to higher EM gain levels.
    
    Typically optimal signal to noise ratio and dynamic range is achieved between x1 to x300 EM Gain.
    Higher gains of > x300 are recommended for single photon counting only. Before using
    higher levels, you should ensure that light levels do not exceed the regime of tens of
    photons per pixel, otherwise accelerated ageing of the sensor can occur.
    """
    return self._advanced
  
  @advanced.setter
  def advanced(self, state):
    state2 = ctypes.c_int32(int(state))
    sdk.SetEMAdvanced(state2)
    self._advanced = state
    
  @property
  def mode(self):
    """The EM Gain mode can be one of the following possible settings:
    
    - 0: The EM Gain is controlled by DAC settings in the range 0-255. Default mode.
    - 1: The EM Gain is controlled by DAC settings in the range 0-4095.
    - 2: Linear mode.
    - 3: Real EM gain
    
    To access higher gain values (if available) it is necessary to enable advanced EM gain,
    see SetEMAdvanced.
    """
    return self._mode

  @mode.setter
  def mode(self, mode):
    if isinstance(mode, str):
      value = self.modes[mode]
    else:
      value = mode
    sdk.SetEMGainMode(value)
    self._mode

    
  def _gui(self, tkcanvas):
    """ add options to a frame for the spectrometer, gain mode, turn on and off gain, and gain level"""
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}
    # turn on and off gain

    
    # for gain oin off
    self.frames += [tkinter.LabelFrame(self.frames[0], text='EM gain on/off')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    self.text += [tkinter.Button(self.frames[-1], text='EM on/off', command=self)]
    self.text[-1].pack()

    # for gain
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Gain')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    temp = tkinter.Label(self.frames[-1], text='Gain:')
    temp.grid(row=0, column=0)
    self.text += [temp]

    self.inp['gain'] = tkinter.DoubleVar()
    self.inp['gain'].set(self.gain)
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['gain'])
    temp.grid(row=0, column=1)
    self.text += [temp]

    # radio for read mode
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Gain Mode')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    #find all the necessary values based off of the _AddCapability object
    # current is the currently selected (used for instantiation of the radio)
    temp
    self.inp['gainmode'] = tkinter.DoubleVar()
    self.inp['gainmode'].set(self.mode)

                         
    for vals in range(len(temp)):
      self.text += [tkinter.Radiobutton(self.frames[-1],
                                        text=str(vals),
                                        variable = self.inp['gainmode'],
                                        value=vals)]
      self.text[-1].pack(anchor=tkinter.W)
                      
    
      self.frames[0].pack()
    
class Temperature(object):
  """Manages the camera cooler. 
  
  Default temperature setpoint is 0C.
  """
  def __init__(self, cam, setpoint=0):
    self._cam = cam
    self._setpoint = setpoint
    self._cooler = None
    
  @property
  def range(self):
    """Return the valid range of temperatures in centigrade to which the detector can be cooled."""
    tmin = ctypes.c_int32()
    tmax = ctypes.c_int32()

    sdk.GetTemperatureRange(ctypes.byref(tmin), ctypes.byref(tmax))
    return (tmin.value, tmax.value)
  
  @property
  def precision(self):
    """Return the number of decimal places to which the sensor temperature can be returned.""" 
    precision = ctypes.c_int32()
    sdk.GetTemperaturePrecision(ctypes.byref(precision))#, ignore = (sdk.DRV_NOT_SUPPORTED,))
    return precision.value
    
  @property
  def setpoint(self):
    """Return the current setpoint."""
    return self._setpoint
  
  @setpoint.setter
  def setpoint(self, value):
    """Change the setpoint."""
    tmin,tmax = self.range()
    value = max(tmin, min(value, tmax)) #force value between ends
    sdk.SetTemperature(int(value))
    self._setpoint = value
    
  @property
  def read(self):
    """Returns the temperature of the detector to the nearest degree, and the status of cooling process."""
    value = ctypes.c_int32()
    error_code = sdk.GetTemperature(ctypes.byref(value))
    #andorError(error_code, ignore={ERROR_CODE[k] for k in TEMPERATURE_MESSAGES}) #UPDATE
    return {"temperature": value.value, "status": sdk.error[error_code]}
  
  @property
  def cooler(self):
    """Query or set the state of the TEC cooler (True: ON, False: OFF)."""
    state = ctypes.c_int32()
    try:
      sdk.IsCoolerOn(ctypes.byref(state)) # returns 1 if on, 0 if off
    except AttributeError:
      if self._cooler is None:
        sdk.CoolerOFF() #Since we don't know the status, force if off (for safety).
        self._cooler = 0
    return bool(state)
               
  @cooler.setter  
  def cooler(self, state):
    if state:
      sdk.CoolerON()
      self._cooler = 1
    else:
      sdk.CoolerOFF()
      self._cooler = 0
    
  def __repr__(self):
    return "Current temperature: " + str(self.read) + ", cooler: "+ ("ON" if self.cooler else "OFF") + ", setpoint: " + str(self.setpoint)+"."

  def _gui(self, tkcanvas):
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}
    
    # Cooler onoff
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Cooler')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    self.text += [tkinter.Button(self.frames[-1], text='Cooler on/off')]
    self.text[-1].pack()
    
    # Current Temp
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Current Temperature')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    self.text += [tkinter.Label(self.frames[-1], text='Temperature:'+str(self.read['temperature'])+' C')]
    self.text[-1].pack()

    # Set point value
    self.frames += [tkinter.LabelFrame(self.frames[0],text='Set Point [C] '+str(self.range[0])+'< temp <'+str(self.range[1]))]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1
    
    temp = tkinter.Label(self.frames[-1], text='Temperature [c]')
    temp.grid(row=0, column=0)
    self.text += [temp]

    self.inp['setpoint'] = tkinter.DoubleVar()
    self.inp['setpoint'].set(self.setpoint)
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['exposure'])
    temp.grid(row=0, column=1)
    self.text += [temp]
    
  
class PreAmp(object):
  """The pre-amplifier gain.
  
  Callable.
  
  :Usage:
  
  >>> preamp.gain # current setting
  >>> preamp()    # choose the gain from a menu
  """
  def __init__(self):
    #self._cam = cam
    #: Number of PreAmp settings available.
    self.number = self._number()
    self.gains = self.list_gains()
    self.__call__(0)
    self.choose = self.__call__
  
  def _number(self):
    """Number of PreAmp settings available."""
    noGains = ctypes.c_int32()
    sdk.GetNumberPreAmpGains(ctypes.byref(noGains))
    return noGains.value
  
  def list_gains(self):
    """Return a dictionary {index: gain, ...} of the available settings."""
    gain = ctypes.c_float()
    gain_list = {}
    for index in range(self.number):
      sdk.GetPreAmpGain(index, ctypes.byref(gain))
      gain_list[index] = gain.value
    return gain_list
  
  @while_acquiring
  def __call__(self, index=None):
    """Set the PreAmp gain. If no index is given, choose from a menu."""
    if index == None:
      print("Select PreAmp gain from: ")
      print(self.gains)
      choice = input('> ')
    else:
      choice = index
    sdk.SetPreAmpGain(choice)
    self._gain = {"index": choice, "value": self.gains[choice]}
    
  @property
  def gain(self):
    """Current pre-amplifier gain."""
    return self._gain["value"]
    
  def __repr__(self):
    return "Current PreAmp gain: x" + str(self.gain) + ". Possible settings: " + str(self.gains)

  def _gui(self, tkcanvas):
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}

    # radio for Preamp gain
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Pre-Amp Gain')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1

    # current is the currently selected (used for instantiation of the radio)
    self.inp['gain'] = tkinter.DoubleVar()
    self.inp['gain'].set(self.gain)

                         
    for text in range(len(self.gains)):
      self.text += [tkinter.Radiobutton(self.frames[-1],
                                        text=str(self.gains[text]),
                                        variable = self.inp['gain'],
                                        value=text)]
      self.text[-1].pack(anchor=tkinter.W)
                      
    self.frames[0].pack()  

class Shutter(object):
  """Controls the internal shutter.
  
  Use Open(), Closed() or Auto(), or Set(TTL, mode. closingtime openingtime) for custom operation.
  The opening/closing times ar set to minimum by default.
  """
  def __init__(self, cam):
    self._cam = cam
    isInstalled = ctypes.c_int32()
    sdk.IsInternalMechanicalShutter(ctypes.byref(isInstalled))
    self.installed = bool(isInstalled)
    self.transfer_times = self.MinTransferTimes
    self.mode = {"auto":0, "open": 1, "closed": 2, "open for FVB series": 4, "open for any series": 5}
    self.TTL_open = {"low":0, "high": 1}
    self.state = None
               
  @property 
  def MinTransferTimes(self):
    minclosingtime = ctypes.c_int32()
    minopeningtime = ctypes.c_int32()
    sdk.GetShutterMinTimes(ctypes.byref(minclosingtime), ctypes.byref(minopeningtime))
    return {"closing": minclosingtime.value, "opening": minopeningtime.value}
  
  def Set(self, mode, ttl=None, closingtime=None, openingtime=None):
    if ttl is None: ttl = self.TTL_open["high"]
    if closingtime is None: closingtime = self.transfer_times["closing"]
    if openingtime is None: openingtime = self.transfer_times["opening"]
    sdk.SetShutter(ttl, mode, closingtime, openingtime)
  
  @while_acquiring
  def Open(self):
    self.Set(self.mode["open"])
    self.state = "open"
  
  @while_acquiring
  def Close(self):
    self.Set(self.mode["closed"])
    self.state = "closed"
    
  def Auto(self):
    self.Set(self.mode["auto"])
    self.state = "auto"
    
  def __repr__(self):
    return "Internal Shutter present and currently + self.state." if self.installed else "No internal shutter."

  def _gui(self, tkcanvas):
    """Display attributes"""
    self.frames = [tkinter.Label(tkcanvas,text=self.__repr__)]
    self.frames[0].pack()

  
class Detector(object):
  """Represents the EMCCD sensor.
  
  In addition to providing properties to access the pixel size (in um),
  sensor dimensions (in pixels), and bit depth, this class is also a container for:
  
    - the horizontal shift speed
    - the vertical shift speed
    - the output amplifier
    - the preamplifier
    - the A/D converter
  """
  # NOTE: actually the AD converter and output amp are not really part of the sensor, if we limit it to the 2D CCD array...
  def __init__(self):
    self.VSS = VSS()
    self.OutputAmp = OutputAmp()
    self.HSS = HSS(self.OutputAmp)
    self.ADC = self.HSS.ADC
    self.PreAmp = PreAmp() 
    self.size = self._size
    #: 
    self.pixel_size = self._pixel_size
  
  @property
  def _pixel_size(self):
    """Returns the dimension of the pixels in the detector in microns."""
    xSize = ctypes.c_float()
    ySize = ctypes.c_float()
    sdk.GetPixelSize(ctypes.byref(xSize), ctypes.byref(ySize))
    return (xSize.value, ySize.value)
    
  @property
  def _size(self):
    """Returns the size of the detector in pixels. The horizontal axis is taken to be the axis parallel to the readout register."""
    xpixels = ctypes.c_int32()
    ypixels = ctypes.c_int32()
    sdk.GetDetector(ctypes.byref(xpixels), ctypes.byref(ypixels))
    self.width = xpixels.value
    self.height = ypixels.value
    self.pixels = xpixels.value * ypixels.value
    return (xpixels.value, ypixels.value)
  
  @property
  def bit_depth(self):
    return self.ADC.bit_depth
    
  def __repr__(self):
    return "Andor CCD | "+str(self.size[0])+"x"+str(self.size[1]) +" pixels | Pixel size: " + str(self.pixel_size[0])+"x"+str(self.pixel_size[1]) +"um."


  def _gui(self, tkcanvas):
    """Display attributes"""
    self.frames = [tkinter.Label(tkcanvas,text=self.__repr__)]
    self.frames[0].pack()


# CAPABILITIES
# Upon initialisation, the camera capabilities are determined and only the valid ones 
# are made available.

class _AddCapabilities(object):
  """Populates a type of capabilities (ReadModes, AcqModes etc.) with only the modes that are available.
  
  :Usage:
  
  >>> self._capabilities = _Capabilities()
  >>> self.ReadMode = _AddCapabilities(self._capabilities._ReadModes, ref)
  >>> self.AcqMode = _AddCapabilities(self._capabilities._AcqModes)
  
  *ref* is a dict of {"string": object} tuple giving an optional object to insert as attribute 'string'
  """
  def __init__(self, caps, ref = {}):
    for c in caps:
      if c._available:
        setattr(c, c._typ, self) # include reference to higher-level class of the right type.
        for key, value in ref.items(): # add custom references
          setattr(c, key, value)
        setattr(self, c._name, c) # create Capability with the right name
    self.current = None
    
  @property 
  def info(self):
    """ Print user-friendly information about the object and its current settings. """
    return self.__repr__()
    
#Better to have a different class for each mode since they are not configured in the same way...

class Capability(object):
  """ A general class for camera capabilities.
  
  This is mostly a convenience class that allows to programmatically declare 
  the available capabilities.
  """
  def __init__(self, typ, name, code, caps):
    """
    :param typ: Capability type (eg ReadMode, AcqMode...)
    :param name: Capability name
    :param code: the Capability identifier (eg sdk.AC_READMODE_FVB)
    :param caps: the element of the Capability structure corresponding to typ (eg caps.ulReadModes)  
    """
    self._name = name # This will be the name as it appear to the user
    self._available = code > 0 and caps > 0
    self._code = code
    self._typ = typ

# ReadModes capabilities

class ReadModes(_AddCapabilities):
  """ This class is just container for the available ReadMode_XXX classes """
  # It's little more than an alias for _AddCapabilities
  def __init__(self, caps, ref = {}):
    super(ReadModes, self).__init__(caps, ref)
    self._index = {0:self.FullVerticalBinning.__call__,
                   1:self.MultiTrack.__call__,
                   2:self.RandomTrack.__call__,
                   3:self.SingleTrack.__call__,
                   4:self.Image.__call__}
    
  def __repr__(self):
    return "Current Read mode : " + self.current._name

  def __getitem__(self, num):
    return self._index[num]
    
    
class ReadMode(Capability):
  """Base class for ReadMode_XXX classes.
  
  .. seealso::
     
    - :class:` ReadMode_Image`
    - :class:`ReadMode_SingleTrack`
    - :class:`ReadMode_FullVerticalBinning`
    - :class:` ReadMode_MultiTrack`
    - :class:`ReadMode_RandomTrack`
     
  """
  #Doesn't do anything but makes the class hierachy more sensible. 
  def __init__(self, typ, name, code, caps):
    super(ReadMode, self).__init__(typ, name, code, caps)  

  def _gui(self, tkcanvas): #do nothing if called
    self.__call__() #assumes no necessary argument calls
    tkcanvas.destroy() #don't build the window
    
  def __call__(self): #for completeness sake.
    pass
    
class ReadMode_FullVerticalBinning(ReadMode):
  """Full Vertical Binning mode."""
  def __init__(self, typ, name, code, caps):
    super(ReadMode_FullVerticalBinning, self).__init__(typ, name, code, caps)
    
  def __call__(self):
    """Set the camera in FVB mode."""
    sdk.SetReadMode(0)
    self.ReadMode.current = self
    self.shape = [1]
    self.shape = self._cam.Detector.width
    self.pixels = self._cam.Detector.width
    
class ReadMode_SingleTrack(ReadMode):
  """Single Track mode."""
  def __init__(self, typ, name, code, caps):
    super(ReadMode_SingleTrack, self).__init__(typ, name, code, caps)
    
  def __call__(self, center, height):
    """Set and configure the Readout Mode to Single Track.
    
    :param center: position of track center (in pixel)
    :param height: track height (in pixels)
    """
    sdk.SetReadMode(3)
    sdk.SetSingleTrack(center, height)
    self._center = center
    self._height = height
    self._cam.ReadMode.current = self
    self.pixels = self._cam.Detector.width
    self.ndims = 1
    self.shape = [self._cam.Detector.width]
  
  @property
  def center(self):
    """Set or query the track center (can be called during acquisition)."""
    return self._center
  @center.setter
  @while_acquiring
  def center(self, center):
    sdk.SetSingleTrack(center, self.height)
    self._center = center
  
  @property
  def height(self):
    """Set or query the track height (can be called during acquisition)."""
    return self._height
  @height.setter
  @while_acquiring
  def height(self, height):
    sdk.SetSingleTrack(self.center, height)
    self._height = height
  
  @property
  def position(self):
    """Return a tuple (center, height)."""
    return (self.center, self.height)

  def _gui(self, tkcanvas):
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}
    
    # for exposure
    self.frames += [tkinter.LabelFrame(self.frames[0], text='Single Track')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1
    
    temp = tkinter.Label(self.frames[-1], text='Center')
    temp.grid(row=0, column=0)
    self.text += [temp]

    self.inp['center'] = tkinter.IntVar()
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['center'])
    temp.grid(row=0, column=1)
    self.text += [temp]    

    
    temp = tkinter.Label(self.frames[-1], text='Height')
    temp.grid(row=2, column=0)
    self.text += [temp]

    self.inp['height'] = tkinter.IntVar()
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['height'])
    temp.grid(row=2, column=1)
    self.text += [temp]    

    self.text += [tkinter.Button(self.frames[0], text='Close', command=tkcanvas.destroy)]
    self.text[-1].grid(row=3, column=0)
    
    self.text += [tkinter.Button(self.frames[0],
                                 text='Set',
                                 command=lambda: self(self.inp['center'].get(),
                                                      self.inp['height'].get()))]
    self.text[-1].grid(row=3, column=1)
    
    self.frames[0].pack()

    
  
class ReadMode_MultiTrack(ReadMode):
  """Multi-track mode."""
  def __init__(self, typ, name, code, caps):
    super(ReadMode_MultiTrack, self).__init__(typ, name, code, caps)
    
  def __call__(self, number, height, offset):
    """
    :param number: number of tracks
    :param height: height of tracks, in pixels
    :param offset: first track offset, in pixels
    """   
    sdk.SetReadMode(1)
    gap = ctypes.c_int32()
    bottom = ctypes.c_int32()
                                
    sdk.SetMultiTrack(number, height, offset, ctypes.byref(bottom), ctypes.byref(gap))
    self.number = number
    self.height = height
    self.offset = offset
    self.bottom = bottom.value
    self.gap = gap.value
    self._cam.ReadMode.current = self
    self.pixels = self._cam.Detector.width * self.number
    if self.number == 1:
      self.ndims = 1
      self.shape= [self._cam.Detector.width]
    else:
      self.ndims = 2
      self.shape= [self.number, self._cam.Detector.width]


  def _gui(self, tkcanvas):
    self.frames = []
    self.frames += [tkinter.LabelFrame(tkcanvas,text='Andor')]
    self.text = []
    self.row = 0
    self.inp = {}
    
    # for exposure
    self.frames += [tkinter.LabelFrame(self.frames[0],text='Multi Track')]
    self.frames[-1].grid(row=self.row, column=0)
    self.row += 1
    
    temp = tkinter.Label(self.frames[-1], text='Number')
    temp.grid(row=0, column=0)
    self.text += [temp]

    self.inp['number'] = tkinter.IntVar()
    #self.inp['center'].set(self.)
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['number'])
    temp.grid(row=0, column=1)
    self.text += [temp]    

    
    temp = tkinter.Label(self.frames[-1], text='Height')
    temp.grid(row=1, column=0)
    self.text += [temp]

    self.inp['height'] = tkinter.IntVar()
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['height'])
    temp.grid(row=1, column=1)
    self.text += [temp]    

    temp = tkinter.Label(self.frames[-1], text='Offset')
    temp.grid(row=2, column=0)
    self.text += [temp]

    self.inp['offset'] = tkinter.IntVar()
    temp = tkinter.Entry(self.frames[-1], textvariable=self.inp['offset'])
    temp.grid(row=2, column=1)
    self.text += [temp]    

    self.text += [tkinter.Button(self.frames[0], text='Close', command=tkcanvas.destroy)]
    self.text[-1].grid(row=3, column=0)
    
    self.text += [tkinter.Button(self.frames[0],
                                 text='Set',
                                 command=lambda: self(self.inp['number'].get(),
                                                      self.inp['height'].get(),
                                                      self.inp['offset'].get()))]
    self.text[-1].grid(row=3, column=1)
        
    self.frames[0].pack()
      

class ReadMode_RandomTrack(ReadMode):
  """RandomTrack mode."""
  def __init__(self, typ, name, code, caps):
    super(ReadMode_RandomTrack, self).__init__(typ, name, code, caps)
    
  def __call__(self, numTracks, areas):
    """Set the camera in RandomTrack mode.
    
    :param int numTracks: number of tracks:
    :param areas: track parameters: tuple (start1, stop1, start2, stop2, ...)
    """
    #cdef np.ndarray[np.int_t, mode="c", ndim=1] areasnp = np.ascontiguousarray(np.empty(shape=6, dtype = np.int))
    #cdef np.ndarray[np.int_t, mode="c", ndim=1] areasnp = np.ascontiguousarray(areas, dtype=np.int32)# np.int) #UPDATE

    areasnp = np.ascontiguousarray(areas, dtype=np.int32)

    sdk.SetReadMode(2) #UPDATE
    print(areasnp)
    sdk.SetRandomTracks(numTracks, ctypes.c_void_p(areasnp.ctypes.data))
    self.numTracks = numTracks
    self.areas = areas
    self._cam.ReadMode.current = self
    self.pixels = self._cam.Detector.width * self.numTracks
    if self.numTracks == 1:
      self.ndims = 1
      self.shape= [self._cam.Detector.width]
    else:
      self.ndims = 2
      self.shape= [self.numTracks, self._cam.Detector.width]
      
  def data_to_image(self, data):
    """Forms an image from Random Track data."""
    raise NotImplementedError

  def _gui(self, tkcanvas):
    self.frames = [tkinter.Label(tkcanvas,text='Random Track not accessible through this GUI interface')]
    self.frames[0].pack()
    self.frames += [tkinter.Label(tkcanvas,text='Please specify values in a setup/ save file')]
    self.frames[1].pack()

    
class ReadMode_Image(ReadMode):
  """Full image mode."""
  def __init__(self, typ, name, code, caps):
    super(ReadMode_Image, self).__init__(typ, name, code, caps)
    
  def __call__(self, binning=None, h=None, v=None, isolated_crop=False):
    """Set Readout mode to Image, with optional binning and sub-area coordinates.
    
    NOTE: binning and subarea not implemented yet. 
    
    :param binning: (hbin, vbin)
    :param h: (left, right) horizontal coordinates (in binned pixels)
    :param v: (top, bottom) vertical coordinates
    :param isolated_crop: ?
    :type isolated_crop: bool
    
    .. Warning:: this nay be buggy/not working
    
    """
    #NOTE: this is probably buggy 
    sdk.SetReadMode(4) #UPDATE
    # process **kwargs and set Image parameters if they are defined:  
    (hbin, vbin) = (1, 1) if binning is None else binning
    h = (1, self._cam.Detector.width) if h is None else h
    v = (1, self._cam.Detector.height) if v is None else v
    #(hsize, vsize) = self._cam.Detector.size if size is None else size
    #(h0, v0) = (1, 1) if lower_left is None else lower_left
    #if not None in (binning, size, lower_left):
    sdk.SetImage(hbin, vbin, h[0], h[1], v[0], v[1])
    #if isolated_crop:
    #  andorError(SetIsolatedCropMode(isolated_crop, hsize * hbin, vbin, hbin))
    
    self._cam.ReadMode.current = self
    self.shape = [h[1] - h[0] + 1, v[1] - v[0] + 1]
    self.pixels = self.shape[0] * self.shape[1]
    self.ndims = 2
    
    
# AcqModes capabilities
# The AcqMode class provide functions that are common to all modes (status, start, stop),
# while the AcqMode_XXX classes provide mode-specific functions (initialisation and doc)
# NOTE : the "typ" parameters could be removed here...
# To change the mode or change the parameters, just call the object:
# >>> main.AcqMode.Kinetic(params)
# The first call to an SDK function will raise an error if it can't be change, so we don't need to worry about that.
# Then to start the acquisition:
# >>> main.Acquire.start()
# >>> main.Acquire.status
# >>> main.Acquire.stop()
# main.Acquire is just a reference to the current AcqMode object.

class AcqModes(_AddCapabilities):
  """Container for the available AcqMode_XXX classes. """
  # It's little more than an alias for _AddCapabilities
  def __init__(self, caps, ref = {}):
    super(AcqModes, self).__init__(caps, ref)
    self.current = None
    
  def __repr__(self):
    return "Current Acquisition mode : " + self.current._name

  
class AcqMode(Capability):
  """Base class for acquisition modes AcqMode_XXX.
  
  .. seealso:
     
     - :class:`AcqMode_Video`
     - :class:`AcqMode_Single`
     - :class:`AcqMode_Accumulate`
     - :class:`AcqMode_Kinetic`

  """
  # The parent class for all acquisition modes. 
  # Includes methods to start/stop the acquisition and collect the acquired data
  def __init__(self, typ, name, code, caps):
    super(AcqMode, self).__init__(typ, name, code, caps)
    self.current = None
    self.rollover = False
    self.snapshot_count = 0
    self.last_snap_read = 0
    
    self._index = {1:self.Single,
                   2:self.Accumulate,
                   3:self.Kinetic,
                   5:self.Video}

  # Acquisition control

  def __getitem__(self, num):
    return self._index[num]
  
  @property
  def status(self):
    """Return the camera status code and corresponding message."""
    status = ctypes.c_int32(0)
    sdk.GetStatus(ctypes.byref(status))
    return status.value
  
  @property
  def running(self):
    """Query whether the camera is busy (ongoing acquisition or video).""" 
    if self.status is 20072:
      return True
    else:
      return False
  
  def start(self):
    """Start the acquisition."""
    sdk.StartAcquisition()
    self.start_time = time.time()
    self.snapshot_count += 1
    
  def stop(self):
    """Stop an ongoing acquisition."""
    sdk.AbortAcquisition()
    sdk.CancelWait() # I hope this doesn't throw an error
    
  def wait(self, new_data=False):
    """Wait either for new data to be available or for the whole acquisition sequence (default) to terminate.
    
    :param bool new_data: if True, pause until a new image is available in the buffer.
                     if False, pause until the whole acquisition terminates.
    
    Press :kbd:`Ctrl+C` to stop waiting.
    
    .. Warning:: This is not thread-safe!    
    """
    try:
      sdk.WaitForAcquisition()
      if not new_data:
        while self.status is 20072:
          sdk.WaitForAcquisition()
    except KeyboardInterrupt:
      pass
    
  def __call__(self):
    """Set the camera acquisition mode. 
    
    Called by sub-classes.
    """
    # Stuff to do for all modes when calling the method, namely set 'main.AcqMode.current' and 'main.Acquire' to the current mode
    self._cam._AcqMode.current = self
    self._cam.Acquire = self
    self.snapshot_count = 0
    
  @property
  def max_exposure(self):
    """Return the maximum settable exposure time, in seconds."""
    MaxExp = ctypes.c_float()
    sdk.GetMaximumExposure(ctypes.byref(MaxExp))
    return MaxExp.value
  
  # Data collection
  
  @property
  def size_of_circular_buffer(self):
    """Return the maximum number of images the circular buffer can store based on the current acquisition settings."""
    index = ctypes.c_int32()
    sdk.GetSizeOfCircularBuffer(ctypes.byref(index))
    return index.value
    
  @property
  def images_in_buffer(self):
    """Return information on the number of available images in the circular buffer.
    
   This information can be used with GetImages to retrieve a series of images. If any
   images are overwritten in the circular buffer they no longer can be retrieved and the
   information returned will treat overwritten images as not available.
   """
    #cdef sdk.at_32 first, last #UPDATE
    first = ctypes.c_int32()
    last = ctypes.c_int32()
    sdk.GetNumberAvailableImages(ctypes.byref(first), ctypes.byref(last))
    return {"first": first.value, "last": last.value}

  @property
  def new_images(self):
    """Return information on the number of new images (i.e. images which have not yet been retrieved) in the circular buffer.
    
    This information can be used with GetImages to retrieve a series of the latest images. 
    If any images are overwritten in the circular buffer they can no longer be retrieved
    and the information returned will treat overwritten images as having been retrieved.
    """
    #cdef sdk.at_32 first, last
    first = ctypes.c_int32()
    last = ctypes.c_int32()
    sdk.GetNumberNewImages(ctypes.byref(first), ctypes.byref(last))
    return {"first": first.value, "last": last.value}
      
  #@rollover
  def Newest(self, n=1, type=16):
    """Returns a data array with the most recently acquired image(s) in any acquisition mode.
    
    :param number: number of images to retrieve
    :param type: whether to return the data as 16 or 32-bits integers (16 [default] or 32)
    """

    if n == 1:
      npixels = self._cam.ReadMode.current.pixels
      if type == 16:
        data16 = np.ascontiguousarray(np.empty(shape=npixels, dtype=np.uint16))
        sdk.GetMostRecentImage16(ctypes.c_void_p(data16.ctypes.data), npixels) #HERE
        data = data16
      else:
        data32 = np.ascontiguousarray(np.empty(shape=npixels, dtype=np.int32))
        sdk.GetMostRecentImage(ctypes.c_void_p(data32.ctypes.data), npixels) #HERE BYREF CHANGE
        data = data32
      return data.reshape(self._cam.ReadMode.current.shape)
    elif n > 1:
      most_recent = self.images_in_buffer['last']
      return self.Images(most_recent - n + 1, most_recent, type=type)
    else:
      raise ValueError('Invalid number of images: ' + str(n))
      
  
  @rollover
  def Oldest(self, type=16):
    """Retrieve the oldest available image from the circular buffer.
    
    Once the oldest image has been retrieved it is no longer available,
    and calling GetOldestImage again will retrieve the next image.
    This is a useful function for retrieving a number of images.
    For example if there are 5 new images available, calling it 5 times will retrieve them all.
    
    :param type: whether to return the data as 16 or 32-bits integers (16 [default] or 32)
    """
    npixels = self._cam.ReadMode.current.pixels
    
    if type == 16:
      data16 = np.ascontiguousarray(np.empty(shape=npixels, dtype=np.uint16))
      sdk.GetOldestImage16(ctypes.c_void_p(data16.ctypes.data), npixels)
      return data16
    else:
      data32 = np.ascontiguousarray(np.empty(shape=npixels, dtype=np.int32))
      sdk.GetOldestImage(ctypes.c_void_p(data32.ctypes.data), npixels)
      return data32  
  
  @rollover
  def Images(self, first, last, type=16):
    """Return the specified series of images from the circular buffer.
    
    If the specified series is out of range (i.e. the images have been
    overwritten or have not yet been acquired) then an error will be returned.
    
    :param first: index of first image in buffer to retrieve.
    :param last: index of last image in buffer to retrieve.
    :param type: whether to return the data as 16 or 32-bits integers (default: 16)
    """
    nimages = last - first + 1
    pixels_per_image = self._cam.ReadMode.current.pixels
    total_pixels = nimages * pixels_per_image
    final_shape = [nimages] + self._cam.ReadMode.current.shape
    
    validfirst = ctypes.c_int32()
    validlast = ctypes.c_int32()
    
    if type == 16:
      data16 = np.ascontiguousarray(np.empty(shape=total_pixels, dtype=np.uint16))
      sdk.GetImages16(first, last, ctypes.c_void_p(data16.ctypes.data), total_pixels, ctypes.byref(validfirst), ctypes.byref(validlast))
      data = data16
    else:
      data32 = np.ascontiguousarray(np.empty(shape=total_pixels, dtype=np.int32))
      sdk.GetImages(first, last, ctypes.c_void_p(data32.ctypes.data), total_pixels, ctypes.byref(validfirst), ctypes.byref(validlast))
      data = data32
    self.valid = {'first': validfirst, 'last': validlast}
    return data.reshape(final_shape)

  @rollover
  def GetAcquiredData(self, type=16):
    """Return the whole data set from the last acquisition.
    
    GetAcquiredData should be used once the acquisition is complete to retrieve all the data from the series.
    This could be a single scan or an entire kinetic series.
    
    :param type: (16 or 32) whether to return the data as 16 or 32-bits integers (default: 16)
    """   
    pixels_per_image = self._cam.ReadMode.current.pixels
    nimages = self.nimages
    total_pixels = nimages * pixels_per_image
    final_shape = [nimages] + self._cam.ReadMode.current.shape
    
    if type == 16:
      data16 = np.ascontiguousarray(np.empty(shape=total_pixels, dtype = np.uint16))
      sdk.GetAcquiredData16(ctypes.c_void_p(data16.ctypes.data), total_pixels)
      data = data16
    else:
      data32 = np.ascontiguousarray(np.empty(shape=total_pixels, dtype = np.int32))
      sdk.GetAcquiredData(ctypes.c_void_p(data32.ctypes.data), total_pixels)
      data = data32
    self.last_acquired_data = data.reshape(final_shape) 
    return self.last_acquired_data

  def Video(self):
    """Switch to Video mode and start acquiring."""
    self = self._cam._AcqMode.Video
    self.__call__(start=False)
    
  def Kinetic(self, numberKinetics, kineticCycleTime, numberAccumulation = 1, accumulationCycleTime = 0, safe=True):
    """Switch to and configure Kinetic acquisition."""
    self = self._cam._AcqMode.Kinetic
    self.__call__(numberKinetics, kineticCycleTime, numberAccumulation, accumulationCycleTime,safe=safe)
  
  def Single(self):
    """Switch to Single mode."""
    #self.stop()
    self = self._cam._AcqMode.Single
    self.__call__()

  def Accumulate(self, numberAccumulation, accumulationCycleTime, safe=True):
    """Switch to and configure Accumulate acquisition."""
    self = self._cam._AcqMode.Accumulate
    self.__call__(numberAccumulation, accumulationCycleTime, safe=safe)

  def save(self, filename):
    """Save data to a .SIF Andor file

    :param string filename: name of the SIF file"""
    sdk.SaveAsSif(filename)

  def progress(self):
    progress = ctypes.c_int32()
    series = ctypes.c_int32()
    sdk.GetAcquisitionProgress(progress, series)
    return progress.value, series.value
    
    
  def saveHDF(self, filename, dataset, data, metadata_func=None):
    """Save data and associated metadata to an HDF5 file.
    
    :param string filename: name of the H5 file (must already exist).
    :param string dataset_name: name of the dataset (must not already exist).
    :param data: any HDF5 compatible data (eg cam.Acquire.Newest())
    
    The following metadata are also recorded: 
      - acquisition mode
      - exposure time
      - EM gain
      - time (string).
    """
    with h5py.File(filename, 'r+') as f:
      f.create_dataset(dataset, data=data)
      f[dataset].attrs['mode'] = self._name
      f[dataset].attrs['exposure'] = self._cam.exposure
      f[dataset].attrs['em_gain'] = self._cam.EM._read_gain_from_camera()
      f[dataset].attrs['created'] = time.strftime("%d/%m/%Y %H:%M:%S")
      if metadata_func is not None:
        metadata_func(f[dataset])
    
  def take_multiple_exposures(self, exposures):
    """Take a series of single images with varying exposure time.
    
    :param exposures: a tuple of exposure times.
    
    :returns: a numpy array of length len(exposures).
    """
    if self._name is "Video":
      video = True
      self.stop()
      self.Single()
    data = []
    for e in exposures:
      self._cam.exposure = e
      self.start()
      self.wait()
      data.append(self.Newest())
    if video:
      self.Video()
      self.start()
    return np.array(data)

  def _gui(self, tkcanvas):
    tkcanvas.destroy()
    
class AcqMode_Single(AcqMode):
  """ Set the camera in Single Acquisition mode.
  
  The snapshot_count counter is reset when Single() is called, 
  and incremented every time snap() (or equivalently start()) is called.
  
  Arguments: None
  """
  def __init__(self, typ, name, code, caps):
    super(AcqMode_Single, self).__init__(typ, name, code, caps)
    self.shape = []
    self.ndims = 0
    self.nimages = 1
    
  def __call__(self, safe=True):
    """Set the camera in Single Acquisition mode.
    
    :param bool safe: if False, any ongoing acquisition will be stopped;
                 if True (default) an error will be raised.
    """
    if not safe:
      self.stop()
    sdk.SetAcquisitionMode(1)
    super(AcqMode_Single, self).__call__()
    
  def __repr__(self):
    return "Snapshot acquisition mode."
    
    
  def snap(self, wait=True, type=16):
    """Take a single image. 
    
    :param wait: if True, wait for the acquisition to complete and return the data.
    :param type: (16 or 32) whether to return the data as 16 or 32-bits integers (default: 16)
    """
    self.start()
    if wait:
      self.wait()
      return self.Newest(type)
    
class AcqMode_Accumulate(AcqMode):
  """Set the camera in Accumulate mode.
  
  It's a good idea to retrieve the data as 32bits integers."""
  def __init__(self, typ, name, code, caps):
    #
    super(AcqMode_Accumulate, self).__init__(typ, name, code, caps)
    self.shape = []
    self.ndims = 0
    self.nimages = 1
    self.numberAccumulation = 0
    self._kinetic = False # whether the accumulation cycle is part of a kinetic sequence.
    
  def __call__(self, numberAccumulation, accumulationCycleTime, safe=True):
    """ Set the camera in Accumulate mode.
    
    :param int numberAccumulation: Number of accumulations
    :param int accumulationCycleTime: cycle time
    :param bool safe: if True, raises an error if an acquisition is ongoing.
    """
    if not safe:
      self.stop()
    if not self._kinetic:
      sdk.SetAcquisitionMode(2)
    sdk.SetNumberAccumulations(numberAccumulation)
    sdk.SetAccumulationCycleTime(accumulationCycleTime)
    self.numberAccumulation = numberAccumulation
    self.accumulationCycleTime = accumulationCycleTime
    super(AcqMode_Accumulate, self).__call__()
    
  def __repr__(self):
    return "Accumulate acquisition with settings: \n" + \
           "  Number of Accumulations: "+ str(self.numberAccumulation) +"\n" \
           "  Cycle time: "+ str(self._cam.acquisitionTimings['accumulate']) +"."
  
  def save(self, filename, dataset_name, metadata_func=None):
    """Save data and associated metadata from the last completed acquisition to an HDF5 file.
    
    :param string filename: name of the H5 file (must already exist).
    :param string dataset_name: name of the dataset (must not already exist).
    :param metadata_func: optional function to save more metadata. Takes a :class:`h5py.Group` as unique argument.
    
    The following metadata are also recorded: 
      - acquisition mode
      - exposure time
      - EM gain
      - time (string)
      - accumulation number and cycle time
    """
    def save_metadata(h5group, metadata_func=None):
      h5group.attrs['accumulate_cycle_time'] = self._cam.acquisitionTimings['accumulate']
      h5group.attrs['accumulate_number'] = self.numberAccumulation
      if metadata_func is not None:
        metadata_func(h5group)
    data = self.GetAcquiredData()
    super(AcqMode_Accumulate, self).save(filename, dataset_name, data, save_metadata)
    

class AcqMode_Video(AcqMode):
  """ Set the camera in Video (Run Till Abort) mode.
  
  Arguments: None
  """
  def __init__(self, typ, name, code, caps):
    super(AcqMode_Video, self).__init__(typ, name, code, caps)
    self.shape = []
    self.ndims = 0
    self.nimages = 1
    
  def __call__(self, start=False, live=False):
    sdk.SetAcquisitionMode(5)
    super(AcqMode_Video, self).__call__()
    if start:
      super(AcqMode_Video, self).start()
    if live:
      self._cam.Display.start()
      
  def __repr__(self):
    return "<Video acquisition mode>"

class AcqMode_Kinetic(AcqMode_Accumulate):
  """Kinetic mode. 

  Callable.
  """
  def __init__(self, typ, name, code, caps):
    super(AcqMode_Kinetic, self).__init__(typ, name, code, caps)
    self._kinetic = True
    self.numberKinetics = 0
    self.kineticCycleTime = 0
    
  def __call__(self, numberKinetics, kineticCycleTime, numberAccumulation = 1, accumulationCycleTime = 0, safe=True):
    """Set the camera in Kinetic mode.
    
    :param numberKinetics: number of images in kinetic sequence
    :param kineticCycleTime: : interval between images in kinetic sequence, in seconds
    :param numberAccumulation: number of images to accumulate for each image in the kinetic sequence
    :param accumulationCycleTime: interval between accumulated images, in seconds
    :param safe: set to False to cancel any ongoing acquisition.
    """
    if not safe:
      self.stop()
    sdk.SetAcquisitionMode(3)
    sdk.SetNumberKinetics(numberKinetics)
    sdk.SetKineticCycleTime(ctypes.c_float(kineticCycleTime))
    self.numberKinetics = numberKinetics
    self.kineticCycleTime = kineticCycleTime
    self.ndims = 1
    self.shape = [numberKinetics,]
    self.nimages = numberKinetics
    # Now call Accumulate()
    super(AcqMode_Kinetic, self).__call__(numberAccumulation, accumulationCycleTime, safe)
    
    # NOTE : Should check the value of GetAcquisitionTimings 
  
  def save(self, filename, dataset_name):
    """Save data and associated metadata from the last completed acquisition to an HDF5 file.
    
    :param string filename: name of the H5 file (must already exist).
    :param string dataset_name: name of the dataset (must not already exist).
    :param metadata_func: optional function to save more metadata. Takes a :class:`Group` as unique argument.
    
    The following metadata are also recorded: 
      - acquisition mode
      - exposure time
      - EM gain
      - time (string)
      - accumulation number and cycle time
      - Kineatic number and cycle time
    """
    def metadata_func(h5group):
      h5group.attrs['kinetic_cycle_time'] = self._cam.acquisitionTimings['kinetic']
      h5group.attrs['kinetic_number'] = self.numberKinetics
    # data will be collected by Accumulate.save()
    super(AcqMode_Kinetic, self).save(filename, dataset_name, metadata_func)
    
  
  def __repr__(self):
    if self.numberAccumulation > 1:
      acc_str = "  Number of Accumulation: " + str(self.numberAccumulation) + "\n" \
            + "  Accumulation cycle time: " + str(self.accumulationCycleTime)
    else:
      acc_str = "  No Accumulation"
    return("Kinetic acquisition with settings : \n" \
            + "  Number in Kinetic series: " + str(self.numberKinetics) + "\n" \
            + "  Kinetic cycle time: " + str(self.kineticCycleTime) + "\n" \
            + acc_str)       


class TriggerModes(_AddCapabilities):
  """ This class is just container for the available TriggerMode_XXX classes """
  # It's little more than an alias for _AddCapabilities
  def __init__(self, caps, ref = {}):
    super(TriggerModes, self).__init__(caps, ref)
        
  def __repr__(self):
    return "Current Trigger mode : " + self.current._name

  
class TriggerMode(Capability):
  
  def __init__(self, typ, name, code, caps, trigger_code):
    super(TriggerMode, self).__init__(typ, name, code, caps)
    self._inverted = False
    self._trigger_code = trigger_code
    self._index = {0:self.Internal,
                   1:self.External,
                   6:self.External_Start,
                   7:self.External_Exposure,
                   9:self.External_FVB}

  def __call__(self, fast=True):
    """Call with no argument to set the trigger mode."""
    self._cam._TriggerMode.current = self
    sdk.SetTriggerMode(self._trigger_code)
    self.fast(fast)

  @property
  def fast(self):
    return self._fast

  @fast.setter
  def fast(self, inp):
    self._fast = inp
    sdk.SetFastExtTrigger(int(inp))

  def __getitem__(self, num):
    self = self._index[num]
    self.__call__()
    
  @property
  def inverted(self):
    """This property will set whether an acquisition will be triggered on a rising (False, default) or falling (True) edge external trigger."""
    return self._inverted
  @inverted.setter
  def inverted(self, value):
    sdk.SetTriggerInvert(value)
    self._inverted = value
    
  def __repr__(self):
    return "<" + self._name + " Trigger>"

  def Internal(self):
    self = self._cam._TriggerModes.Internal
    self.__call__()

  def External(self):
    self = self.self._cam._TriggerModes.External
    self.__call__()
    
  def External_Start(self):
    self = self._cam._TriggerModes.External_Start
    self.__call__()
    
  def External_Exposure(self):
    self = self._cam._TriggerModes.External_Exposure
    self.__call__()
    
  def External_FVB(self):
    self = self._cam._TriggerModes.External_FVB
    self.__call__()
    
class Capabilities(object):
  """Container for camera capabilities.
  
  Retrieves and parses the SDK's AndorCapabilities struct, returning
  dictionaries indicating which capabilities are available.
  
  The following sets of capabilities are completely parsed:
    - ``AcqModes``
    - ``ReadModes``
    - ``ReadModesWithFrameTransfer``
    - ``TriggerModes``
    - ``CameraType``
    - ``PixelMode``
    - ``PCICard``
    - ``EMGain``
  
  The following are only partially parsed:
    - ``SetFunctions`` (see also ``Fan`` and ``Temperature``)
    - ``GetFunctions`` (see also ``Fan`` and ``Temperature``)
    - ``Features``
  
  and some of the relevant capabilities are present in the ``Fan`` 
  and ``Temperature`` dictionaries.

  Finally, when available, :class:`AcqMode`, :class:`ReadMode` and 
  :class:`TriggerMode` objects are created as the properties ``_AcqModes``,
  ``_ReadModes`` and ``_TriggerModes``.
  
  """
  # Should we initialise caps here?
  def __init__(self):
    #cdef sdk.AndorCapabilities caps
    #caps.ulSize = cython.sizeof(caps)
    caps = sdk.AndorCapabilities()
    caps.ulSize = 92
    sdk.GetCapabilities(ctypes.byref(caps))

    self.AcqModes = {"Single": sdk.acqMode['AC_ACQMODE_SINGLE'] & caps.ulAcqModes > 0, 
                     "Video": sdk.acqMode['AC_ACQMODE_VIDEO'] & caps.ulAcqModes > 0,
                     "Accumulate": sdk.acqMode['AC_ACQMODE_ACCUMULATE'] & caps.ulAcqModes > 0,
                     "Kinetic": sdk.acqMode['AC_ACQMODE_KINETIC'] & caps.ulAcqModes > 0,
                     "Frame transfer": sdk.acqMode['AC_ACQMODE_FRAMETRANSFER'] & caps.ulAcqModes > 0,
                     "Fast kinetics": sdk.acqMode['AC_ACQMODE_FASTKINETICS'] & caps.ulAcqModes > 0,
                     "Overlap": sdk.acqMode['AC_ACQMODE_OVERLAP'] & caps.ulAcqModes > 0}

    self.ReadModes = {"Full image": sdk.readMode['AC_READMODE_FULLIMAGE'] & caps.ulReadModes > 0,
                      "Subimage": sdk.readMode['AC_READMODE_SUBIMAGE'] & caps.ulReadModes > 0,
                      "Single track": sdk.readMode['AC_READMODE_SINGLETRACK'] & caps.ulReadModes > 0,
                      "Full vertical binning": sdk.readMode['AC_READMODE_FVB'] & caps.ulReadModes > 0,
                      "Multi-track": sdk.readMode['AC_READMODE_MULTITRACK'] & caps.ulReadModes > 0,
                      "Random track": sdk.readMode['AC_READMODE_RANDOMTRACK'] & caps.ulReadModes > 0,
                      "Multi track scan": sdk.readMode['AC_READMODE_MULTITRACKSCAN'] & caps.ulReadModes > 0}
    
    self.ReadModesWithFrameTransfer = {"Full image": sdk.readMode['AC_READMODE_FULLIMAGE'] & caps.ulFTReadModes > 0,
                                       "Subimage": sdk.readMode['AC_READMODE_SUBIMAGE'] & caps.ulFTReadModes > 0,
                                       "Single track": sdk.readMode['AC_READMODE_SINGLETRACK'] & caps.ulFTReadModes > 0,
                                       "Full vertical binning": sdk.readMode['AC_READMODE_FVB'] & caps.ulFTReadModes > 0,
                                       "Multi-track": sdk.readMode['AC_READMODE_MULTITRACK'] & caps.ulFTReadModes > 0,
                                       "Random track": sdk.readMode['AC_READMODE_RANDOMTRACK'] & caps.ulFTReadModes > 0,
                                       "Multi track scan": sdk.readMode['AC_READMODE_MULTITRACKSCAN'] & caps.ulFTReadModes > 0}
  
    self.TriggerModes = {"Internal": sdk.triggerMode['AC_TRIGGERMODE_INTERNAL'] & caps.ulTriggerModes > 0,
                         "External": sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL'] & caps.ulTriggerModes > 0,
                         "External with FVB + EM": sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL_FVB_EM'] & caps.ulTriggerModes > 0,
                         "Continuous": sdk.triggerMode['AC_TRIGGERMODE_CONTINUOUS'] & caps.ulTriggerModes > 0,
                         "External start": sdk.triggerMode['AC_TRIGGERMODE_EXTERNALSTART'] & caps.ulTriggerModes > 0,
                         "External exposure": sdk.triggerMode['AC_TRIGGERMODE_EXTERNALEXPOSURE'] & caps.ulTriggerModes > 0,
                         "Inverted": sdk.triggerMode['AC_TRIGGERMODE_INVERTED'] & caps.ulTriggerModes > 0,
                         "Charge shifting": sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL_CHARGESHIFTING'] & caps.ulTriggerModes > 0}
    
    self._TriggerModes = (TriggerMode("TriggerMode", "Internal", 1, 1, 0),
                          TriggerMode("TriggerMode", "External", sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL'], caps.ulTriggerModes, 1),
                          TriggerMode("TriggerMode", "External_FVB", sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL_FVB_EM'], caps.ulTriggerModes, 9),
                          TriggerMode("TriggerMode", "Continuous", sdk.triggerMode['AC_TRIGGERMODE_CONTINUOUS'], caps.ulTriggerModes, 10),
                          TriggerMode("TriggerMode", "External_Start", sdk.triggerMode['AC_TRIGGERMODE_EXTERNALSTART'], caps.ulTriggerModes, 6),
                          TriggerMode("TriggerMode", "External_Exposure", sdk.triggerMode['AC_TRIGGERMODE_EXTERNALEXPOSURE'], caps.ulTriggerModes, 7),
                          TriggerMode("TriggerMode", "External_Charge_Shifting", sdk.triggerMode['AC_TRIGGERMODE_EXTERNAL_CHARGESHIFTING'], caps.ulTriggerModes, 12))
    
    self._AcqModes = (AcqMode_Single("AcqMode", "Single", sdk.acqMode['AC_ACQMODE_SINGLE'], caps.ulAcqModes),
                      AcqMode_Video("AcqMode", "Video", sdk.acqMode['AC_ACQMODE_VIDEO'], caps.ulAcqModes),
                      AcqMode_Accumulate("AcqMode", "Accumulate", sdk.acqMode['AC_ACQMODE_ACCUMULATE'], caps.ulAcqModes),
                      AcqMode_Kinetic("AcqMode", "Kinetic", sdk.acqMode['AC_ACQMODE_KINETIC'], caps.ulAcqModes))
    
    self._ReadModes = (ReadMode_Image("ReadMode", "Image", sdk.readMode['AC_READMODE_FULLIMAGE'], caps.ulReadModes),
                       #ReadMode_SubImage("ReadMode", "Subimage", sdk.readMode['AC_READMODE_SUBIMAGE'], caps.ulReadModes),
                       ReadMode_SingleTrack("ReadMode", "SingleTrack", sdk.readMode['AC_READMODE_SINGLETRACK'], caps.ulReadModes),
                       ReadMode_FullVerticalBinning("ReadMode", "FullVerticalBinning", sdk.readMode['AC_READMODE_FVB'], caps.ulReadModes),
                       ReadMode_MultiTrack("ReadMode", "MultiTrack", sdk.readMode['AC_READMODE_MULTITRACK'], caps.ulReadModes),
                       ReadMode_RandomTrack("ReadMode", "RandomTrack", sdk.readMode['AC_READMODE_RANDOMTRACK'], caps.ulReadModes))
                       #ReadMode_MultiTrackScan("ReadMode", "MultiTrackScan", sdk.readMode['AC_READMODE_MULTITRACKSCAN'], caps.ulReadModes))

    self.CameraType = sdk.cameraType[caps.ulCameraType]

    self.PixelModes = {"8 bits": sdk.pixelMode['AC_PIXELMODE_8BIT'] & caps.ulPixelMode > 0, 
                       "14 bits": sdk.pixelMode['AC_PIXELMODE_14BIT'] & caps.ulPixelMode > 0,
                       "16 bits": sdk.pixelMode['AC_PIXELMODE_16BIT'] & caps.ulPixelMode > 0,
                       "32 bits": sdk.pixelMode['AC_PIXELMODE_32BIT'] & caps.ulPixelMode > 0,
                       "Greyscale": sdk.pixelMode['AC_PIXELMODE_MONO'] & caps.ulPixelMode > 0,
                       "RGB": sdk.pixelMode['AC_PIXELMODE_RGB'] & caps.ulPixelMode > 0,
                       "CMY": sdk.pixelMode['AC_PIXELMODE_CMY'] & caps.ulPixelMode > 0}

    self.SetFunctions = {"Extended EM gain range": sdk.setFunction['AC_SETFUNCTION_EMADVANCED'] & caps.ulSetFunctions > 0,
                         "Extended NIR mode": sdk.setFunction['AC_SETFUNCTION_EXTENDEDNIR'] & caps.ulSetFunctions > 0,
                         "High capacity mode": sdk.setFunction['AC_SETFUNCTION_HIGHCAPACITY'] & caps.ulSetFunctions > 0}
    
    self.Fan = {"Fan can be controlled": sdk.features['AC_FEATURES_FANCONTROL'] & caps.ulFeatures >0,
                "Low fan setting": sdk.features['AC_FEATURES_MIDFANCONTROL'] & caps.ulFeatures >0}

    self.Temperature = {"Temperature can be read during acquisition": sdk.features['AC_FEATURES_TEMPERATUREDURINGACQUISITION'] & caps.ulFeatures > 0,
                        "Temperature can be read": sdk.getFunction['AC_GETFUNCTION_TEMPERATURE'] & caps.ulGetFunctions > 0,
                        "Valid temperature range can be read": sdk.getFunction['AC_GETFUNCTION_TEMPERATURERANGE'] & caps.ulGetFunctions > 0}

    self.PCICard = {"Maximum speed (Hz)": caps.ulPCICard}

    self.EMGain = {"8-bit DAC settable": sdk.EMGain['AC_EMGAIN_8BIT'] & caps.ulEMGainCapability > 0,
                   "12-bit DAC settable": sdk.EMGain['AC_EMGAIN_12BIT'] & caps.ulEMGainCapability > 0,
                   "Gain setting represent a linear gain scale. 12-bit DAC used internally": sdk.EMGain['AC_EMGAIN_LINEAR12']
                   & caps.ulEMGainCapability > 0,
                   "Gain setting represents the real EM Gain value. 12-bit DAC used internally": sdk.EMGain['AC_EMGAIN_REAL12']
                   & caps.ulEMGainCapability > 0}

PixelModes = {0: "8 bits", 1: "14 bits", 2: "16 bits", 3: "32 bits"}   
  
TEMPERATURE_MESSAGES = (20034, 20035, 20036, 20037, 20040)
  
