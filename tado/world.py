import scipy
import matplotlib.pyplot as plt
import scipy.optimize

class world(object):

    self.a = 6378137.
    self.f = 1./298.257223563

    
    def __init__(self, longitude, latitude, heading):

        self.longitude = longitude
        self.lattitude = latitude
        self.heading = heading

    def rho(self, phi):
        return pow(self.a,2)/scipy.sqrt(pow(self.a,2) + pow(scipy.cos(phi)

    def call(self, angle):

        return 
