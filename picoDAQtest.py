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

import sys, time, numpy as np, threading
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

def read_config(j):
  '''read a json file (with comments marked with '#')
  '''
  import json

# -- helper function to filter input lines
  def filter_lines(f, cc='#'):
    """ remove charcters after comment character cc from file  
      Args:
        * file f:  file 
        * char cc:   comment character
      Yields:
        * string 
    """
    jtxt=''
    while True:
      line=f.readline()
      if (not line): return jtxt # EOF
      if cc in line:
        line=line.split(cc)[0] # ignore everything after comment character    
        if (not line): continue # ignore comment lines
      if (not line.isspace()):  # ignore empty lines
        jtxt += line        
#   -- end filter_lines

  jsontxt = filter_lines(f)
  return json.loads(jsontxt) 

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
  print('     DAQconfiguration from file ' + DAQconfFile)
  try:
    with open(DAQconfFile) as f:
      DAQconfdict=read_config(f)
  except:
    print('     failed to DAQ configuration file ' + DAQconfFile)
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

  # read scope configuration file
  print('     scope configuration from file ' + DeviceFile)
  try:
    with open(DeviceFile) as f:
      PSconfdict=read_config(f)
  except:
    print('     failed to read scope configuration file ' + DeviceFile)
    exit(1)

  # read scope configuration file
  try:
    with open(BMfile) as f:
        BMconfdict=read_config(f)
  except:
    print('     failed to read BM input file ' + BMconfFile)
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
  if "NBuffers" in BMconfdict: 
    NBuffers = BMconfdict["NBuffers"] # number of buffers for Buffer Manager
  else:
    NBuffers= 16
  BM = picodaqa.BufferMan(NBuffers, NChannels, NSamples, TSampling,
        PSconf.acquirePicoData)
# ... tell device what its buffer manager is ...
  PSconf.setBufferManagerPointer(BM)
# ... and start data acquisition thread.
  if verbose>0:
    print(" -> starting Buffer Manager Threads")   
  BM.start() # set up buffer manager processes  
  if "BMmodules" in BMconfdict: 
    BMmodules = BMconfdict["BMmodules"] # display modules to start
  else:
    BMmodules = ["mpBufInfo"]

# temporary for backward compatibility ("modes" defined in PSconfig)
  try: 
    BMmodules = BMmodules + PSconf.mode
  except:
    pass

# for this example, mode encodes what to do ...
  modules = BMmodules
  if type(modules) != list:  
    modules = [modules]
#

# --- infinite LOOP
  try:
    mode_valid = False
    thrds = []
    procs =[]
    
    if ('osci' in modules) or ('VMeter' in modules) or\
       ('RMeter' in modules) or ('BufInfo' in modules):
      mode_valid= True
      # print('calling AnimatedInstruments')
      thrds.append(threading.Thread(target=picodaqa.animInstruments,
                                           args=(modules, PSconf, BM) ) )
      mode_valid= True   

    if 'test' in modules: # test consumers
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

    if 'mpBufInfo' in modules: 
      mode_valid= True
      maxBMrate = 100.
      BMIinterval = 1000.
      procs.append(mp.Process(name='BufManInfo',
                   target = picodaqa.mpBufManInfo, 
                   args=(BM.getBMInfoQue(), maxBMrate, BMIinterval) ) )
#                           BM InfoQue      max. rate  update interval

    if 'mpOsci' in modules: 
      mode_valid= True   
      OScidx, OSmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='Osci',
                              target = picodaqa.mpOsci, 
                              args=(OSmpQ, PSconf, 50., 'event rate') ) )
#                                                interval
    if 'mpRMeter' in modules:
      mode_valid= True   
      RMcidx, RMmpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(name='RMeter',
                target = picodaqa.mpRMeter, 
                args=(RMmpQ, 75., 2500., 'trigger rate history') ) )
#                         maxRate interval name

#    if 'test' in modules:
#      mode_valid= True   
#      cidx, mpQ = BM.BMregister_mpQ()
#    procs.append(mp.Process(target = subprocConsumer, 
#                 args=(mpQ,) ) )
# 

# pulse shape analysis
    if 'filtRMeter' in modules:  # Rate Meter for event filter as sub-process
      mode_valid= True   
      filtRateQ = mp.Queue(1) # information queue for Filter
      procs.append(mp.Process(name='RMeter',
                target = picodaqa.mpRMeter, 
                args=(filtRateQ, 12., 2500., 'muon rate history') ) )
#                      mp.Queue  rate  update interval          

    if 'mpHist' in modules:  # Rate Meter for event filter as sub-process
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
                args=(histQ, Hdescriptors, 2000., 'Filter Histograms') ) )
#                     data Queue, Hist.Desrc  interval    

    if 'pulseFilter' in modules: # event filter as thread 
      mode_valid= True   
      if 'filtRMeter' not in modules: filtRateQ = None
      if 'mpHist' not in modules: histQ = None
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
