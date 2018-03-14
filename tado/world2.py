from math import sin, cos, asin, atan2, pi

a = 6378137. #m from WGS84
f = 1./298.257223563 # from the inverse flattening defined in WGS84
r = a*(1. - f/3.) #m

#pi = 3.14159265

def eval(phi0, theta0, b, distance):
    delta = distance/r

    # standard case when not at a pole
    if abs(phi0) < pi/2.:
        phi1 = sin(sin(phi0)*cos(delta) +
                            cos(phi0)*sin(delta)*cos(b))
    
        theta1 = theta0 + atan2(sin(b)*sin(delta)*cos(phi0),
                                cos(delta) - sin(phi0)*sin(phi1))

    # when at a pole
    elif abs(phi0) == pi/2.:
        phi1 = phi0 + -1*abs(phi0)/phi0*delta
        theta1 = b

    phi1 = phi1*180/pi
    theta1 = ((theta1*180/pi + 540.) % 360.) - 180.
    return phi1, theta1
    

def convert(lat, lng, bear):
    # convert the latitude longitude and bearing values into proper units
    lat *= pi/180.
    lng *= pi/180.
    bear *= pi/180.
    return lat, lng, bear
