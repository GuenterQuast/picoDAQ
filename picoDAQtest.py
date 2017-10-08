#!/usr/bin/python
# -*- coding: utf-8 -*-
# script picoDAQ.py
'''
**picoDAQ** Data Aquisition Example with Picoscpe 

Demonstrate data acquisition with PicoScope usb-oscilloscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

  tested with  PS2000a and PS4000

  relies on package *picodaqa*:

  - instance BM of BufferManager class and
  - device initialisation as defined in picoConfig class

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
#import matplotlib
#matplotlib.use('tkagg')  # set backend (qt5 not running as thread in background)
#import matplotlib.pyplot as plt, matplotlib.animation as anim

import picodaqa
# contais picoConfig, BufferMan and AnimatedInstruments

# --------------------------------------------------------------
#     scope settings defined in .json-File, see picoConfig
# --------------------------------------------------------------



# - - - - some examples of consumers connected to BufferManager- - - - 


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
    if ('osci' in mode) or ('VMeter' in mode) or ('RMeter' in mode):
      mode_valid= True
      # print('calling AnimatedInstruments')
      thr_animInstruments=threading.Thread(target=picodaqa.animInstruments,
                                           args=(mode, PSconf, BM) )
      thr_animInstruments.daemon=True
      thr_animInstruments.start()
    if 'test' in mode: # test consumers
      thr_randConsumer=threading.Thread(target=randConsumer )
      thr_randConsumer.daemon=True
      thr_randConsumer.start()
      thr_obligConsumer=threading.Thread(target=obligConsumer )
      thr_obligConsumer.daemon=True
      thr_obligConsumer.start()
      mode_valid= True   
# 
# -> put your own code here - for the moment, we exit ...
    if not mode_valid:
      print ('!!! no valid mode - exiting')
      exit(1)
#                                            <--         

# run until key pressed
    raw_input('\n                                             Press <ret> to end -> \n\n')

    if verbose: print(' ending  -> cleaning up ')
    RUNNING = False  # stop background processes
    BM.end()         # tell buffer manager that we're done
    time.sleep(2)    #     and wait for tasks to finish
    PSconf.picoDevObj.stop()
    PSconf.picoDevObj.close()
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
    PSconf.picoDevObj.stop()
    PSconf.picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)
  
