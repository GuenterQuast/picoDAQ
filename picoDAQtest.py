#!/usr/bin/python
# -*- coding: utf-8 -*-
# script picoDAQ.py
'''
  **picoDAQtest** Data Aquisition Example with Picoscpe 

  Demonstrate data acquisition with PicoScope usb-oscilloscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

  relies on package *picodaqa*:
    - instance BM of BufferManager class and
    - device initialisation as defined in picoConfig class

  tested with  PS2000a and PS4000

  Functions:
 
    - set up PicoScope channel ranges and trigger
    - PicoScope configuration optionally from json file
    - acquire data (implemented as thread)
    - manage event data and distribute to obligatory and random consumers
    - analyse and plot data:

      - obligatoryConsumer test speed of data acquisition
      - randomConsumer     test concurrent access
      - VMeter             average Voltages with bar graph display
      - Osci               simple waveform display
      - RMeter             displays event rate as a function of time
      - Histogram          histogramms event variables

  graphics implemented with matplotlib

  For Demo Mode: Connect output of signal gnerator to channel B, 
  and an open cable to Channel A
'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, json, numpy as np, threading
#from multiprocessing import Process, Queue
import multiprocessing as mp

# import relevant pieces from picodaqa
import picodaqa.picoConfig
import picodaqa.BufferMan

# animated displays running as background processes/threads
import picodaqa.mpBufManInfo
import picodaqa.mpOsci
import picodaqa.mpRMeter
import picodaqa.mpLogWin
import picodaqa.mpHists
import picodaqa.AnimatedInstruments

# examples of consumers and analysers
from exampleConsumers import *
from pulseFilter import *

# !!!!
# import matplotlib.pyplot as plt
# !!!! matplot can only be used if no other thread using it is active


# --------------------------------------------------------------
#     scope settings defined in .json-File, see picoConfig
# --------------------------------------------------------------

def cleanup():
    if verbose: print('  ending  -> cleaning up ')
    BM.end()         # tell buffer manager that we're done
    time.sleep(2)    #     and wait for tasks to finish
    PSconf.picoDevice.stop()
    PSconf.picoDevice.close()
    time.sleep(1)
#    if verbose>0: print('                      -> exit')
#    sys.exit(0)

if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

  print('\n*==* script ' + sys.argv[0] + ' executing')

# check for / read command line arguments
  if len(sys.argv)==2:
    jsonfname = sys.argv[1]
    print('     scope configurtion from file ' + jsonfname)
    try:
      with open(jsonfname) as f:
        confdict=json.load(f)
    except:
      print('     failed to read input file ' + jsonfname)
      exit(1)
  else:
    confdict=None

# initialisation
  print(' -> initializing PicoScope')

# configure and initialize PicoScope
  PSconf=picodaqa.picoConfig.PSconfig(confdict)
  # copy some of the important configuration variables
  verbose=PSconf.verbose
  NChannels = PSconf.NChannels # number of channels in use
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples

# configure Buffer Manager  ...
  NBuffers= 16 # number of buffers for Buffer Manager
  BM = picodaqa.BufferMan(NBuffers, NChannels, NSamples, TSampling,
        PSconf.acquirePicoData)
# ... tell device what its buffer manager is ...
  PSconf.setBufferManagerPointer(BM)
# ... and start data acquisition thread.
  if verbose>0:
    print(" -> starting Buffer Manager Threads")   
  BM.start() # set up buffer manager processes  

# for this example, mode encodes what to do ...
  mode = PSconf.mode
  if type(mode) != list:  
    mode = [mode]
#

# --- infinite LOOP
  try:
    mode_valid = False
    thrds = []
    procs =[]
    
    if ('osci' in mode) or ('VMeter' in mode) or\
       ('RMeter' in mode) or ('BufInfo' in mode):
      mode_valid= True
      # print('calling AnimatedInstruments')
      thrds.append(threading.Thread(target=picodaqa.animInstruments,
                                           args=(mode, PSconf, BM) ) )
      mode_valid= True   

    if 'test' in mode: # test consumers
      thrds.append(threading.Thread(target=randConsumer,
                                    args=(BM,) ) )
      thrds.append(threading.Thread(target=obligConsumer,
                                    args=(BM,) ) )
      mode_valid= True   

# modules to be run as a subprocess
#     use multiprocessing.Queue for data transfer

  # logging window for buffer manager
    logQ = mp.Queue()
    procs.append(mp.Process(name='LogWin', 
                        target = picodaqa.mpLogWin, 
                        args=(logQ, ) ) )

    if 'mpBufInfo' in mode: 
      mode_valid= True
      maxBMrate = 100.
      BMIinterval = 1000.
      procs.append(mp.Process(name='BufManInfo',
                   target = picodaqa.mpBufManInfo, 
                   args=(BM.getBMInfoQue(), maxBMrate, BMIinterval) ) )
#                           BM InfoQue      max. rate  update interval

    if 'mpOsci' in mode: 
      mode_valid= True   
      OScidx, OSmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='Osci',
                              target = picodaqa.mpOsci, 
                              args=(OSmpQ, PSconf, 50., 'event rate') ) )
#                                                interval
    if 'mpRMeter' in mode:
      mode_valid= True   
      RMcidx, RMmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='RMeter',
                target = picodaqa.mpRMeter, 
                args=(RMmpQ, 75., 2500., 'trigger rate history') ) )
#                         maxRate interval name

#    if 'test' in mode:
#      mode_valid= True   
#      cidx, mpQ = BM.BMregister_mpQ()
#    procs.append(mp.Process(target = subprocConsumer, 
#                 args=(mpQ,) ) )
# 

# pulse shape analysis
    if 'filtRMeter' in mode:  # Rate Meter for event filter as sub-process
      mode_valid= True   
      filtRateQ = mp.Queue(1) # information queue for Filter
      procs.append(mp.Process(name='RMeter',
                target = picodaqa.mpRMeter, 
                args=(filtRateQ, 12., 2500., 'muon rate history') ) )
#                      mp.Queue  rate  update interval          

    if 'mpHist' in mode:  # Rate Meter for event filter as sub-process
      mode_valid= True   
      histQ = mp.Queue(1) # information queue for Filter
#  book histograms and start histogrammer
      Hdescriptors = []
      Hdescriptors.append([0., 0.4, 50, 10., 'noise Trg. Pulse (V)', 0] )
      Hdescriptors.append([0., 0.8, 50, 10., 'valid Trg. Pulse (V)', 0] )
      Hdescriptors.append([0., 0.8, 50, 10., 'Pulse height (V)', 0] )
      Hdescriptors.append([0., 7., 35, 7.5, 'Tau (µs)', 1] )
      procs.append(mp.Process(name='Hists',
                              target = picodaqa.mpHists, 
                              args=(histQ, Hdescriptors, 2000.) ) )
#                                data Queu, Hist.Desrc  interval    

    if 'pulseFilter' in mode: # event filter as thread 
      mode_valid= True   
      if 'filtRMeter' not in mode: filtRateQ = None
      if 'mpHist' not in mode: histQ = None
      thrds.append(threading.Thread(target=pulseFilter,
            args = ( BM, filtRateQ, histQ, True, 1) ) )
#                        RMeterQ   histQ  fileout verbose    

#   could also run this in main thread
#     pulseFilter(BM, filtRateQ, verbose=1) 

# start all background processes   
    for prc in procs:
      prc.deamon = True
      prc.start()
      print(' -> starting process ', prc.name, ', PID=', prc.pid)
    time.sleep(1.)

# start threads
    for thrd in thrds:
      thrd.daemon = True
      thrd.start()
        
# start run
    BM.setLogQ(logQ) # redirect output to logging Queue
    BM.run() 

# -> put your own code here - for the moment, we simply wait ...
    if not mode_valid:
      print ('!!! no valid mode - exiting')
      exit(1)


# ---- run until key pressed
    # fist, remove pyhton 2 vs. python 3 incompatibility
    if sys.version_info[:2] <=(2,7):
      get_input = raw_input
    else: 
      get_input = input

# ->> wait here until key pressed <<- 
    get_input('\n                                  Press <ret> to end -> \n\n')

    print('picoDAQtest preparing to end ...')
    cleanup()
    for prc in procs:
      prc.terminate()
    time.sleep(2)

  except KeyboardInterrupt:
# END: code to clean up
    print('picoDAQtest: keyboard interrupt - preparing to end ...')
    cleanup()
    for prc in procs:
      prc.terminate()
    time.sleep(2)
    sys.exit()
  
  sys.exit()
