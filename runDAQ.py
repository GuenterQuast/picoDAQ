#!/usr/bin/python
# -*- coding: utf-8 -*-
# script runDAQ.py
'''
  **runDAQ** run Data Aquisition with Picoscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

  relies on package *picodaqa*:
    - instance BM of BufferManager class and
    - device initialisation as defined in picoConfig class

  tested with  PS2000a, PS3000a and PS4000

  Functions:
 
    - set up PicoScope channel ranges and trigger
    - PicoScope configuration optionally from json file
    - acquire data (implemented as thread)
    - manage event data and distribute to obligatory and random consumers
    - analyse and plot data:

      - obligatoryConsumer test speed of data acquisition
      - randomConsumer     test concurrent access
      - VMeter             effective Voltages with bar graph display
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

import sys, time, numpy as np, threading
#from multiprocessing import Process, Queue
import multiprocessing as mp

# import relevant pieces from picodaqa
from picodaqa.read_config import *
import picodaqa.picoConfig
import picodaqa.BufferMan

# animated displays running as background processes/threads
import picodaqa.mpOsci
import picodaqa.mpVMeter
import picodaqa.mpRMeter
import picodaqa.mpHists
import picodaqa.AnimatedInstruments # deprecated !!!



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
  # read DAQ configuration file
  if len(sys.argv)==2:
    DAQconfFile = sys.argv[1]
  else: 
    DAQconfFile = 'DAQconfig.json'
  print('    DAQconfiguration from file ' + DAQconfFile)
  try:
    with open(DAQconfFile) as f:
      DAQconfdict=read_config(f)
  except:
    print('     failed to read DAQ configuration file ' + DAQconfFile)
    exit(1)

  if "DeviceFile" in DAQconfdict: 
    DeviceFile = DAQconfdict["DeviceFile"] # configuration file for scope
  else:
    print('     no device configuration file - exiting')
    exit(1)

  if "BMfile" in DAQconfdict: 
    BMfile = DAQconfdict["BMfile"] # Buffer Manager configuration file 
  else:
    print('     no BM configuration file - exiting')
    exit(1)

  if "ANAscript" in DAQconfdict: 
    ANAscript = DAQconfdict["ANAscript"] # configuration file for user analysis 
  else:
    ANAscript = None

  if 'DAQmodules' in DAQconfdict:
    modules = DAQconfdict["DAQmodules"]
  else:
    modules = [] 

    
  # read scope configuration file
  print('    Device configuration from file ' + DeviceFile)
  try:
    with open(DeviceFile) as f:
      PSconfdict=read_config(f)
  except:
    print('     failed to read scope configuration file ' + DeviceFile)
    exit(1)

  # read Buffer Manager configuration file
  try:
    with open(BMfile) as f:
        BMconfdict=read_config(f)
  except:
    print('     failed to read BM input file ' + BMfile)
    exit(1)

# initialisation
  print(' -> initializing PicoScope')

# configure and initialize PicoScope
  PSconf=picodaqa.picoConfig.PSconfig(PSconfdict)
  # copy some of the important configuration variables
  verbose=PSconf.verbose
  NChannels = PSconf.NChannels # number of channels in use
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples

# configure Buffer Manager  ...
  print(' -> initializing BufferMan')
  BM = picodaqa.BufferMan(BMconfdict, PSconf)
# ... tell device what its buffer manager is ...
  PSconf.setBufferManagerPointer(BM)

# ... and start data acquisition thread.
  if verbose:
    print(" -> starting Buffer Manager Threads")   
  BM.start() # set up buffer manager processes  

  if 'DAQmodules' in BMconfdict:
    modules = modules + BMconfdict["DAQmodules"]
                       
# list of modules (= backgound processes) to start
  if type(modules) != list:  
    modules = [modules]
#

# --- infinite LOOP
  try:
    thrds = []
    procs =[]
    
    if ('osci' in modules) or ('VMeter' in modules) or\
       ('RMeter' in modules) or ('BufInfo' in modules):
      # print('calling AnimatedInstruments')
      thrds.append(threading.Thread(target=picodaqa.animInstruments,
                                           args=(modules, PSconf, BM) ) )

# modules to be run as subprocesses
#                  these use multiprocessing.Queue for data transfer
  # rate display
    if 'mpRMeter' in modules:
      RMcidx, RMmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='RMeter', target = picodaqa.mpRMeter, 
                args=(RMmpQ, 75., 2500., 'trigger rate history') ) )
#                         maxRate interval name
  # Voltmeter display
    if 'mpVMeter' in modules:
      VMcidx, VMmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='VMeter', target = picodaqa.mpVMeter, 
                args=(VMmpQ, PSconf, 500., 'effective Voltage') ) )
#                           config interval name

# ---> put your own code here 
    if ANAscript:
      try:
        print('    including user analysis from file ' + ANAscript )
        exec( open(ANAscript).read() )
      except:
        print('     failed to read analysis script ' + ANAscript)
        exit(1)
# <---

    if len(procs)==0 and len(thrds)==0 :
      print ('!!! nothing to do - running BM only')
# start all background processes   
    for prc in procs:
      prc.deamon = True
      prc.start()
      print(' -> starting process ', prc.name, ' PID=', prc.pid)
    time.sleep(1.)
# start threads
    for thrd in thrds:
      thrd.daemon = True
      thrd.start()
# start run
#    BM.setLogQ(logQ) # redirect output to logging Queue
    BM.run() 

# ---- run until key pressed
    # fist, remove pyhton 2 vs. python 3 incompatibility
    if sys.version_info[:2] <=(2,7):
      get_input = raw_input
    else: 
      get_input = input

# ->> wait here until key pressed <<- 
    while True:
      A=get_input(40*' '+'type -> E(nd), P(ause) or R(esume) + <ret> ')
      if A=='P':
        BM.pause()
      elif A=='R':
        BM.resume()
      elif A=='E': 
        break

    print(sys.argv[0]+' preparing to end ...')
    cleanup()
    for prc in procs:
      print('    terminating '+prc.name)
      prc.terminate()
    time.sleep(2)

# ---> end-of-run code could go here
    print('Data Acquisition ended normally')
# <---

  except KeyboardInterrupt:
# END: code to clean up
    print(sys.argv[0]+': keyboard interrupt - preparing to end ...')
    cleanup()
    for prc in procs:
      print('    terminating '+prc.name)
      prc.terminate()
    time.sleep(2)
    sys.exit()
  
  sys.exit()
