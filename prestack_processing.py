""" A bunch of function to process prestack reflection seismic data """
import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np


def kill_geophones(input_data,xi,output_data='auto'):
    """ Function to kill malfunctionning geophones
        Use before gain
        input data: as .su seismic prestack data
        xi:list of ints representing geophone numbers
        """
    if output_data =='auto':
        output_data = input_data[:-3] + '_kill.su'
    a = ','.join(str(i) for i in xi)

    cmd = 'sukill<' + input_data + ' key=tracf a=' + a + '>' + output_data
    subprocess.call(cmd,shell=True)
    return output_data

def bandpass_filter(input_data,low,high,output_data='auto'):
    a = low-10
    b = low
    c = high
    d = high+10
    e = [a,b,c,d]
    f = (',').join(str(i) for i in e)

    if output_data =='auto':
        output_data = input_data[:-3] + '_filtered.su'

    cmd = 'sufilter<' + input_data + ' f=' + f + '>' + output_data
    subprocess.call(cmd, shell=True)
    return output_data

def agc(input_data,window,output_data='auto'):
    if output_data =='auto':
        output_data = input_data[:-3] + '_agc.su'
    cmd = 'sugain<' + input_data + ' agc=1 wagc=' + str(window) + '>' + output_data
    subprocess.call(cmd, shell=True)
    return output_data

def top_mute(input_data,xmute,tmute,output_data='auto'):
    if output_data =='auto':
        output_data = input_data[:-3] + '_muted.su'
    xmute = ','.join(str(i) for i in xmute)
    tmute = ','.join(str(i) for i in tmute)
    cmd = 'sumute<' + input_data + ' xmute=' + xmute + ' tmute=' + \
            tmute + ' key=offset mode=0 >' + output_data
    subprocess.call(cmd, shell=True)
    return output_data

def genCVS(input_data,output_prefix,velocities):
    velocities = list(velocities)
    for v in velocities:
        cmd = 'susort<' + input_data + ' cdp offset | \
                sunmo tnmo=0 vnmo=' + str(v) + '| \
                sustack>' + output_prefix + '_' + str(v) + '.su'
        subprocess.call(cmd, shell=True)

def stack_from_velocity(input_data,velo_in,cdps,times,
                                        output_data = '2D_stack.su',
                                        velo_out='stacking_velocity.bin'):
    vnmo = ''
    cdp = ''
    for i,ci in enumerate(cdps):
        if i%20 == 0:
            vnmo += ' tnmo='
            vnmo += ",".join(str(x)for x in np.round(times,3))
            vnmo += ' vnmo='
            vnmo += ",".join(str(x)for x in np.round(velo_in[:,i],1))
            cdp += str(ci) + ','
    cdp = cdp[:-1]
    cmd = 'susort<' + input_data + ' cdp offset | \
                    sunmo smute=1.7 cdp=' + cdp + vnmo + ' voutfile=' + velo_out + '| \
                    sustack>' + output_data

    subprocess.call(cmd, shell=True)


# def fv_lmo_filtering('')
