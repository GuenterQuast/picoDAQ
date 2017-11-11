# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, numpy as np

import matplotlib
#matplotlib.use('wxagg') # set backend (qt5 not running as thread in background)
matplotlib.use('tkagg') # set backend (qt5 not running as thread in background)
import matplotlib.pyplot as plt, matplotlib.animation as anim

from .BufferMan import *
from .Oscilloscope import *
from .VoltMeter import *
from .plotBufManInfo import *
from .RMeter import *

'''
Animated graphical displays of data received from BufferMan,

  implemented as random consumers

  needs access BufferMan instance and read access to picoConfig
'''
# 
### consumer examples with graphics -----------------------------------------
#

def animInstruments(opmode, conf, BM):
  '''
    animated instruments to display status of buffer manager and
    information from collected data (as random consumers)

      - a "RateMeter" consumer
      - a "Voltmeter" consumer
      - an Oscilloscpe display  
    
    Args: 

      opmode: list: "osci", "VMeter" and/or "RMeter"
      conf: instance of configuration class of device
      BM:   buffer manager instance

  '''
# provde access to the relevant instance of class picoConfig as global variables
  verbose = conf.verbose
  picoChannels = conf.picoChannels
  NChannels = conf.NChannels
  NSamples = conf.NSamples
  TSampling = conf.TSampling
  pretrig = conf.pretrig
  CRanges = conf.CRanges     # channel voltage ranges (hw settings)
  ChanColors = conf.ChanColors
  trgChan = conf.trgChan
  trgActive = conf.trgActive
  trgThr = conf.trgThr
  trgTyp = conf.trgTyp
  # array of sampling times (in ms)
  SamplingPeriod = TSampling * NSamples
  if SamplingPeriod < 1E-3:  
    samplingTimes =\
      1E6*np.linspace(-pretrig * SamplingPeriod, 
                     (1.-pretrig) * SamplingPeriod, NSamples)
    TUnit = '(µs)'
  elif SamplingPeriod < 1.:
    samplingTimes =\
      1E3*np.linspace(-pretrig * SamplingPeriod, 
                     (1.-pretrig) * SamplingPeriod, NSamples)
    TUnit = '(ms)'
  else:
    samplingTimes =\
      1E3*np.linspace(-pretrig * SamplingPeriod, 
                     (1.-pretrig) * SamplingPeriod, NSamples)
    TUnit = '(s)'

# ----- funcion definitions 

  def yieldVMEvent():
# random consumer of Buffer Manager, receives an event copy
   # this is useful for clients accessing only a subset of events
#    if not BM.RUNNING: sys.exit(1)
    if not BM.RUNNING: sys.exit(1)

    myId = BM.BMregister()   # register with Buffer Manager
    mode = 1              # random consumer, request event copy

    evCnt=0
    while BM.RUNNING:
      e = BM.getEvent(myId, mode=mode)
      if e != None:
  #    print('*==* yieldEventCopy: received event %i' % evNr)
        evCnt+=1
        yield (evCnt,) + e

  def yieldOsEvent():
# random consumer of Buffer Manager
    if not BM.RUNNING: sys.exit(1)

    myId = BM.BMregister()   # register with Buffer Manager
    mode = 1              # random consumer, request event copy

    cnt=0
    while BM.RUNNING:
      e = BM.getEvent(myId, mode=mode)
      if e != None:
  #      print('*==* yieldEventCopy: received event %i' % evNr)
        cnt+=1
        yield (cnt,) + e

  def yieldRMEvent():
# random consumer of Buffer Manager
    if not BM.RUNNING: sys.exit(1)
    myId = BM.BMregister()   # register with Buffer Manager
    mode = 1              # random consumer, request event copy

    cnt=0
    while BM.RUNNING:
      e = BM.getEvent(myId, mode=mode)
      if e != None:
  #    print('*==* yieldEventCopy: received event %i' % evNr)
        cnt+=1
        yield (cnt,) + e

  def sequence_gen():
  # generator for sequence of integers
    i=0
    while BM.RUNNING:
      i+=1
      yield i
    return

# -----------------------------------------------

# - control part for animated Instruments()
  print('*==* AnimatedInstruments: opmode= ', opmode)

  anims=[]
  if 'RMeter' in opmode:
# RateMeter
    if verbose>0: print(' -> Ratemeter starting')
    RMinterval=1000.
    maxR = 10.  # maximum expected rate
    RM = RMeter(maxR, RMinterval, BM)
    figRM = RM.fig
    anims.append(anim.FuncAnimation(figRM, RM, yieldRMEvent,
                         interval=RMinterval, init_func=RM.init,
                         blit=True, fargs=None, repeat=True, save_count=None) ) 
  # save_count=None is a (temporary) workaround to fix memory leak in animate

  if 'BufInfo' in opmode:
# Buffer Manager Info
    if verbose>0: print(' -> plotBufManInfo starting')
    BMinterval=1000.
    maxR = 100.  # maximum expected rate
    BMi = plotBufManInfo(BM, maxR, BMinterval)
    figBMi = BMi.fig
    anims.append(anim.FuncAnimation(figBMi, BMi, sequence_gen,
                         interval=BMinterval, init_func=BMi.init,
                         blit=True, fargs=None, repeat=True, save_count=None) )

  if 'VMeter' in opmode:
# Voltmeter
    if verbose>0: print(' -> Voltmeter starting')
    WaitTime=500.
    VM=VoltMeter(WaitTime, conf)
    figVM = VM.fig
    anims.append(anim.FuncAnimation(figVM, VM, yieldVMEvent,
                         interval=WaitTime, init_func=VM.init,
                         blit=True, fargs=None, repeat=True, save_count=None) )
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  if 'osci' in opmode:
# Oscilloscope
    if verbose>0: print(' -> Oscilloscope starting')
    Interval = 50.
#    Osci = Oscilloscope(conf, BM)
    Osci = Oscilloscope(conf)
    figOs = Osci.fig
    anims.append(anim.FuncAnimation(figOs, Osci, yieldOsEvent, interval=Interval,                                         init_func=Osci.init, blit=True,
                         fargs=None, repeat=True, save_count=None))
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  try:
    plt.show()
    print ('*==* AnimatedInstruments: exiting ...')    
  except: 
    print ('!==! AnimatedInstruments: killed ...')
  sys.exit()  
