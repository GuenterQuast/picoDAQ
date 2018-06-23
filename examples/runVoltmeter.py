#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''PicoScope as Voltmeter
     this script reads data samples from PicoScope and 
     displays data as effective voltage

     Usage: ./runVoltmeter.py [<Oscilloscpope_config>.yaml Interval]
'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, yaml, numpy as np, multiprocessing as mp

# import relevant pieces from picodaqa
import picodaqa.picoConfig
from picodaqa.mpVMeter import mpVMeter

# helper function
def stop_processes(proclst):
  '''
    Close all running processes at end of run
  '''
  for p in proclst: # stop all sub-processes
    if p.is_alive():
      print('    terminating '+p.name)
      if p.is_alive(): p.terminate()
      time.sleep(1.)

if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

  print('\n*==* script ' + sys.argv[0] + ' running \n')

# check for / read command line arguments
  # read DAQ configuration file
  if len(sys.argv) >= 2:
    PSconfFile = sys.argv[1]
  else: 
    PSconfFile = 'PSVoltMeter.yaml'
  print('    PS configuration from file ' + PSconfFile)

  if len(sys.argv)==3:
    interval = float(sys.argv[2])
  else: 
    interval = 0.5

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
  deltaT = interval * 1000.   # update interval in ms
  VMmpQ =  mp.Queue(1) # Queue for data transfer to sub-process
  procs.append(mp.Process(name='VoltMeter', target = mpVMeter, 
            args=(VMmpQ, PSconf.OscConfDict, deltaT, 'effective Voltage') ) )
#                Queue            config                      interval    name

# start subprocess(es)
  for prc in procs:
    prc.deamon = True
    prc.start()
    print(' -> starting process ', prc.name, ' PID=', prc.pid)

  sig = np.zeros(NChannels)
  PSconf.acquireData(buf) # read initial data from PicoScope
  VMmpQ.put( (0, 0. , buf) ) 

# -- LOOP 
  try:
    cnt = 0
    T0 = time.time()
    print('          type <cntrl>C to end -->')
    while True:
      cnt +=1
      PSconf.acquireData(buf) # read data from PicoScope
      # construct an "event" like BufferMan.py does and send via Queue
      VMmpQ.put( (cnt, time.time()- T0 , buf) ) 

  except KeyboardInterrupt:
    VMmpQ.put( (cnt, time.time()- T0 , buf) ) 
    print('\n' + sys.argv[0]+': keyboard interrupt - closing down ...')
  finally:
    PSconf.closeDevice() # close down hardware device
    time.sleep(1.)
    stop_processes(procs)  # stop all sub-processes in list
    print('*==* ' + sys.argv[0] + ': normal end')
