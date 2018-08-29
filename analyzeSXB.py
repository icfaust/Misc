import matplotlib.pyplot as plt
import scipy
import scipy.interpolate
import sys
sys.path.append('/home/faustian/python/adas/xxdata_13/')

from matplotlib import rc

import adasread
rc('text', usetex=True)
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
#rc('font',**{'family':'sans-serif','sans-serif':['Computer Modern Sans serif']})
rc('font',size=18)



# GRAB Lyalpha ONLY
def plot(filein,Telim,Nelim):

    plt.figure()
    out = adasread.xxdata_13(filein,1,Telim,Nelim)
    print(out[13])
    print(out[12])
    print(out[14])
    ne = scipy.array(out[13]).ravel()
    Te = scipy.array(out[12]).ravel()
    SXB = scipy.array(out[14][:,:,0])

    temp =  ne != 0
    temp2 = Te != 0
    
    xout,yout = scipy.meshgrid(ne[temp]*1e6,Te[temp2])
    zout = SXB[temp2,:]
    zout = zout[:,temp]

    plt.pcolor(xout,yout,zout)
    plt.clim([.3,1.6])
    plt.colorbar()
    plt.xlabel(r'electron density [$10^{20} $m$^{-3}$]')
    plt.ylabel(r'electron temperature [eV]')
    #plt.title(filein+' colorbar is ionizations per photon')

def plot2(filein,Telim,Nelim,pts=101):

    plt.figure()
    out = adasread.xxdata_13(filein,1,Telim,Nelim)
    print(out[13].shape)
    print(out[12].shape)
    print(out[14].shape)

    ne = scipy.array(out[13]).ravel()
    Te = scipy.array(out[12]).ravel()
    SXB = scipy.array(out[14][:,:,0])
    
    temp =  ne != 0
    temp2 = Te != 0

    xout2,yout2 = scipy.meshgrid(ne[temp],Te[temp2])
    SXB = SXB[temp2,:]
    SXB = SXB[:,temp]

    ne1 = scipy.linspace(ne[temp].min(),ne[temp].max(),pts)
    Te1 = scipy.linspace(Te[temp2].min(),Te[temp2].max(),pts)
    xout,yout = scipy.meshgrid(ne1,Te1)

    interp = scipy.interpolate.RectBivariateSpline(scipy.log(ne[temp]),
                                                   Te[temp2],
                                                   SXB)

    zout = interp.ev(scipy.log(xout),yout)
    #xout,yout = scipy.meshgrid(ne[temp]*1e6,Te[temp2])
    #zout = SXB[temp2,:]
    #zout = zout[:,temp]

    plt.pcolor(xout*1e6,yout,zout.T)
    plt.colorbar()
    plt.xlabel(r'electron density [$10^{20}$ m$^{-3}$]')
    plt.ylabel(r'electron temperature [eV]')
    #plt.title(filein+' colorbar is ionizations per photon')

def plot3(filein,Telim,Nelim,pts=11):

    plt.figure()
    out = adasread.xxdata_13(filein,1,Telim,Nelim)
    print(out[13].shape)
    print(out[12].shape)
    print(out[14].shape)

    ne = scipy.array(out[13]).ravel()
    Te = scipy.array(out[12]).ravel()
    SXB = scipy.array(out[14][:,:,0])
    
    temp =  ne != 0
    temp2 = Te != 0

    SXB = SXB[temp2,:]
    SXB = SXB[:,temp]
    xout2,yout2 = scipy.meshgrid(ne[temp],Te[temp2])
    print(Te[temp2])

    ne1 = scipy.linspace(ne[temp].min(),ne[temp].max(),pts)
    Te1 = scipy.linspace(Te[temp2].min(),Te[temp2].max(),pts)
    xout,yout = scipy.meshgrid(ne1,Te1)

    zout = scipy.interpolate.griddata((scipy.log(xout2.flatten()),yout2.flatten()),SXB.flatten(),(scipy.log(xout),yout),'cubic')

    #xout,yout = scipy.meshgrid(ne[temp]*1e6,Te[temp2])
    #zout = SXB[temp2,:]
    #zout = zout[:,temp]

    plt.imshow(zout,cmap='viridis',extent=[ne1[0]*1e6,ne1[-1]*1e6,Te1[0],Te1[-1]],aspect='auto',origin='lower')

    #plt.clim([.3,1.8])
    colorz = plt.colorbar()
    colorz.set_label(r'S/XB [ionizations per Ly$_\alpha$ photon]')
    plt.xlabel(r'electron density [m$^{-3}$]')
    plt.ylabel(r'electron temperature [eV]')
    #plt.title(filein+' colorbar is ionizations per photon')
