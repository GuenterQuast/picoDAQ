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
import picodaqa
#  contais picoConfig, BufferMan, AnimatedInstruments, mpOSci, mpRMeter, ...

from exampleConsumers import *

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
    RUNNING = False  # signal to background threads
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
  print('-> initializing PicoScope')

# configure and initialize PicoScope
  PSconf=picodaqa.picoConfig.PSconfig(confdict)
  # copy some of the important configuration variables
  verbose=PSconf.verbose
  NChannels = PSconf.NChannels # number of channels in use
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples


# configure Buffer Manager  ...
  NBuffers= 16 # number of buffers for Buffer Manager
  BM = picodaqa.BufferMan(NBuffers, NChannels, NSamples, 
        PSconf.acquirePicoData)
# ... tell device what its buffer manager is ...
  PSconf.setBufferManagerPointer(BM)
# ... and start data acquisition thread.
  if verbose>0:
    print(" -> starting Buffer Manager Threads")   
  RUNNING = True
  BM.run()  

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
    if 'mpOsci' in mode: 
      mode_valid= True   
      OScidx, OSmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(target = picodaqa.mpOsci, 
                              args=(OSmpQ, PSconf, 50.) ) )
#                                                interval
    if 'mpRMeter' in mode: # as subprocess,
      mode_valid= True   
      RMcidx, RMmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(target = picodaqa.mpRMeter, 
                              args=(RMmpQ, 10., 2500.) ) )
#                                     maxRate  interval
#    if 'test' in mode:
#      mode_valid= True   
#      cidx, mpQ = BM.BMregister_mpQ()
#    procs.append(mp.Process(target = subprocConsumer, 
#                 args=(mpQ,) ) )
# 


# start background processes   
    for prc in procs:
      prc.deamon = True
      prc.start()
    time.sleep(1.)

# start threads
    for thrd in thrds:
      thrd.daemon = True
      thrd.start()
        

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
