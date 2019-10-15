import numpy as np
import os
import subprocess

def dipfilt(input_data,min_slope=-0.1,max_slope=0.1,output_data='auto'):

    if output_data == 'auto':
        output_data = input_data[:-3] + '_dipfilt.su'
    cmd = 'sudipfilt<' + input_data + ' dx=1 slopes=-0.01,0,0.01 amps=0,1,0\
            >' + output_data
    subprocess.call(cmd,shell=True)

    return output_data

def medfilt(input_data,median=0,output_data='auto'):
    if output_data == 'auto':
        output_data = input_data[:-3] + '_medfilt.su'

    cmd = 'sumedian<' + input_data + ' xshift=0,20 tshift=0,10 >' + output_data
    subprocess.call(cmd,shell=True)

    return output_data
