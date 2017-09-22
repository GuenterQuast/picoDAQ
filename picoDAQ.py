# -*- coding: utf-8 -*-
"""
Demonstration der Datenaufnahme mit Picoscope PS2000a 
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time
from picoscope import ps2000a
import pylab as plt
import numpy as np

import matplotlib.animation as anim

if __name__ == "__main__":
    verbose=True  # print detailed info if True

    if verbose: print(__doc__)
    if verbose: print("Attempting to open Picoscope 2000...")
    ps = ps2000a.PS2000a()  
    if verbose:
      print("Found the following picoscope:")
      print(ps.getAllUnitInfo())

# configure oscilloscope
# 1). Time Base

    sampleTime=300E-3
    Nsamples=512
    dT= sampleTime / Nsamples

    TSampling, nSamples, maxSamples = \
        ps.setSamplingInterval(dT, sampleTime)

    if verbose:
      print("Sampling interval = %.4g µs" % (TSampling * 1E6))
      print("Taking  samples = %d" % nSamples)
      print("Maximum samples = %d" % maxSamples)

# 2. Channel Ranges
    Vmax=500E-3       # setChannel command uses next largest amplitude

    RangeA = ps.setChannel('A', 'AC', Vmax,
                                  0.0, enabled=True, BWLimited=False)
    RangeB = ps.setChannel('B', 'AC', Vmax,
                                  0.0, enabled=True, BWLimited=False)
    if verbose:
      print("range channel A = %.3g" % RangeA)
      print("range channel B = %.3g" % RangeB)

#    if verbose:
      print("inializing function generator")   
    ps.setSigGenBuiltInSimple(frequency=50, pkToPk=0.7, waveType="Sine",  
        offsetVoltage=0)

    Nblocks=10
    t0=time.time()
    for i in range(Nblocks):
      ps.setSimpleTrigger('A', Vmax/10., 'Rising', timeout_ms=100, enabled=True)
      ps.runBlock()
#      ps.waitReady()
      while not ps.isReady():
        time.sleep(0.001)
      #      if verbose: print("Done waiting for trigger")
      dataA = ps.getDataV('A', nSamples, returnOverflow=False)
      dataB = ps.getDataV('B', nSamples, returnOverflow=False)

    #  print(np.sum(dataA) )
    dt=time.time() - t0  
    print ('* ==* data acquisition finished after %.3g s' % dt)
    tdead = (dt - Nblocks*TSampling*nSamples)/dt
    print ('   -> dead time %.3g%%' % (tdead*100) )
    
    ps.stop()
    ps.close()

    #Uncomment following for call to .show() to not block
    #plt.ion()
    
    fig=plt.figure(figsize=(10., 7.5) )
    ax=fig.add_subplot(1,1,1)
    dataTimeAxis = np.arange(nSamples) * TSampling
    ax.plot(dataTimeAxis, dataA, label="Voltage A")
    ax.plot(dataTimeAxis, dataB, label="Voltage B")
    ax.grid(True)
    ax.set_title("Picoscope Data")
    ax.set_ylabel("Voltage (V)")
    ax.set_xlabel("Time (s)")
    ax.legend()
    plt.show()   






