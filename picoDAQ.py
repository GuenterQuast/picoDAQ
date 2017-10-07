#!/usr/bin/python
# -*- coding: utf-8 -*-
# script picoDAQ.py
'''
**picoDAQ** Data Aquisition Example with Picoscpe 

Demonstrate data acquisition with PicoScope usb-oscilloscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

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

  For Demo Mode:
     Connect output of signal gnerator to channel B')
     Connect open cable to Channel A \n')
'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, json, numpy as np, threading

# graphical devices use matplotlib
import matplotlib
matplotlib.use('tkagg')  # set backend (qt5 not running as thread in background)
import matplotlib.pyplot as plt, matplotlib.animation as anim

from picoscope import ps2000a
picoDevObj = ps2000a.PS2000a()  
#from picoscope import ps4000
#picoDevObj = ps2000a.PS4000()  

import BufferMan

# --------------------------------------------------------------
#              define scope settings here
# --------------------------------------------------------------

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

import picoConfig

# --------------------------------------------------------------

def picoIni(PSconf):
  ''' initialise device controlled by class PSconf '''
  if verbose>1: print(__doc__)
  if verbose>0: print("Opening PicsoScope device ...")
#  ps = ps2000a.PS2000a()  
  if verbose>1:
    print("Found the following picoscope:")
    print(picoDevObj.getAllUnitInfo())

# configure oscilloscope
# 1) Time Base
  TSampling, NSamples, maxSamples = \
        picoDevObj.setSamplingInterval(PSconf.sampleTime/PSconf.Nsamples, 
               PSconf.sampleTime)
  if verbose>0:
    print("  Sampling interval = %.4g µs (%.4g µs)" \
                   % (TSampling*1E6, PSconf.sampleTime*1E6/PSconf.Nsamples ) )
    print("  Number of samples = %d (%d)" % (NSamples, PSconf.Nsamples))
    #print("Maximum samples = %d" % maxSamples)
# 2) Channel Ranges
    CRanges=[]
    for i, Chan in enumerate(PSconf.picoChannels):
      CRanges.append(picoDevObj.setChannel(Chan, PSconf.ChanModes[i], 
                   PSconf.ChanRanges[i], VOffset=PSconf.ChanOffsets[i], 
                   enabled=True, BWLimited=False) )
      if verbose>0:
        print("  range channel %s: %.3gV (%.3gV)" % (PSconf.picoChannels[i],
                  CRanges[i], PSconf.ChanRanges[i]))
# 3) enable trigger
  picoDevObj.setSimpleTrigger(PSconf.trgChan, PSconf.trgThr, PSconf.trgTyp,
        PSconf.trgDelay, PSconf.trgTO, enabled=PSconf.trgActive)    
  if verbose>0:
    print("  Trigger channel %s enabled: %.3gV %s" % (PSconf.trgChan, 
          PSconf.trgThr, PSconf.trgTyp))

# 4) enable Signal Generator 
  if PSconf.frqSG !=0. :
    picoDevObj.setSigGenBuiltInSimple(frequency=PSconf.frqSG, 
       pkToPk=PSconf.PkToPkSG, waveType=PSconf.waveTypeSG, 
       offsetVoltage=PSconf.offsetVoltageSG, sweepType=PSconf.swpSG, 
       dwellTime=PSconf.dwellTimeSG, stopFreq=PSconf.stopFreqSG)
    if verbose>0:
      print(" -> Signal Generator enabled: %.3gHz, +/-%.3g V %s"\
            % (PSconf.frqSG, PSconf.PkToPkSG, PSconf.waveTypeSG) )
      print("       sweep type %s, stop %.3gHz, Tdwell %.3gs" %\
            (PSconf.swpSG, PSconf.stopFreqSG, PSconf.dwellTimeSG) )

  PSconf.setSamplingPars(TSampling, NSamples, CRanges) # store in config class
 
  return
# -- end def picoIni

def acquirePicoData(buffer):
  '''
  read data from device
    this part is hardware (i.e. driver) specific code for PicoScope device

    Args:
      ps:  class handling devide
      buffer: space to store data

    Returns:
      ttrg: time when device became ready
      tlife life time of device
  '''
  picoDevObj.runBlock(pretrig=pretrig) #
    # wait for PicoScope to set up (~1ms)
  time.sleep(0.001) # set-up time not to be counted as "life time"
  ti=time.time()
  while not picoDevObj.isReady():
    if not RUNNING: return -1, -1
    time.sleep(0.001)
    # waiting time for occurence of trigger is counted as life time
  ttrg=time.time()
  tlife = ttrg - ti       # account life time
  # store raw data in global array 
  for i, C in enumerate(picoChannels):
    picoDevObj.getDataRaw(C, NSamples, data=rawBuf[i])
    picoDevObj.rawToV(C, rawBuf[i], buffer[i], dtype=np.float32)
# alternative:
      #picoDevObj.getDataV(C, NSamples, dataV=VBuf[ibufw,i], dtype=np.float32)
  return ttrg, tlife
#

# - - - - some examples of consumers connected to BufferManager- - - - 

# rely on instance BM of BufferManager class
#   and initialisation of PicoScope parameters as defined in picoDAQ.py 

def obligConsumer():
  '''
    test readout speed: do nothing, just request data from buffer manager

      - an example of an obligatory consumer, sees all data
        (i.e. data acquisition is halted when no data is requested)
    
    for reasons of speed, only a pointer to the event buffer is returned
  '''
# register with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* obligConsumer: event Nr %i, %i events seen'%(evNr,evcnt))

#    introduce random wait time to mimick processing activity
    time.sleep(-0.25 * np.log(np.random.uniform(0.,1.)) )
  return
#-end def obligComsumer

def randConsumer():
  '''
    test readout speed: 
      does nothing except requesting random data samples from buffer manager
  '''

  # register with Buffer Manager
  myId = BM.BMregister()
  mode = 1    # random consumer, request event copy

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* randConsumer: event Nr %i, %i events seen'%(evNr,evcnt))
# introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,1000)/1000.)
# - end def randConsumer()
  return
#

from AnimatedInstruments import *

if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

# initialisation
  print('-> initializing PicoScope')

  PSconf=picoConfig.PSconfig(confdict)
  verbose=PSconf.verbose
  NChannels = PSconf.NChannels

  picoIni(PSconf) 
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples
  SamplingPeriod = TSampling * NSamples  

# !!! remaining global variables, needed by acquirePicoData()
  picoChannels = PSconf.picoChannels
  pretrig = PSconf.pretrig

# reserve global space for data
  # static buffer for picoscope driver for storing raw data
  rawBuf = np.empty([NChannels, NSamples], dtype=np.int16 )

  NBuffers= 16
  BM = BufferMan.BufferMan(NBuffers, NChannels, NSamples, acquirePicoData)

  # start data acquisition thread
  if verbose>0:
    print(" -> starting Buffer Manager Threads")   
  RUNNING = True
  BM.run()  

  mode = PSconf.mode
#
# --- infinite LOOP
  try:
    if mode=='VMeter': # Voltmeter mode
      m=0
    elif mode=='osci': # Oscilloscpe mode
      m=1
    elif mode=='demo': #  both VMeter and Oscilloscpe
      m=2
    elif mode=='test': # test consumers
      thr_randConsumer=threading.Thread(target=randConsumer )
      thr_randConsumer.daemon=True
      thr_randConsumer.start()
      thr_obligConsumer=threading.Thread(target=obligConsumer )
      thr_obligConsumer.daemon=True
      thr_obligConsumer.start()
      m=2
    else:
      print ('!!! no valid mode - exiting')
      exit(1)
    
    thr_animInstruments=threading.Thread(target=animInstruments,
                      args=(m, PSconf, BM) )
    thr_animInstruments.daemon=True
    thr_animInstruments.start()

# run until key pressed
    raw_input('\n                                             Press <ret> to end -> \n\n')
    if verbose: print(' ending  -> cleaning up ')
    RUNNING = False  # stop background processes
    BM.end()         # tell buffer manager that we're done
    time.sleep(2)    #     and wait for tasks to finish
    picoDevObj.stop()
    picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)

#
#    while True:
#      time.sleep(10.)

  except KeyboardInterrupt:
# END: code to clean up
    if verbose>0: print(' <ctrl C>  -> cleaning up ')
    RUNNING = False  # stop background data acquisition
    BM.end()
    time.sleep(2)    #     and wait for tasks to finish
    picoDevObj.stop()
    picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)
  
