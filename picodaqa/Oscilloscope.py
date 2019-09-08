# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np, matplotlib.pyplot as plt

class Oscilloscope(object):
  ''' Oscilloscope: display channel readings in time domain'''

  def __init__(self, OscConfDict, name='event rate', BM = None):
    ''' Args:
          conf: picoConfig instance 
          BM:   BufferMan instance (optional)
    ''' 
    self.name = name
    # get oscilloscpe settings   
    self.Channels = OscConfDict['Channels']
    self.NChannels = OscConfDict['NChannels']
    self.NSamples = OscConfDict['NSamples']
    self.TSampling = OscConfDict['TSampling']
    self.pretrig = OscConfDict['pretrig']
    self.CRanges = OscConfDict['CRanges']
    self.ChanOffsets = OscConfDict['ChanOffsets']
    self.ChanColors = OscConfDict['ChanColors']
    self.trgChan = OscConfDict['trgChan']
    self.trgActive = OscConfDict['trgActive'] 
    self.trgThr = OscConfDict['trgThr'] 
    self.trgTyp = OscConfDict['trgTyp'] 

  # array of sampling times (in ms)
    self.SamplingPeriod = self.TSampling * self.NSamples
    self.samplingTimes =\
         np.linspace(-self.pretrig * self.SamplingPeriod, 
            (1.-self.pretrig) * self.SamplingPeriod, self.NSamples)
    if self.SamplingPeriod < 1E-3:  
      self.samplingTimes *= 1E6
      self.TUnit = '(µs)'
    elif self.SamplingPeriod < 1.:
      self.samplingTimes *= 1E3
      self.TUnit = '(ms)'
    else:
       self.TUnit = '(s)'

    self.BM = BM

# figure parameters
    self.NPoints = 250  # number of points on graph
    self.iStep = int(self.NSamples  / self.NPoints) + 1
# set up a figure to plot samplings from Picoscope
    axes=[]
    if self.NChannels <= 2:
      fig=plt.figure("Oscilloscope", figsize=(6., 3.) )
      axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
      if len(self.Channels)>1:
        axes.append(axes[0].twinx())
      fig.subplots_adjust(left=0.13, bottom=0.15, right=0.87, top=0.925,
                          wspace=0., hspace=0.1)
    else:
      fig=plt.figure("Oscilloscope", figsize=(6., 6.) )
      axes.append(fig.add_subplot(2, 1, 1, facecolor='ivory'))
      axes.append(axes[0].twinx())
      axes.append(fig.add_subplot(2, 1, 2, facecolor='ivory'))
      if self.NChannels > 3:
        axes.append(axes[2].twinx())
      fig.subplots_adjust(left=0.13, bottom=0.1, right=0.87, top=0.925,
                    wspace=-0.1, hspace=.1)
        
    for i in range(self.NChannels):
      axes[i].set_xlim(self.samplingTimes[0], self.samplingTimes[-1])
      axes[i].set_ylim(-self.CRanges[i]-self.ChanOffsets[i], 
                      self.CRanges[i]-self.ChanOffsets[i])
      axes[i].grid(True, color=self.ChanColors[i], linestyle = '--', alpha=0.5)
      axes[i].set_ylabel(self.Channels[i] + "     Voltage (V)",
                   size='large',color = self.ChanColors[i])
      axes[i].tick_params(axis='y', color = self.ChanColors[i])

# time base
    if self.NChannels <=2:
      axes[0].set_xlabel("Time "+self.TUnit, size='large') 
    else:
      axes[0].set_xticklabels([])
      axes[2].set_xlabel("Time "+self.TUnit, size='large') 

# trigger settings
    trgidx=self.Channels.index(self.trgChan)
    trgax=axes[trgidx]
    trgcol=self.ChanColors[trgidx]
    if self.trgActive:      
      trgax.set_title("Trigger: %s, %.3gV %s" \
              % (self.trgChan, self.trgThr, self.trgTyp),
            color=trgcol,
            fontstyle='italic', fontname='arial', family='monospace',
            horizontalalignment='right')
      trgax.axhline(self.trgThr, color=trgcol, 
         linestyle='--', alpha = 0.7)
      axes[0].axvline(0., color=trgcol, 
           linestyle='--', alpha = 0.5)
      if self.NChannels>2:
        axes[2].axvline(0., color=trgcol, 
           linestyle='--', alpha = 0.5)
    else: # no active trigger channel 
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
    for i, C in enumerate(self.Channels):
      g, = self.axes[i].plot([], [], 
                           color=self.ChanColors[i])
      self.graphsOs += (g,)
      g.set_xdata(self.samplingTimes[::self.iStep])
      
    self.animtxtOs = self.axes[0].text(0.65, 0.94, ' ', 
                     transform=self.axes[0].transAxes,
#                     backgroundcolor='white', 
                     alpha=0.7)

    self.T0=time.time() # remember start time
    self.n0 = 0         # initialize counter 
    self.N0 = 0         #   event number

    return self.graphsOs + (self.animtxtOs,)
  
  #def __call__( self, (n, evNr, evTime, evData) ):
  def __call__( self, evt ):
    n, evNr, evTime, evData = evt
    if n == 0:
      return self.init()

    if n == 1: # 1st event sometimes sticks - don't plot
      for i, C in enumerate(self.Channels):
        self.graphsOs[i].set_ydata([None]*len(evData[i, ::self.iStep]) )
    else:
      for i, C in enumerate(self.Channels):
        self.graphsOs[i].set_ydata(evData[i, ::self.iStep])

# display rate and life time
    if n-self.n0 == 50:
      dn = evNr - self.N0
      dt = evTime - self.T0
      rate = dn/dt
      self.N0 = evNr
      self.T0 = evTime
      if self.BM != None: 
        txt='rate: %.3gHz  life: %.0f%%' %(self.BM.readrate, self.BM.lifefrac)
      else:
        txt = self.name + ': %.3g Hz'%(rate)
      self.animtxtOs.set_text(txt)
      self.n0=n
    return self.graphsOs + (self.animtxtOs,)
# -end class Oscilloscope
