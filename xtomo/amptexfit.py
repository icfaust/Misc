import scipy
import scipy.interpolate
import matplotlib.pyplot as plt
from matplotlib import rc
import scipy.optimize
rc('text', usetex=True)
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('font',size=18)

def fe55fit( loc, peakx=[3025.,3300.], ev=[5.89875,6.49045], back=13):
    """ expecting two peaks for Fe-55 at 5.89875 and 6.49045 keV,
    however, data x range is not in keV but bins (requires fit),
    uses scipy.optimize.curve_fit"""

    data = scipy.loadtxt(loc).T
    xdata = data[0].astype(float)
    ydata = data[1].astype(float)

    ydata2 = ydata - back
    ydata2 = ydata2/2. + abs(ydata2)/2.

    a1 = ydata2.max()
    a2 = peakx[0]
    a3 = 100.
    b1 = ydata2.max()/2.
    b2 = peakx[1]
    b3 = 100.

    popt, pcov = scipy.optimize.curve_fit(twogauss,
                                          xdata,
                                          ydata,
                                          p0=[a1,a2,a3,b1,b2,b3])

    return xdata,ydata,popt
    

def twogauss(xdata, peak1, off1, sig1, peak2, off2, sig2):
    return gauss(xdata, peak1, off1, sig1) + gauss(xdata, peak2, off2, sig2)


def gauss(xdata, peakval, offset, sigma):
    return peakval * scipy.exp( -(((xdata - offset)/sigma)**2)/2.)


def fit(loc, peakx=[3025.,3300.], ev=[5.89875,6.49045], back=13):    

    x,y,popt = fe55fit('/home/ian/python/xtomo/'+loc+'.txt',
                       peakx = peakx,
                       ev = ev,
                       back = back)

    plt.semilogy(x,y)
    plt.semilogy(twogauss(x,
                          popt[0],
                          popt[1],
                          popt[2],
                          popt[3],
                          popt[4],
                          popt[5]))
    
    plt.semilogy(gauss(x,
                       popt[0],
                       popt[1],
                       popt[2]),'k:')
    
    plt.semilogy(gauss(x,
                       popt[3],
                       popt[4],
                       popt[5]),'k:')
    
    print(popt)
    kevbin = (ev[1]-ev[0])/(popt[4]-popt[1])
    temp1 = 2*scipy.sqrt(2*scipy.log(2))*popt[2]*kevbin
    temp2 = 2*scipy.sqrt(2*scipy.log(2))*popt[5]*kevbin

    plt.xlim(xmax=5e3)
    plt.ylim(ymin=1.)
    plt.ylabel('Counts/Channel')
    plt.xlabel('Channel')
    plt.text(popt[1],popt[0],r'.   '+str(ev[0])+' keV')
    plt.text(popt[4],popt[3],r'.   '+str(ev[1])+' keV')
    plt.title(r'$^{55}$Fe spectrum, '+str(int(1e3*temp1))+' and '+str(int(1e3*temp2))+' eV FWHM')    
    temp = plt.axis()
    x = (temp[1]-temp[0])*1.01+temp[0]
    y = (temp[3]-temp[2])*.85+temp[2]
    
    plt.text(x,y,loc,rotation='vertical',fontsize=14)
    
    plt.show()


def compare(inp=[102,103,104,105,1101], day=1150310000,time=[3845.45,5600.97,13857.78,6963.35,11230.]):

    txt=['no','5','3','1','no']

    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[4])+'.txt')
    
    k0 = dat0[0]/time[4]/scipy.sqrt(scipy.pi*2*dat0[2])
    k1 = dat0[3]/time[4]/scipy.sqrt(scipy.pi*2*dat0[5])
    for i in xrange(len(inp)):
        x,y0,dat1 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[i])+'.txt')
        print(i,1-dat1[0]/time[i]/k0/scipy.sqrt(scipy.pi*2*dat1[2]),1-dat1[3]/time[i]/k1/scipy.sqrt(scipy.pi*2*dat1[5]),txt[i])

def compare2(inp=[1102,103,104,105,1101], day=1150310000,time=[5845.45,5600.97,13857.78,6963.35,11230.]):

    txt=['no','5','3','1','no']

    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[4])+'.txt')
    
    k0 = dat0[0]/time[4]
    k1 = dat0[3]/time[4]

    for i in xrange(len(inp)):

        x,y0,dat1 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[i])+'.txt')
        print(i,1-dat1[0]/time[i]/k0,1-dat1[3]/time[i]/k1,txt[i])

    
def compare3(inp=[101,102,103,104,105,106,107,108], day=1150311000,time=[11230.98,5853.36,6389.85,8005.11,6291.73,6910.24,7658.35,7952.96]):

    txt = ['no foil','5','no','5','3','1','new','3 off axis']
    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[0])+'.txt')
    
    k0 = dat0[0]/time[0]
    k1 = dat0[3]/time[0]

    for i in xrange(len(inp)):

        x,y0,dat1 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[i])+'.txt')
        print(i,1-dat1[0]/time[i]/k0,1-dat1[3]/time[i]/k1,txt[i])


def compare4(inp=[103,104,105,106,107,108], day=1150311000,time=[6389.85,8005.11,6291.73,6910.24,7658.35,7952.96]):

    txt = ['no','5','3','1','new','3 off axis']
    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[0])+'.txt')
    
    k0 = dat0[0]/time[0]
    k1 = dat0[3]/time[0]

    for i in xrange(len(inp)):

        x,y0,dat1 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[i])+'.txt')
        print(i,1-dat1[0]/time[i]/k0,1-dat1[3]/time[i]/k1,txt[i])


def compare5(inp=[103,104,105,106,107,108], day=1150311000,time=[6389.85,8005.11,6291.73,6910.24,7658.35,7952.96]):

    txt = ['no','5','3','1','new','3 off axis']

    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[0])+'.txt')
    
    k0 = dat0[0]/time[0]/scipy.sqrt(scipy.pi*2*dat0[2])
    k1 = dat0[3]/time[0]/scipy.sqrt(scipy.pi*2*dat0[5])
    
    for i in xrange(len(inp)):
        x,y0,dat1 =  fe55fit('/home/ian/python/xtomo/'+str(day+inp[i])+'.txt')
        print(i,1-dat1[0]/time[i]/k0/scipy.sqrt(scipy.pi*2*dat1[2]),1-dat1[3]/time[i]/k1/scipy.sqrt(scipy.pi*2*dat1[5]),txt[i])

def Beatten(rho=1.848,thick=50e-4,peak=[5.89875,6.49045]):
    mu = scipy.loadtxt('bemassatten.txt').T
    inter = scipy.interpolate.interp1d(mu[0]*1e3,scipy.exp(-mu[2]*rho*thick),kind='cubic')
    x,y0,dat0 =  fe55fit('/home/ian/python/xtomo/1150311103.txt')
    data = scipy.exp(-mu[1]*rho*thick)
    xd = scipy.linspace(1,10,1e3)
    plt.semilogy(xd,1-inter(xd),label='50$\mu$m foil')
    plt.semilogy(peak,1-inter(peak),marker=r'$\circ$',label='$^{55}$Fe K lines',linestyle='None')
    plt.text(peak[0],1-inter(peak[0]),r'   ' + "%0.2f" % (100*(1-inter(peak[0]))) + r'\%')
    plt.text(peak[1],1-inter(peak[1]),r'   ' + "%0.2f" % (100*(1-inter(peak[1]))) + r'\%')
    plt.xlim([0,8])
    plt.ylim([1e-3,1])
    plt.ylabel(r'1 - Transmission')
    plt.xlabel(r'Energy [keV]')
    plt.title('XTOMO Be foil attenuation (with $^{55}$Fe peaks)')
    plt.legend()
    plt.show()


def fit2(loc=['1150311103','1150311104'], time = [6389.85,8005.11], peakx=[3025.,3300.], ev=[5.89875,6.49045], back=13,txt=['no foil','array 5']):    

    for i in xrange(len(loc)):
        x,y,popt = fe55fit('/home/ian/python/xtomo/'+loc[i]+'.txt',
                           peakx = peakx,
                           ev = ev,
                           back = back)

        plt.semilogy(x,y/time[i],label=txt[i])
        plt.semilogy(x,twogauss(x,
                                popt[0],
                                popt[1],
                                popt[2],
                                popt[3],
                                popt[4],
                                popt[5])/time[i])
        
        plt.semilogy(x,gauss(x,
                             popt[0],
                             popt[1],
                             popt[2])/time[i],'k:')
        
        plt.semilogy(x,gauss(x,
                             popt[3],
                             popt[4],
                             popt[5])/time[i],'k:')
    
        print(popt)
        kevbin = (ev[1]-ev[0])/(popt[4]-popt[1])
        temp1 = 2*scipy.sqrt(2*scipy.log(2))*popt[2]*kevbin
        temp2 = 2*scipy.sqrt(2*scipy.log(2))*popt[5]*kevbin

    plt.xlim(xmax=5e3)
    plt.ylim(ymin=1e-3)
    plt.ylabel('Counts/Channel/s')
    plt.xlabel('Channel')
       # plt.text(popt[1],popt[0]/time[i],r'.   '+str(ev[0])+' keV')
       # plt.text(popt[4],popt[3]/time[i],r'.   '+str(ev[1])+' keV')
        #plt.title(r'$^{55}$Fe spectrum, '+str(int(1e3*temp1))+' and '+str(int(1e3*temp2))+' eV FWHM')    
    temp = plt.axis()
    x = (temp[1]-temp[0])*1.01+temp[0]
    y = (temp[3]-temp[2])*.85+temp[2]
    
    plt.text(x,y,loc,rotation='vertical',fontsize=14)
    plt.legend()
    
    plt.show()
