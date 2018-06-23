#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Data Logger 
     reads samples from PicoScope and display averages as voltage history

     Usage: ./runDataLogger.py [<Oscilloscpope_config>.yaml Interval]

'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, yaml, numpy as np, multiprocessing as mp

# import relevant pieces from picodaqa
import picodaqa.picoConfig
from picodaqa.mpDataLogger import mpDataLogger

# helper function
def stop_processes(proclst):
  '''
    Close all running processes at end of run
  '''
  for p in proclst: # stop all sub-processes
    if p.is_alive():
      print('    terminating '+p.name)
      p.terminate()
      time.sleep(1.)

if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

  print('\n*==* script ' + sys.argv[0] + ' running \n')

# check for / read command line arguments
  # read DAQ configuration file
  if len(sys.argv)>=2:
    PSconfFile = sys.argv[1]
  else: 
    PSconfFile = 'PSdataLogger.yaml'
  print('    PS configuration from file ' + PSconfFile)

  if len(sys.argv)==3:
    interval = float(sys.argv[2])
  else: 
    interval = 0.2

  # read scope configuration file
  print('    Device configuration from file ' + PSconfFile)
  try:
    with open(PSconfFile) as f:
      PSconfDict=yaml.load(f)
  except:
    print('     failed to read scope configuration file ' + PSconfFile)
    exit(1)

# configure and initialize PicoScope
  PSconf=picodaqa.picoConfig.PSconfig(PSconfDict)
  PSconf.init()
  # copy some of the important configuration variables
  NChannels = PSconf.NChannels # number of channels in use
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples
  buf = np.zeros( (NChannels, NSamples) ) # data buffer for PicoScope driver

  procs=[]
  deltaT = interval *1000   # minimal time between figure updates in ms
  DLmpQ =  mp.Queue(1) # Queue for data transfer to sub-process
  procs.append(mp.Process(name='DataLogger', target = mpDataLogger, 
               args=(DLmpQ, PSconf.OscConfDict, deltaT, '(Volt)') ) )
#                   Queue        config       interval    name

# start subprocess(es)
  for prc in procs:
    prc.deamon = True
    prc.start()
    print(' -> starting process ', prc.name, ' PID=', prc.pid)

    sig = np.zeros(NChannels)

  # -- LOOP 
  try:
    print('          type <cntrl>C to end -->')
    while True:
      PSconf.acquireData(buf) # read data from PicoScope
      for i, b in enumerate(buf): # process data 
        # sig[i] = np.sqrt (np.inner(b, b) / NSamples)    # eff. Voltage
        sig[i] = b.sum() / NSamples          # average
      DLmpQ.put(sig) 

  except KeyboardInterrupt:
     print(sys.argv[0]+': keyboard interrupt - closing down ...')
  finally:
    PSconf.closeDevice() # close down hardware device
    DLmpQ.put(None) 
    time.sleep(1.)
    stop_processes(procs)  # stop all sub-processes in list
    print('*==* ' + sys.argv[0] + ': normal end')
