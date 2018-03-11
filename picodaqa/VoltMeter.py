# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class VoltMeter(object):
  ''' Bar graph display of average over samples '''

  def __init__(self, conf):
    '''Args:   Wtime: waiting time between updates
              conf: Configuration of channels
    '''
   # collect relevant configuration parameters
    self.Npoints = 120  # number of points for history
    self.bwidth = 0.5   # width of bars

    self.NChannels = conf.NChannels
    self.CRanges = conf.CRanges     # channel voltage ranges (hw settings)
    self.ChanColors = conf.ChanColors
    self.picoChannels = conf.picoChannels

   # data structures needed throughout the class
    self.ix = np.linspace(-self.Npoints+1, 0, self.Npoints) # history plot
    self.ind = self.bwidth + np.arange(self.NChannels) # bar position for voltages
  # 
    self.V = np.empty(self.NChannels)
    self.stdV = np.empty(self.NChannels)
    self.Vhist = np.zeros( [self.NChannels, self.Npoints] )
    self.stdVhist = np.zeros( [self.NChannels, self.Npoints] )

# set up a figure to plot actual voltage and samplings from Picoscope
    fig = plt.figure("Voltmeter", figsize=(4., 5.3) )
    fig.subplots_adjust(left=0.2, bottom=0.08, right=0.8, top=0.95,
                  wspace=None, hspace=.25)
    axes=[]
  # history plot
    axes.append(plt.subplot2grid((6,1),(4,0), rowspan=2) )
    if self.NChannels > 1:
      axes.append(axes[0].twinx())
# for absolute Voltage
#    axes[0].set_ylim(-self.CRanges[0], self.CRanges[0])
#    axes[1].set_ylim(-self.CRanges[1], self.CRanges[1])
# for effective Voltage
    for i, C in enumerate(self.picoChannels):
      if i > 1:
        break # works for a maximum of 2 Channels only
      axes[i].set_ylim(0., self.CRanges[i])
      axes[i].set_ylabel('Chan ' + C + ' (Veff)', color=self.ChanColors[i])
    axes[0].set_xlabel('History')
  # barchart
    axes.append(plt.subplot2grid((6,1),(1,0), rowspan=3) )
    axbar1 = axes[-1]
    axbar1.set_frame_on(False)
    if self.NChannels > 1:
      axbar2=axbar1.twinx()
      axbar2.set_frame_on(False)
    axbar1.get_xaxis().set_visible(False)
    axbar1.set_xlim(0., self.NChannels)
    axbar1.axvline(0, color = self.ChanColors[0])
    if self.NChannels > 1:
      axbar1.axvline(self.NChannels, color = self.ChanColors[1])

# for absolute Voltage
#    axbar1.set_ylim(-self.CRanges[0], self.CRanges[0])
# for effective Voltage
    axbar1.set_ylim(0., self.CRanges[0])
    axbar1.axhline(0., color='k', linestyle='-', lw=2, alpha=0.5)
    axbar1.set_ylabel('Chan A (Veff)', color = self.ChanColors[0])
    if self.NChannels > 1:
#     axbar2.set_ylim(-self.CRanges[1], self.CRanges[1])
      axbar2.set_ylim(0., self.CRanges[1])
      axbar2.set_ylabel('Chan B (Veff)', color = self.ChanColors[1])
  # Voltage in Text format
    axes.append(plt.subplot2grid((6,1),(0,0)) )
    axtxt=axes[-1]
    axtxt.set_frame_on(False)
    axtxt.get_xaxis().set_visible(False)
    axtxt.get_yaxis().set_visible(False)
    axtxt.set_title('Picoscope as Voltmeter', size='xx-large')

    self.fig = fig
    self.axes = axes
    self.axbar1 = axbar1
    if self.NChannels > 1:
      self.axbar2 = axbar2
# -- end def grVMeterIni

  def init(self):
  # initialize objects to be animated

  # a bar graph for the actual voltages
#    self.bgraph = self.axes[0].bar(ind, np.zeros(self.NChannels), self.bwidth,
#                           align='center', color='grey', alpha=0.5)
    self.bgraph1, = self.axbar1.bar(self.ind[0], 0. , self.bwidth,
       align='center', color = self.ChanColors[0], alpha=0.5) 
    if self.NChannels > 1:
      self.bgraph2, = self.axbar2.bar(self.ind[1], 0. , self.bwidth,
          align='center', color = self.ChanColors[1], alpha=0.5) 
  # history graphs
    self.graphs=()
    for i, C in enumerate(self.picoChannels):
      if i > 1:
        break  # max. of 2 channels
      g,= self.axes[i].plot(self.ix, np.zeros(self.Npoints), 
          color=self.ChanColors[i])
      self.graphs += (g,)
    self.animtxt = self.axes[-1].text(0.01, 0.05 , ' ',
              transform=self.axes[-1].transAxes,
              size='large', color='darkblue')

    self.t0=time.time() # remember start time

    if self.NChannels > 1 :
      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)  
    else:
# -- end VoltMeter.init()
      return (self.bgraph1,) + self.graphs + (self.animtxt,)  

  def __call__( self, evt ):
    n, evNr, evTime, evData = evt
    if n == 0:
      return self.init()

    k=n%self.Npoints
    txt_t='Time  %.1fs' %(evTime)            
    txt=[]
    for i, C in enumerate(self.picoChannels):
      if i > 1: 
        break  # works for 2 channels only
      self.V[i] = np.sqrt (np.inner(evData[i], evData[i])/len(evData[i]) )
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
      if self.NChannels > 1:
        self.bgraph2.set_height(self.V[1])
    else:  
      self.bgraph1.set_height(0.)
      if self.NChannels > 1:
        self.bgraph2.set_height(0.)
    if self.NChannels > 1:
      self.animtxt.set_text(txt_t + '\n' + txt[0] + '\n' + txt[1])
    else:
      self.animtxt.set_text(txt_t + '\n' + txt[0])
#
    if self.NChannels > 1 :
      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)
    else:
      return (self.bgraph1,) + self.graphs + (self.animtxt,)
#- -end def Voltmeter.__call__
#-end class VoltMeter
