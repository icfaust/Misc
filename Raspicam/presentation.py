import scipy
import scipy.interpolate
import matplotlib.pyplot as plt
from matplotlib import rc
import MDSplus as MDS

rc('text', usetex=True)
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('font',size=18)

def go(shot):
    node = '\SPECTROSCOPY::TOP.VIDEO_DAQ:MATROX3:CAMERA_2'
    tree = MDS.Tree('spectroscopy',shot)
    camtime = tree.getNode(node).dim_of().data()

    node2 = '.results:netpow'
    tree = MDS.Tree('lh',shot)
    y = tree.getNode(node2).data()
    x = tree.getNode(node2).dim_of().data()

    f = scipy.interpolate.interp1d(x,
                                   y,
                                   bounds_error=False)
    camy = f(camtime)

    plt.plot(x,y,'k')
    plt.plot(camtime,camy,'go',markersize=12)
    plt.title('WIDE2 frame times')
    plt.xlabel('time [s]')
    plt.ylabel('LH Power [kW]')

    temp = plt.gca().axis()
    x3 = (temp[1]-temp[0])*1.01+temp[0]
    y3 = (temp[3]-temp[2])*.97+temp[2]
    
    plt.text(x3,y3,str(shot),rotation='vertical',fontsize=14)


    plt.show()


def go2(shot):
    node = '\SPECTROSCOPY::TOP.VIDEO_DAQ:MATROX3:CAMERA_2'
    tree = MDS.Tree('spectroscopy',shot)
    camtime = tree.getNode(node).dim_of().data()
    camtime = scipy.mgrid[camtime[0]:camtime[-1]:1./90]
    #print(camtime)


    node2 = '.results:netpow'
    tree = MDS.Tree('lh',shot)
    y = tree.getNode(node2).data()
    x = tree.getNode(node2).dim_of().data()

    f = scipy.interpolate.interp1d(x,
                                   y,
                                   bounds_error=False)
    camy = f(camtime)

    plt.plot(x,y,'k')
    plt.plot(camtime,camy,'ro',markersize=8)
    plt.title('90fps frame times')
    plt.xlabel('time [s]')
    plt.ylabel('LH Power [kW]')

    temp = plt.gca().axis()
    x3 = (temp[1]-temp[0])*1.01+temp[0]
    y3 = (temp[3]-temp[2])*.97+temp[2]
    
    plt.text(x3,y3,str(shot),rotation='vertical',fontsize=14)

    plt.show()
