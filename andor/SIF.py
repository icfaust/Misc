#import andor2
from AUGreport import AUGspecWarning

import shutil
import thread
from time import sleep
import Queue

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen


# initial version should have a replication of the visual basic code
# which will then slowly introduce fault reporting and fault tolerance
# this will minimize effort and is quickest for initial implementation
# This initial version will not have a GUI interface, but will be broken
# down in such a way to allow for it to become an object (easier to make
# a GUI)

#SIF is a Spectrometer Object, which utilizes a Andor Spectrometer camera (A camera object)

class Spectrometer(object):

    def __init__(self, cam=None, settings=None, email=None, dweet=None, GUI=None):
        if settings == None:# or cam == None:
            raise AttributeError('Both a camera and a Settings object (needed for camera operation) must be provided')

        #objects needed for operation of camera
        self.Settings = settings
        self.Cam = cam

        #error reporting information (strings)
        self.email = email
        self.dweet = dweet       
        self._GUI = GUI

        #state verification flags
        self._setup = False
        self._running = False
        self._seq = 0

    def acquire(self, queue=None): #rewrite this with a set of threading objects
        self.Cam.AcqMode.start()

        while self._running:
            self._running = self.Cam.running
            sleep(5)
            try:
                queuein = queue.get() #if anything is put into the queue, then stop operation
                self._running = False
            except queue.Empty:
                pass
        queue.task_done()

    @property
    def shotnum(self):
        return self._shot

    @shotnum.setter
    def shotnum(self):
        try:
            temp = open(self.Settings.shotfileLoc,'r')
            self._shot = int(temp.readline())
            shutil.move(self.Settings.shotfileLoc, self.Settings.shotfileLoc+'_'+str(self._shot))
        except FileNotFoundError:
            AUGspecWarning('Shotfile cannot be read',
                           email=self.email,
                           dweet=self.dweet,
                           name=self.Settings.name,
                           subject='Shotfile read error')
                
    @property
    def setupLoad(self):
        return self._setup
    
    @setupLoad.setter
    def setupLoad(self, setupfile):
        self._setup = False #setupLoad must be redefined for each spectrometer, otherwise will specify setup not loaded

    def store(self, end='.SIF'):
        #force all files based on number to a specific length
        strshot = '{0:05d}'.format(self.shot)

        #file names
        localfile = + self.Settings.name + str(self.sequence) + end

        try:
            self.Cam.save(localfile) 
        except:
            AUGspecWarning('Cannot save data',
                           email=self.email,
                           dweet=self.dweet,
                           name=self.Settings.name,
                           subject='Cannot save data')

    def AFScopy(self, end='.SIF'):
        #force all files based on number to a specific length
        strshot = '{0:05d}'.format(self.shot)

        #file names
        localfile = + self.Settings.name + str(self.sequence) + end
        AFSfile = self.Settings.AFSLocation + self.Settings.name + strshot + end
        
        try:
            shutil.copy(localfile, AFSfile)
        except:
            AUGspecWarning('AFS copy error',
                           email=self.email,
                           dweet=self.dweet,
                           name=self.Settings.name,
                           subject='Cannot save data')
            
    @property
    def vacuum(self):
        return self._vacuum
    
    @vacuum.setter
    def vacuum(self):
        try:
            self._vacuum = bool(urlopen(self.Settings.vacCheckURL))
        except:
            AUGspecWarning('Vacuum cannot be read',
                           email=self.email,
                           dweet=self.dweet,
                           name=self.Settings.name,
                           subject='Vacuum error') 

    @property
    def sequence(self):
        return self._seq

    @sequence.setter
    def sequence(self, seq):
        self._seq = seq

    def start(self, single=None, tempsetpoint=25):
        self._running = True

        if not self._setup: #The spectrometer will not run without running a setup
            self._running = False
        
        while self._running:

            if not self.vacuum(): #check the vacuum status
                AUGspecWarning('Vacuum Warning',
                               email=self.email,
                               dweet=self.dweet,
                               name=self.Settings.name,
                               subject='High Vacuum Warning')
                self.Cam.Temperature.setpoint(tempsetpoint) #Immediately raise camera temperature to protect the camera
                self.Cam.Temperature.cooler = False #turn off cooler
                self._running = False
            
            elif abs(self.Temperature.read['temperature'] - self.Settings.setTemp) > 2: #if the vacuum is good, and the temperature is not up to snuff
                AUGspecWarning('Temperature Warning',
                               email=self.email,
                               dweet=self.dweet,
                               name=self.Settings.name,
                               subject='Chip temperature not at set point')
                self.Cam.Temperature.setpoint(self.Settings.setTemp) # set it again just in case
                if not self.Temperature.cooler: #if the cooler is off, turn it on.
                    self.Cam.Temperature.cooler = True #turn on cooler            

            #if the temp is bad, still acquire, but if the vacuum is bad, shut everything down.
                    
            if self._running:

                if not self._GUI is None:
                    self._GUI.printf("acquisition of shot:"+str())
                    self.sequence = int(self._GUI.seqInput.get())
                
                self.Cam.Acquire.start()
                self.Cam.Acquire.wait() #supposedly not thread safe

            #Double check the number of frames (if it was stopped)
            #progress, series = self.Cam.Acquire.progress()
            self.shotnum()
            if self._running: #if running was not forced off
                
                self.store() #store the data
                #self.AFScopy() hold off on AFScopy yet
                self.sequence(self.sequence + 1) #push up the sequence
                if not self._GUI is None:
                    self._GUI.printf("acqusition complete")
                    self._GUI.shotUpdate(self.shotnum)
                    self._GUI.sequenceUpdate(self.sequence)
                
            # IF SINGLE
            if single:
                self._running = False #this will call a function which includes the function stop

        if not self._GUI is None:
            self._GUI.stop() #reset buttons on gui
            
        self.stop()
            
    def stop(self):
        self._running = False
        self.Cam.Acquire.stop() #if camera is waiting for acquisition, just stop it

    def printf(self,text):
        if not self._GUI is None:
            self._GUI.printf(text)
        
class Settings(object):
    """ This object parses typical settings necessary to interface with the ASDEX shot cycle"""
    
    def __init__(self, startfile=None):
        startup = self.readSetupFile(startfile)

        # this is unique to the Johann_autorun.cfg script
        self.name = startup[0][0]
        self.setupFile1= [startup[1][0], ' '.join(str(x) for x in startup[1][1:])] #location of the camera setup file #1
        self.setupFile2 = [startup[2][0], ' '.join(str(x) for x in startup[2][1:])]#location of the camera setup file #2
        self.tempLocation = startup[3][0] #where to temporarily store the output datafile
        self.AFSLocation = startup[4][0]  #where to put the file in AFS
        self.shotfileLoc = startup[5][0]  #where to look for the shot number
        self.logfileLoc = startup[6][0]   #where to store the log file
        self.setTemp = int(startup[7][0]) #temperature setting
        self.vacCheckURL = startup[8][0]  #where to check the vacuum              

    def readSetupFile(self, setupfile):
        filein = open(setupfile,'r')
        output = []
        for i in filein:
            if i[0] != '#':
                output += [i.split()]
        return output

class SIF(Spectrometer):

    def __init__(self, startfile="Johann_autorun.cfg", email=None, dweet=None):
        settings = Settings(startfile)
        super(SIF, self).__init__(None,#andor2.Andor(),
                                  Settings(startfile),
                                  email=email,
                                  dweet=dweet)

    @property
    def setupLoad(self):
        return self._setup
            
    @setupLoad.setter
    def setupLoad(self, setupfile):
        """ Load the setupfile described in the string setupfile """

        try:
            # this is unique to the setup of the SIF spectrometer
            data = self.Settings.readSetupFile(setupfile)
            
            #here is where we modify settings of the SIF.andor object

            #set acq mode, any setup params after fast triggering is assumed to be an acquisition paramter
            
            #set num kinetics (Not very well duck-typed), the following two accept additional parameters
            if temp == 2: #just accumulation
                self.Cam.Acquire[temp](int(data[2][0]), 0)

            elif temp == 3: #kinetic
                self.Cam.Acquire[temp](int(data[1][0]), 0, int(data[2][0]))

            else:
                self.Cam.Acquire[temp]()
            
            #set read mode
            self.Cam.ReadMode[int(data[3][0])]
            
            #set readout speed
            self.Cam.Detector.HSS(int(data[4][0]))
            
            #set exposure time
            self.Cam.exposure(float(data[5][0])/1e3) #in ms
            
            #set trigger mode
            self.Cam.TriggerMode[int(data[6][0])]
            
            #set fast trigger?
            self.Cam.TriggerMode.fast(bool(data[7][0]))
            
        except:
            AUGspecWarning('Setup load failure',
                           email=self.email,
                           dweet=self.dweet,
                           name=self.Settings.name,
                           subject=name+ 'Setup load failure')
        
        self._setup = True #setup properly loaded

    def store(self):
        super(SIF, self).store(end='.SIF')

    def AFScopy(self):
        super(SIF, self).AFScopy(end='.SIF')
