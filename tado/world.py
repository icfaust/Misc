import scipy
import matplotlib.pyplot as plt

a = 6378137. #m from WGS84
f = 1./298.257223563 # from the inverse flattening defined in WGS84
r = a*(1. - f/3.) #m

def eval(phi0, theta0, b, distance):
    delta = distance/r

    # standard case when not at a pole
    if abs(phi0) < scipy.pi/2.:
        phi1 = scipy.arcsin(scipy.sin(phi0)*scipy.cos(delta) +
                            scipy.cos(phi0)*scipy.sin(delta)*scipy.cos(b))
    
        theta1 = theta0 + scipy.arctan2(scipy.sin(b)*scipy.sin(delta)*scipy.cos(phi0),
                                        scipy.cos(delta) - scipy.sin(phi0)*scipy.sin(phi1))

    # when at a pole
    elif abs(phi0) == scipy.pi/2.:
        phi1 = phi0 + -1*scipy.sign(phi0)*delta
        theta1 = b

    phi1 = phi1*180/scipy.pi
    theta1 = ((theta1*180/scipy.pi + 540.) % 360.) - 180.
    return phi1, theta1
    

def convert(lat, lng, bear):
    # convert the latitude longitude and bearing values into proper units
    lat *= scipy.pi/180.
    lng *= scipy.pi/180.
    bear *= scipy.pi/180.
    return lat, lng, bear
