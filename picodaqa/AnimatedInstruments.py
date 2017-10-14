# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np

import matplotlib
matplotlib.use('wxagg') # set backend (qt5 not running as thread in background)
#matplotlib.use('tkagg') # set backend (qt5 not running as thread in background)
import matplotlib.pyplot as plt, matplotlib.animation as anim

from .BufferMan import *

'''
Animated graphical displays of data received from BufferMan,

  implemented as random consumers

  need access to an instance of BufferMan and picoConfig

  
'''
# 
### consumer examples with graphics -----------------------------------------
#

def animInstruments(opmode, conf, BM):
  '''
    animated instruments to displays data

    - a "Voltmeter" as an obligatory consumer
    - an Oscilloscpe display  as a random consumer


   Args: 

     opmode: list: "osci", "VMeter" and/or "RMeter"
     conf: instance of configuration class of device
     BM:   buffer manager instance

  '''
# privde access to the relevant instance of class picoConfig as global variables
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

  def yieldVMEvent():
# random consumer of Buffer Manager, receives an event copy
   # this is useful for clients accessing only a subset of events

    myId = BM.BMregister()   # register with Buffer Manager
    mode = 1              # random consumer, request event copy

    evCnt=0
    while BM.RUNNING:
      evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #    print('*==* yieldEventCopy: received event %i' % evNr)
      evCnt+=1
      yield (evCnt, evTime, evData)
    exit(1)

  def yieldOsEvent():
# random consumer of Buffer Manager, receives an event copy
   # this is useful for clients accessing only a subset of events

    myId = BM.BMregister()   # register with Buffer Manager
    mode = 1              # random consumer, request event copy

    evCnt=0
    while BM.RUNNING:
      evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #    print('*==* yieldEventCopy: received event %i' % evNr)
      evCnt+=1
      yield (evCnt, evTime, evData)
    exit(1)
  
  class RateMeter(object):
    ''' display rate history '''

    def __init__(self, maxRate=20.):
      self.Npoints = 100
      self.R = np.zeros(self.Npoints)
      self.maxRate = maxRate
      self.xplt = np.linspace(-self.Npoints, 0., self.Npoints)
    # create figure 
      self.fig = plt.figure("RateMeter", figsize=(5.,2.5))
      self.fig.subplots_adjust(left=0.125, bottom=0.2, right=0.99, top=0.85,
                    wspace=None, hspace=.25)
      self.axes = self.fig.add_subplot(1,1,1)
      self.axes.set_title('Buffer Manager Information')
      self.axes.set_ylabel('acquisition rate (HZ)')
      self.axes.set_xlabel('rate history')
      self.axes.set_ylim(0., self.maxRate)

    def init(self):
      self.line1, = self.axes.plot(self.xplt, self.R, 'b-')
      self.animtxt = self.axes.text(0.2, 0.925 , ' ',
                transform=self.axes.transAxes,
                size='small', color='darkblue')
      self.ro = 0.
      self.n0 = 0
      self.t0 = time.time()
      return self.line1, self.animtxt  

    def __call__(self, n):
      if n == 0:
         self.init()

      k = n%self.Npoints
      self.R[k] = BM.readrate
      
      self.line1.set_ydata(np.concatenate( (self.R[k+1:], self.R[:k+1]) ))
      self.animtxt.set_text( \
       'Time: %.1fs  Triggers: %i  rate: %.3gHz  life: %.1f%%'\
          %(time.time()-self.t0, BM.Ntrig, BM.readrate, BM.lifefrac) )

      return self.line1, self.animtxt  


  class VoltMeter(object):
    ''' Bar graph display of average over samples '''

    def __init__(self, Wtime):
     # Arg: Wtime: waiting time between updates

     # collect relevant configuration parameters
      self.Wtime = Wtime    # time in ms between samplings
      self.Npoints = 120  # number of points for history
      self.bwidth = 0.5   # width of bars

     # data structures needed throughout the class
      self.ix = np.linspace(-self.Npoints+1, 0, self.Npoints) # history plot
      self.ind = self.bwidth + np.arange(NChannels) # bar position for voltages
  # 
      self.V = np.empty(NChannels)
      self.stdV = np.empty(NChannels)
      self.Vhist = np.zeros( [NChannels, self.Npoints] )
      self.stdVhist = np.zeros( [NChannels, self.Npoints] )

# set up a figure to plot actual voltage and samplings from Picoscope
      fig = plt.figure("Voltmeter", figsize=(4., 6.) )
      fig.subplots_adjust(left=0.2, bottom=0.08, right=0.8, top=0.95,
                    wspace=None, hspace=.25)
      axes=[]
    # history plot
      axes.append(plt.subplot2grid((7,1),(5,0), rowspan=2) )
      axes.append(axes[0].twinx())
      axes[0].set_ylim(-CRanges[0], CRanges[0])
      axes[1].set_ylim(-CRanges[1], CRanges[1])
      axes[0].set_xlabel('History')
      axes[0].set_ylabel('Chan A (V)', color=ChanColors[0])
      axes[1].set_ylabel('Chan B (V)', color=ChanColors[1])
    # barchart
      axes.append(plt.subplot2grid((7,1),(1,0), rowspan=4) )
      axbar1=axes[2]
      axbar1.set_frame_on(False)
      axbar2=axbar1.twinx()
      axbar2.set_frame_on(False)
      axbar1.get_xaxis().set_visible(False)
      axbar1.set_xlim(0., NChannels)
      axbar1.axvline(0, color=ChanColors[0])
      axbar1.axvline(NChannels, color=ChanColors[1])
      axbar1.set_ylim(-CRanges[0],CRanges[0])
      axbar1.axhline(0., color='k', linestyle='-', lw=2, alpha=0.5)
      axbar2.set_ylim(-CRanges[1], CRanges[1])
      axbar1.set_ylabel('Chan A (V)', color=ChanColors[0])
      axbar2.set_ylabel('Chan B (V)', color=ChanColors[1])
    # Voltage in Text format
      axes.append(plt.subplot2grid((7,1),(0,0)) )
      axtxt=axes[3]
      axtxt.set_frame_on(False)
      axtxt.get_xaxis().set_visible(False)
      axtxt.get_yaxis().set_visible(False)
      axtxt.set_title('Picoscope as Voltmeter', size='xx-large')

      self.fig = fig
      self.axes = axes
      self.axbar1 = axbar1
      self.axbar2 = axbar2
# -- end def grVMeterIni

    def init(self):
  # initialize objects to be animated

      # a bar graph for the actual voltages
#      self.bgraph = self.axes[0].bar(ind, np.zeros(NChannels), self.bwidth,
#                           align='center', color='grey', alpha=0.5)
      self.bgraph1, = self.axbar1.bar(self.ind[0], 0. , self.bwidth,
                           align='center', color=ChanColors[0], alpha=0.5) 
      self.bgraph2, = self.axbar2.bar(self.ind[1], 0. , self.bwidth,
                           align='center', color=ChanColors[1], alpha=0.5) 
    # history graphs
      self.graphs=()
      for i, C in enumerate(picoChannels):
        g,= self.axes[i].plot(self.ix, np.zeros(self.Npoints), color=ChanColors[i])
        self.graphs += (g,)
      self.animtxt = self.axes[3].text(0.01, 0.05 , ' ',
                transform=self.axes[3].transAxes,
                size='large', color='darkblue')

      self.t0=time.time() # remember start time

      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)  
# -- end VoltMeter.init()

    def __call__( self, (n, evTime, evData) ):
      if n == 0:
        return self.init()

      k=n%self.Npoints
      txt_t='Time  %.1fs' %(evTime-self.t0)            
      txt=[]
      for i, C in enumerate(picoChannels):
        self.V[i] = evData[i].mean()
        self.Vhist[i, k] = self.V[i]
        self.stdV[i] = evData[i].std()
        self.stdVhist[i, k] = self.stdV[i]
      # update history graph
        if n>1: # !!! fix to avoid permanent display of first object in blit mode
          self.graphs[i].set_data(self.ix,
            np.concatenate((self.Vhist[i, k+1:], self.Vhist[i, :k+1]), axis=0) )
        else:
          self.graphs[i].set_data(self.ix, np.zeros(self.Npoints))
        txt.append('  %s:   %.3gV +/-%.2gV' % (C, self.Vhist[i,k], 
                                               self.stdVhist[i,k]) )
    # update bar chart
#      for r, v in zip(bgraph, V):
#          r.set_height(v)
      if n>1: # !!! fix to avoid permanent display of first object in blit mode
        self.bgraph1.set_height(self.V[0])
        self.bgraph2.set_height(self.V[1])
      else:  
        self.bgraph1.set_height(0.)
        self.bgraph2.set_height(0.)
      self.animtxt.set_text(txt_t + '\n' + txt[0] + '\n' + txt[1])
#
      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)
#- -end def Voltmeter.__call__
#-end class VoltMeter
                

  class Oscilloscope(object):
    ''' Oscilloscope: display channel readings in time domain'''

    def __init__(self):
# set up a figure to plot samplings from Picoscope
                   # !!! code will need revision for more than 2 channels 
      fig=plt.figure("Oscilloscope", figsize=(6., 4.) )
      fig.subplots_adjust(left=0.13, bottom=0.125, right=0.87, top=0.925,
                    wspace=None, hspace=.25)
      axes=[]
# channel A
      axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
      axes[0].set_ylim(-CRanges[0],CRanges[0])
      axes[0].grid(True)
      axes[0].set_ylabel("Chan. A     Voltage (V)",
                     size='x-large',color=ChanColors[0])
      axes[0].tick_params(axis='y', colors=ChanColors[0])
# channel B
      if len(picoChannels)>1:
        axes.append(axes[0].twinx())
        axes[1].set_ylim(-CRanges[1],CRanges[1])
        axes[1].set_ylabel("Chan. B     Voltage (V)",
                   size='x-large',color=ChanColors[1])
        axes[1].tick_params(axis='y', colors=ChanColors[1])

  # time base
      axes[0].set_xlabel("Time "+TUnit, size='x-large') 

  # trigger settings
      trgidx=picoChannels.index(trgChan)
      trgax=axes[trgidx]
      trgcol=ChanColors[trgidx]
      if trgActive:      
        axes[0].set_title("Trigger: %s, %.3gV %s" % (trgChan, trgThr, trgTyp),
              color=trgcol,
              fontstyle='italic', fontname='arial', family='monospace',
              horizontalalignment='right')
        axes[0].axhline(0., color='k', linestyle='-.', lw=2, alpha = 0.7)
        trgax.axhline(trgThr, color=trgcol, linestyle='--', alpha = 0.7)
        trgax.axvline(0., color=trgcol, linestyle='--', alpha = 0.5)
      else:
        axes[0].set_title("Trigger: none",
              color='lightgrey', fontstyle='italic', 
              fontname='arial', family='monospace',
              horizontalalignment='right')
    # store graphics objects in class instance
      self.fig = fig
      self.axes=axes
# -- end def __init__()

    def init(self):
  # initialize objects to be animated
      self.graphsOs = ()
      for i, C in enumerate(picoChannels):
        g,= self.axes[i].plot(samplingTimes, np.zeros(NSamples), 
                              color=ChanColors[i])
        self.graphsOs += (g,)
      self.animtxtOs = self.axes[0].text(0.65, 0.94, ' ', 
                       transform=self.axes[0].transAxes,
                       backgroundcolor='white', alpha=0.5)

      self.t0=time.time() # remember start time
      self.n0 = 0         # initialize event counter 

      return self.graphsOs + (self.animtxtOs,)
  
    def __call__( self, (n, evTime, evData) ):
      if n == 0:
        return self.init()

      if n>2:    # !!! fix to avoid permanent display of first line in blit mode
        for i, C in enumerate(picoChannels):
          self.graphsOs[i].set_data(samplingTimes, evData[i])
      else:
        for i, C in enumerate(picoChannels):
          self.graphsOs[i].set_data([],[])

# display rate and life time
      if n-self.n0 == 50:
        txt='rate: %.3gHz  life: %.0f%%' % (BM.readrate, BM.lifefrac)
        self.animtxtOs.set_text(txt)
        self.n0=n
      return self.graphsOs + (self.animtxtOs,)
# -end class Oscilloscope

  def sequence_gen():
  # generator for sequence of integers
    i=0
    while BM.RUNNING:
      i+=1
      yield i
    return

# -----------------------------------------------

# - control part for animated Instruments()
  print('-> AnimatedInstruments called: opmode= ', opmode)

  anims=[]
  if 'RMeter' in opmode:
# RateMeter
    if verbose>0: print(' -> Ratemeter starting')
    RMinterval=1000.
    maxR = 10.  # maximum expected rate
    RM = RateMeter(maxR)
    figRM = RM.fig
    anims.append(anim.FuncAnimation(figRM, RM, sequence_gen,
                         interval=RMinterval, init_func=RM.init,
                         blit=True, fargs=None, repeat=True, save_count=None) )
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  print(opmode)
  if 'VMeter' in opmode:
# Voltmeter
    if verbose>0: print(' -> Voltmeter starting')
    WaitTime=500.
    VM=VoltMeter(WaitTime)
    figVM = VM.fig
    anims.append(anim.FuncAnimation(figVM, VM, yieldVMEvent,
                         interval=WaitTime, init_func=VM.init,
                         blit=True, fargs=None, repeat=True, save_count=None) )
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  if 'osci' in opmode:
# Oscilloscope
    if verbose>0: print(' -> Oscilloscope starting')
    Interval = 50.
    Osci = Oscilloscope()
    figOs = Osci.fig
    anims.append(anim.FuncAnimation(figOs, Osci, yieldOsEvent, interval=Interval,                                         init_func=Osci.init, blit=True,
                         fargs=None, repeat=True, save_count=None))
   # save_count=None is a (temporary) workaround to fix memory leak in animate

# plt.show() or plt.ion() must be run in same thread
  try:
     plt.ioff()
     plt.show()
     print ('   no longer RUNNING, matplotlib animate exiting ...')
     while BM.RUNNING:
       time.sleep(0.5)    
       print (' ... waiting after plt.show()...')
  except: 
    print ('   matplotlib animate killed ...')
