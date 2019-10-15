""" A bunch of function to read,write convert and visualize
 reflection seismic data """
import os
import subprocess
import segyio
import matplotlib.pyplot as plt
import numpy as np
from shutil import copyfile


#Geometrie de Mercier
NG = 48
XSHOTS_0 = 76 #70.5 de landstreamer + 5.5 d'offset avec la source
DS = 4.5 #distance entre les shots
DG = 1.5
OFFSETS = np.arange(5.5,77.5,1.5)
TIME = np.arange(0,1000,0.25)

def segy2su(segy_in,su_out = 'auto'):
    if su_out == 'auto':
        su_out = segy_in[:-3] + 'su'
    cmd = 'segyread tape=' + segy_in + ' |segyclean|suchw key1=offset key2=tracf a=4 b=1.5 >' + su_out
    subprocess.call(cmd,shell=True)
    return su_out

def set_geometry(segy_in,bad_shots):
    OUTFILE = segy_in[:-4] + '_geo.sgy'

    bad_shots = np.array(bad_shots)

    with segyio.open(segy_in,'r+',ignore_geometry=True) as f:
        sourceX = f.attributes(segyio.TraceField.SourceX)[:]
        h = f.attributes(segyio.TraceField.HourOfDay)[:]
        m = f.attributes(segyio.TraceField.MinuteOfHour)[:]
        s = f.attributes(segyio.TraceField.SecondOfMinute)[:]
        id_bad = np.isin(f.attributes(segyio.TraceField.FieldRecord)[:],bad_shots)
        data = []
        for i in np.arange(0,sourceX.shape[0]):
            data.append(f.trace[i])

        data = np.array(data)
    #deal with bad shots
    data = data[np.invert(id_bad)]

    #Define geometry
    NSHOTS = data.shape[0]//NG
    RealX_Source = np.arange(XSHOTS_0,XSHOTS_0+(NSHOTS)*DS,DS)
    RealX_Source = np.repeat(RealX_Source,NG)

    # Faire un vecteur pour les positions de géophones
    X_rcv = np.arange((NG-1)*DG,-1,-DG)
    X_rcv = np.tile(X_rcv,NSHOTS)
    X_rcv = X_rcv + (RealX_Source - XSHOTS_0)

    #Un vecteur pour les positions de cdp
    cdp = X_rcv + (RealX_Source-X_rcv)/2

    #write the geometry to the file
    with segyio.open(segy_in,'r+',ignore_geometry=True) as f:
        for i,head in enumerate(f.header):
            try:
                head[segyio.TraceField.SourceX] = int(RealX_Source[i])
                head[segyio.TraceField.CDP] = int(cdp[i])
                head[segyio.TraceField.offset] = int(offset[i])
                head[segyio.TraceField.GroupX] = int(X_rcv[i])
            except:
                pass

    copyfile(segy_in,OUTFILE)

    with segyio.open(OUTFILE,'r+',ignore_geometry=True) as f:
        for i in np.arange(0,data.shape[0]):
                f.trace[i] = data[i]

def plot_shot_from_segy(segy_in,shot_no,scale_factor=1e-3):

    seismic_data = []

    with segyio.open(segy_in,'rb',ignore_geometry=True) as f:
        for i in np.arange(shot_no*NG,(shot_no+1)*NG):
            seismic_data.append(f.trace[i])
        seismic_data = np.array(seismic_data)

    fig,ax = plt.subplots(figsize=(10,10))

    times = seismic_data
    for o, t in zip(OFFSETS,times):
        x = o+t*scale_factor*(0.01*o)
        ax.plot(x,TIME,'k-')
        ax.fill_betweenx(TIME,o,x,where=(x>o),color='k')

    ax.set_ylim(0,1000)
    ax.set_xlim(10,80)
    ax.invert_yaxis()
    ax.set_xlabel('Position relative du géophone (m)',fontsize=14)
    ax.set_ylabel('Temps (ms)',fontsize=14)

#def plot_shot_from_su():
    #à Faire


def plot_stacked_from_su(data_in,extent,aspect=0.2,vmin=-.8,vmax=0.8):
    cmd = 'segyhdrs<' + data_in + ' ns=4000 dt=250|segywrite \
            endian=0 verbose=1 tape=temp.sgy'
    subprocess.call(cmd,shell=True)
    data = []
    with segyio.open('temp.sgy','rb',ignore_geometry=True,) as f:
        for i,trace in enumerate(f.trace):
            data.append(f.trace[i])
        data = np.array(data)
    os.remove('temp.sgy')
    data = data.reshape(-1,len(TIME))
    fig,ax = plt.subplots(figsize=(50,10))
    ax.imshow(data.T,aspect=aspect,cmap='Greys',\
              vmin=vmin,vmax=vmax,extent=extent)
    ax.tick_params(axis='both', which='major', labelsize=18)

def plot_stack_and_velocity(data_in,velo_in,extent,aspect=0.2,vmin=-.8,
                                            vmax=0.8,alpha=0.7):
    cmd = 'segyhdrs<' + data_in + ' ns=4000 dt=250|segywrite \
            endian=0 verbose=1 tape=temp.sgy'
    subprocess.call(cmd,shell=True)
    data = segy2array('temp.sgy')
    os.remove('temp.sgy')
    data = data.reshape(-1,len(TIME))
    fig,ax = plt.subplots(figsize=(50,10))
    ax.imshow(data.T,aspect=aspect,cmap='Greys',\
              vmin=vmin,vmax=vmax,extent=extent)
    im=ax.imshow(np.fromfile(velo_in,'<f4').reshape(-1,4000).T,
                    vmin=150,vmax=300,alpha=alpha, aspect=aspect,extent=extent)
    ax.tick_params(axis='both', which='major', labelsize=18)
    # cbar = plt.colorbar(im,orientation='horizontal')

def print_su_header(data):
    cmd='surange<' + data
    return(subprocess.check_output(cmd,shell=True)).decode()

def segy2array(segy_in):
    data = []
    with segyio.open(segy_in,'rb',ignore_geometry=True,) as f:
        for i,trace in enumerate(f.trace):
            data.append(f.trace[i])
        return np.array(data)

def array2segy(array_in,segy_in,segy_out):
    copyfile(segy_in,segy_out)
    with segyio.open(segy_out,'r+b',ignore_geometry=True,) as f:
        for i,trace in enumerate(f.trace):
            f.trace[i] = array_in[i]


def su2segy(su_in,segy_out = 'auto'):
    if segy_out == 'auto':
        segy_out = su_in[:-2] + 'sgy'
    cmd = 'segyhdrs<' + su_in + ' ns=4000 dt=250|segywrite \
            endian=0 verbose=1 tape=' + segy_out
    subprocess.call(cmd,shell=True)
    return segy_out
