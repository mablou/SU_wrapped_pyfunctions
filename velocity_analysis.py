import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
from scipy.interpolate import griddata
from scipy.ndimage import filters
from .io import segy2array,print_su_header
mplstyle.use('fast')

##################################
####CONSTANT USED FOR THIS PROJECT####
###COULD BE VARIABLES###########
OFFSETS = np.arange(5.5,77.5,1.5)
TIME = np.arange(0,1,0.00025)
NCMP = 10 # number of CMP stacked in analysis
plt.ion()


class VelocityPicking(object):
    def __init__(self, data_in,line, ID,analysis='semblance'):
        self.ID = ID
        self.i = 0
        self.analysis = analysis.lower()
        self.data_in = data_in
        self.line = line
        self.offsets = OFFSETS
        if self.analysis == 'dispersion':
            self.fig = plt.figure()
            self.ax = self.fig.add_subplot(111)
            self.pick, = self.ax.plot([], [],'o-')  # empty line
            self.xs = list(self.pick.get_xdata())
            self.ys = list(self.pick.get_ydata())
            self.ax.set_title('pick dispersion curve - Shot ' + str(self.ID[self.i]))
            self.shot = window_shot(self.data_in,self.ID[self.i])
            self.data = generate_phasevel(self.shot)

        else:
            self.fig,self.axs = plt.subplots(ncols=2,figsize=(20,10))
            self.axs[0].set_title('pick semblance curve - CMP ' + str(self.ID[self.i]))
            self.pick, = self.axs[0].plot([], [],'o-')  # empty line
            self.curve, = self.axs[1].plot([],[],'-')
            self.xs = list(self.pick.get_xdata())
            self.ys = list(self.pick.get_ydata())
            self.cmp = window_cmp(self.data_in,self.ID[self.i],NCMP)
            self.data = generate_semblance(self.cmp)
            self.data = self.data.reshape(NCMP,200,-1)
            self.s = get_shotNum_from_cmp(self.cmp)
            self.axs[1].set_title('Shot Gather # ' + str(self.s))
            self.shot = window_shot(self.data_in,self.s)
            cmd = 'sugain<' + self.shot + ' agc=1 wagc=0.88|\
                    segyhdrs ns=4000 dt=250|segywrite \
                    endian=0 verbose=1 tape=shot_temp.sgy'
            subprocess.call(cmd,shell=True)
            self.seismic_data = segy2array('shot_temp.sgy')



    def on_press(self, event):
        # print('click', event)
        if event.inaxes!=self.pick.axes: return
        if event.button==1:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
            self.pick.set_data(self.xs, self.ys)
            self.pick.figure.canvas.draw()
            if self.analysis == 'semblance':
                self.nmo = [np.sqrt(np.array(y)**2 + \
                                            self.offsets**2/np.array(x)**2) for \
                                            x,y in zip(self.xs,self.ys)]
                for n in self.nmo:
                    self.curve.set_data(self.offsets,n)
                    self.curve.figure.canvas.draw()

        elif event.button==3:
            self.xs.pop(-1)
            self.ys.pop(-1)
            self.pick.set_data(self.xs, self.ys)
            self.pick.figure.canvas.draw()
            if self.analysis == 'semblance':
                self.nmo = [np.sqrt(np.array(y)**2 + \
                                            self.offsets**2/np.array(x)**2) for \
                                            x,y in zip(self.xs,self.ys)]
                for n in self.nmo:
                    self.curve.set_data(self.offsets,n)
                    self.curve.figure.canvas.draw()

    def on_save(self,event):
        if event.key=='cmd+s':
            if self.analysis == 'dispersion':
                cmp = np.ones_like(self.xs) * get_cmpNum_from_shot(self.shot)
            else:
                cmp = np.ones_like(self.xs) * self.ID[self.i]

            np.save(os.path.join(self.save_dir,self.analysis + \
                                            str(self.ID[self.i]) + \
                                            '.npy'),(cmp,self.xs,self.ys))

    def on_next(self,event):
        if event.key == 'cmd+n':
            self.i += 1
            self.xs = []
            self.ys = []
            self.pick.set_data(self.xs, self.ys)
            self.pick.figure.canvas.draw()
            #updating dispersion image
            if self.analysis == 'dispersion':
                os.remove(self.shot)
                self.ax.set_title('pick dispersion curve - Shot ' + str(self.ID[self.i]))
                self.shot = window_shot(self.data_in,self.ID[self.i])
                self.data = generate_phasevel(self.shot)
                self.im.set_data(self.data.reshape(250,-1).T)
                self.im.figure.canvas.draw()

            else:
                os.remove('shot_temp.sgy')
                os.remove(self.cmp)
                os.remove(self.shot)
                self.axs[0].set_title('pick semblance curve - CMP ' + str(self.ID[self.i]))
                self.cmp = window_cmp(self.data_in,self.ID[self.i],NCMP)
                self.data = generate_semblance(self.cmp)
                self.data = self.data.reshape(NCMP,200,-1)
                self.s = get_shotNum_from_cmp(self.cmp)
                self.axs[1].set_title('Shot Gather # ' + str(self.s))
                self.shot = window_shot(self.data_in,self.s)
                cmd = 'sugain<' + self.shot + ' agc=1 wagc=0.88|\
                        segyhdrs ns=4000 dt=250|segywrite \
                        endian=0 verbose=1 tape=shot_temp.sgy'
                subprocess.call(cmd,shell=True)
                self.seismic_data = segy2array('shot_temp.sgy')
                self.im0.set_data((np.sum(self.data,axis=0)).T)
                self.im0.figure.canvas.draw()
                self.im1.set_data(self.seismic_data.T)
                self.im1.figure.canvas.draw()


    def start_picking(self,save_dir='.'):
        self.save_dir = save_dir
        try:
            os.mkdir(self.save_dir)
        except:
            pass
        if self.analysis == 'dispersion':
            self.im = self.ax.imshow((self.data.reshape(250,-1)).T,extent=(0,500,50,0),aspect=10)
        else:
            self.im0 = self.axs[0].imshow(((np.sum(self.data,axis=0)).T),extent=(100,300,1,0),aspect=200,vmin=0,vmax=10)
            self.im1 = self.axs[1].imshow(self.seismic_data.T,extent=[5.5,77.5,1,0],aspect=70,cmap='Greys')

        self.cidpress = self.pick.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.Skey = self.pick.figure.canvas.mpl_connect('key_press_event', self.on_save)
        self.Nkey = self.pick.figure.canvas.mpl_connect('key_press_event', self.on_next)
        # self.exit = pick.figure.canvas.mpl_connect('close_event', self.on_close)


def window_shot(data_in,shotNum,output=None):
    if output==None:
        output= 'shot'+ str(shotNum) + '.su'
    cmd = 'suwind<' + data_in + ' key=fldr min='+ str(shotNum)+\
                                        ' max='+ str(shotNum) + ' >' + output
    subprocess.call(cmd,shell=True)
    return output

def window_cmp(data_in,cmp_min,ncmp,output=None):
    if output==None:
        output= 'cmp'+ str(cmp_min) + '.su'
    cmd = 'susort<' + data_in + ' cdp offset | suwind key=cdp min='+ \
                    str(cmp_min)+' max='+ str(cmp_min + ncmp -1) + '>' + output
    subprocess.call(cmd,shell=True)
    return output

def generate_phasevel(data_in):
    cmd = 'sugain<' + data_in + ' agc=1 wagc=0.88|suphasevel norm=1 fv=0 dv=2 \
                    nv=250 fmax=50|suamp|segyhdrs ns=50 dt=250|segywrite \
                                            endian=0 verbose=1 tape=temp.sgy'
    subprocess.call(cmd,shell=True)
    data = segy2array('temp.sgy')
    os.remove('temp.sgy')
    return data

def generate_semblance(data_in):
    cmd = 'sugain<' + data_in + ' agc=1 wagc=0.88|suvelan fv=100 nv=200 dv=1 \
                        smute=1.5 pwr=1|segyhdrs ns=800 dt=250|segywrite \
                                            endian=0 verbose=1 tape=temp.sgy'
    subprocess.call(cmd,shell=True)
    data = segy2array('temp.sgy')
    os.remove('temp.sgy')
    return data

def get_shotNum_from_cmp(data_in):
    hdr = print_su_header(data_in)
    s = hdr.split('\n')[3].split(' ')
    return int(np.mean([int(s[5]),int(s[6])]))

def get_cmpNum_from_shot(data_in):
    hdr = print_su_header(data_in)
    s = hdr.split('\n')[3].split(' ')
    return int(np.mean([int(s[6]),int(s[7])]))

def gather_velocities(velo_dir,velo_type='semblance'):
    v = []
    t = []
    cmp = []

    for f in os.listdir(velo_dir):
        if f.startswith(velo_type):
            c,x,y = np.load(os.path.join(velo_dir,f))
            if velo_type == 'dispersion':
                idx = np.argsort(1/y)
                t.extend(1/y[idx])
            else:
                idx = np.argsort(y)
                t.extend(y[idx])
            v.extend(x[idx])
            cmp.extend(c)
    return np.array(cmp),np.array(t),np.array(v)

def generate_2D_velocity(velo_dir,cmps,times,velo_type='both'):
    if velo_type == 'both':
        cmp,t,v = gather_velocities(velo_dir,velo_type='dispersion')
        cmp2,t2,v2 = gather_velocities(velo_dir,velo_type='semblance')
        cmp = np.append(cmp,cmp2)
        v = np.append(v,v2)
        t = np.append(t,t2)
    else:
        cmp,t,v = gather_velocities(velo_dir,velo_type=velo_type)

    xi,yi = np.meshgrid(cmps,times*200)
    vgrid = griddata((cmp,t*200),v,(xi,yi),method='nearest')
    img_gaus =  filters.gaussian_filter(vgrid, [20,5], mode='nearest')
    return img_gaus,(cmp,t,v)
