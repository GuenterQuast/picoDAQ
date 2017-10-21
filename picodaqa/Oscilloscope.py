# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np, matplotlib.pyplot as plt

class Oscilloscope(object):
  ''' Oscilloscope: display channel readings in time domain'''

  def __init__(self, conf, BM = None):
    ''' Args:
          conf: picoConfig instance 
          BM:   BufferMan instance (optional)
    ''' 

    self.picoChannels = conf.picoChannels
    self.NChannels = conf.NChannels
    self.NSamples = conf.NSamples
    self.TSampling = conf.TSampling
    self.pretrig = conf.pretrig
    self.CRanges = conf.CRanges     # channel voltage ranges (hw settings)
    self.ChanColors = conf.ChanColors
    self.trgChan = conf.trgChan
    self.trgActive = conf.trgActive
    self.trgThr = conf.trgThr
    self.trgTyp = conf.trgTyp
  # array of sampling times (in ms)
    self.SamplingPeriod = self.TSampling * self.NSamples
    self.samplingTimes =\
         np.linspace(-self.pretrig * self.SamplingPeriod, 
            (1.-self.pretrig) * self.SamplingPeriod, self.NSamples)
    if self.SamplingPeriod < 1E-3:  
      self.samplingTimes *= 1E-6
      self.TUnit = '(µs)'
    elif self.SamplingPeriod < 1.:
      self.samplingTimes *= 1E-3
      self.TUnit = '(ms)'
    else:
       self.TUnit = '(s)'

    self.BM = BM

# set up a figure to plot samplings from Picoscope
                 # !!! code will need revision for more than 2 channels 
    fig=plt.figure("Oscilloscope", figsize=(6., 4.) )
    fig.subplots_adjust(left=0.13, bottom=0.125, right=0.87, top=0.925,
                    wspace=None, hspace=.25)
    axes=[]
# channel A
    axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
    axes[0].set_ylim(-self.CRanges[0], self.CRanges[0])
    axes[0].grid(True)
    axes[0].set_ylabel("Chan. A     Voltage (V)",
                   size='x-large',color = self.ChanColors[0])
    axes[0].tick_params(axis='y', colors = self.ChanColors[0])
# channel B
    if len(self.picoChannels)>1:
      axes.append(axes[0].twinx())
      axes[1].set_ylim(-self.CRanges[1], self.CRanges[1])
      axes[1].set_ylabel("Chan. B     Voltage (V)",
                 size='x-large', color = self.ChanColors[1])
      axes[1].tick_params(axis='y', colors = self.ChanColors[1])

# time base
    axes[0].set_xlabel("Time "+self.TUnit, size='x-large') 

# trigger settings
    trgidx=self.picoChannels.index(self.trgChan)
    trgax=axes[trgidx]
    trgcol=self.ChanColors[trgidx]
    if self.trgActive:      
      axes[0].set_title("Trigger: %s, %.3gV %s" \
              % (self.trgChan, self.trgThr, self.trgTyp),
            color=trgcol,
            fontstyle='italic', fontname='arial', family='monospace',
            horizontalalignment='right')
      axes[0].axhline(0., color='k', linestyle='-.', lw=2, alpha = 0.7)
      trgax.axhline(self.trgThr, color=trgcol, 
         linestyle='--', alpha = 0.7)
      trgax.axvline(0., color=trgcol, 
         linestyle='--', alpha = 0.5)
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
    for i, C in enumerate(self.picoChannels):
      g,= self.axes[i].plot(self.samplingTimes, np.zeros(self.NSamples), 
                           color=self.ChanColors[i])
      self.graphsOs += (g,)
    self.animtxtOs = self.axes[0].text(0.65, 0.94, ' ', 
                     transform=self.axes[0].transAxes,
                     backgroundcolor='white', alpha=0.5)

    self.T0=time.time() # remember start time
    self.n0 = 0         # initialize counter 
    self.N0 = 0         #   event number

    return self.graphsOs + (self.animtxtOs,)
  
  def __call__( self, (n, evNr, evTime, evData) ):
    if n == 0:
      return self.init()

    if n>2:    # !!! fix to avoid permanent display of first line in blit mode
      for i, C in enumerate(self.picoChannels):
        self.graphsOs[i].set_data(self.samplingTimes, evData[i])
    else:
      for i, C in enumerate(self.picoChannels):
        self.graphsOs[i].set_data([],[])

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
        txt='event rate: %.3g Hz' %(rate)
      self.animtxtOs.set_text(txt)
      self.n0=n
    return self.graphsOs + (self.animtxtOs,)
# -end class Oscilloscope
