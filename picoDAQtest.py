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

  For Demo Mode:
     Connect output of signal gnerator to channel B')
     Connect open cable to Channel A \n')
'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, json, numpy as np, threading
#from multiprocessing import Process, Queue
import multiprocessing as mp
import picodaqa
#       contais picoConfig, BufferMan, AnimatedInstruments, mpOSci ...

# !!!!
import matplotlib.pyplot as plt
# !!!!

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
def subprocConsumer(Q):
  '''
    test consumer in subprocess 
      reads event data from multiprocessing.Queue()
  '''    
  cnt = 0  
  try:         
    while True:
      evN, evT, evBuf = mpQ.get()
      cnt += 1
      print('*==* mpQ: got event %i'%(evN) )
      if cnt <= 3:
        print('     event data \n', evBuf)        
      time.sleep(1.)
  except:
    print('subprocConsumer: signal recieved, ending')

def cleanup():
    if verbose: print('  ending  -> cleaning up ')
    RUNNING = False  # signal to background thrads
    time.sleep(1)
    BM.end()         # tell buffer manager that we're done
    time.sleep(2)    #     and wait for tasks to finish
    PSconf.picoDevObj.stop()
    PSconf.picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)

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
    if ('osci' in mode) or ('VMeter' in mode) or ('RMeter' in mode):
      mode_valid= True
      # print('calling AnimatedInstruments')
      thrds.append(threading.Thread(target=picodaqa.animInstruments,
                                           args=(mode, PSconf, BM) ) )
      mode_valid= True   

    if 'test' in mode: # test consumers
      thrds.appene(threading.Thread(target=randConsumer ) )
      thrds.append(threading.Thread(target=obligConsumer ) )
      mode_valid= True   

    if 'mpOsci' in mode: # text subprocess,
     # use multiprocessing.Queue for data transfer
      cidx, mpQ = BM.BMregister_mpQ()
      procs.append(mp.Process(target = picodaqa.mpOsci, 
                 args=(PSconf, mpQ,) ) )
#    procs.append(mp.Process(target = subprocConsumer, 
#                 args=(mpQ,) ) )
# 
      mode_valid= True   

# start threads
    for thrd in thrds:
      thrd.daemon = True
      thrd.start()

# start background processes   
    for prc in procs:
      prc.deamon = True
      prc.start()

# -> put your own code here - for the moment, we simply wait ...
    if not mode_valid:
      print ('!!! no valid mode - exiting')
      exit(1)


# run until key pressed
    raw_input('\n                                  Press <ret> to end -> \n\n')
    print('picoDAQtest preparing to end ...')
    for prc in procs:
      prc.terminate()
    cleanup()
    time.sleep(2)

  except KeyboardInterrupt:
# END: code to clean up
    print('picoDAQtest: keyboard interrupt - preparing to end ...')
    for prc in procs:
      prc.terminate()
    cleanup()
    time.sleep(2)
  
