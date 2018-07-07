# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import time, numpy as np
import matplotlib.pyplot as plt

class DataGraphs(object):
  ''' Bar graph display of average over samples '''

  def __init__(self, Wtime, ConfDict, XYmode):
    '''Args:   Wtime: waiting time between updates
               conf: Configuration of channels
    '''
 
  # collect relevant configuration parameters
    self.Npoints = 120  # number of points for history
    self.bwidth = 0.5   # width of bars

    # get relevant oscilloscpe settings 
    self.dT = Wtime/1000.  
    self.Channels = ConfDict['Channels']
    self.NChannels = ConfDict['NChannels']
    self.CRanges = ConfDict['CRanges']
    self.COffsets = ConfDict['ChanOffsets']
    self.ChanColors = ConfDict['ChanColors']

    self.XYmode = XYmode
    if self.NChannels < 2: 
      self.XYmode = True

   # data structures needed throughout the class
    self.Ti = self.dT* np.linspace(-self.Npoints+1, 0, self.Npoints) 
    self.ind = self.bwidth + np.arange(self.NChannels) # bar position for voltages
  # 
    self.Vhist = np.zeros( [self.NChannels, self.Npoints] )
    self.d = np.zeros( [self.NChannels, self.Npoints] ) 

# set up a figure to plot actual voltage and samplings from Picoscope
    if self.XYmode:
      fig = plt.figure("DataGraphs", figsize=(9., 5.3) )
      fig.subplots_adjust(left=0.075, bottom=0.1, right=0.975, top=0.94,
                          wspace=1.5, hspace=.25)
    else:
      fig = plt.figure("DataGraphs", figsize=(4., 5.3) )
      fig.subplots_adjust(left=0.2, bottom=0.08, right=0.8, top=0.94,
                  wspace=None, hspace=.25)

    axes=[]

  # history plot
    if self.XYmode:
      axes.append(plt.subplot2grid((6,5),(4,0), rowspan=2, colspan=2) )
    else:
      axes.append(plt.subplot2grid((6,1),(4,0), rowspan=2) )
    if self.NChannels > 1:
      axes.append(axes[0].twinx())
#    axes[1].set_ylim(-self.CRanges[1], self.CRanges[1])
# for effective Voltage
    for i, C in enumerate(self.Channels):
      if i > 1:
        break # works for a maximum of 2 Channels only
     # for absolute Voltage
     # axes[i].set_ylim(-self.CRanges[i]-self.COffsets[i], 
     #                   self.CRanges[i]-self.COffsets[i])
      axes[i].set_ylim(0., self.CRanges[i]-self.COffsets[i])
      axes[i].set_ylabel('Chan ' + C + ' (Veff)', color=self.ChanColors[i])
    axes[0].set_xlabel('History (s)', size='x-large')

  # barchart
    if self.XYmode:
      axes.append(plt.subplot2grid((6,5),(1,0), rowspan=3, colspan=2) )
    else:
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
    axbar1.set_ylim(0., self.CRanges[0]-self.COffsets[0])
    axbar1.axhline(0., color='k', linestyle='-', lw=2, alpha=0.5)
    axbar1.set_ylabel('Chan A (Veff)', size='x-large', color = self.ChanColors[0])
    if self.NChannels > 1:
#     axbar2.set_ylim(-self.CRanges[1], self.CRanges[1])
      axbar2.set_ylim(0., self.CRanges[1]-self.COffsets[1])
      axbar2.set_ylabel('Chan B (Veff)', size='x-large', color = self.ChanColors[1])

  # Voltage in Text format
    if self.XYmode:
      axes.append(plt.subplot2grid((6,5), (0,0), rowspan=1, colspan=2) )
    else:
      axes.append(plt.subplot2grid((6,1), (0,0)) )
    axtxt=axes[-1]
    axtxt.set_frame_on(False)
    axtxt.get_xaxis().set_visible(False)
    axtxt.get_yaxis().set_visible(False)
    axtxt.set_title('Voltmeter', size='xx-large')

  # XY display
    if self.XYmode:
      axes.append(plt.subplot2grid((6,5),(0,2), rowspan=6, colspan=3) )
      axXY = axes[-1]
      axXY.set_xlim(0., self.CRanges[0]-self.COffsets[0])
      axXY.set_ylim(0., self.CRanges[0]-self.COffsets[0])
      axXY.set_xlabel('Chan '+self.Channels[0]+' (Veff)', 
         size='x-large', color=self.ChanColors[0])
      axXY.set_ylabel('Chan '+self.Channels[1]+' (Veff)', 
         size='x-large', color=self.ChanColors[1])
      axXY.set_title('XY-View', size='xx-large')
    else:
      axXY = None

    self.fig = fig
    self.axes = axes
    self.axbar1 = axbar1
    if self.NChannels > 1:
      self.axbar2 = axbar2
    self.axtxt = axtxt
    self.axXY = axXY
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
    for i, C in enumerate(self.Channels):
      if i > 1:
        break  # max. of 2 channels
      g,= self.axes[i].plot(self.Ti, np.zeros(self.Npoints), 
          color=self.ChanColors[i])
      self.graphs += (g,)
    self.animtxt = self.axtxt.text(0.01, 0.05 , ' ',
              transform=self.axtxt.transAxes,
              size='large', color='darkblue')
  
    if self.XYmode:
      g, = self.axXY.plot([0.], [0.], 'g-')
      self.graphs += (g,)

    self.t0=time.time() # remember start time

    if self.NChannels > 1 :
      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)  
    else:
# -- end DataGraphs.init()
      return (self.bgraph1,) + self.graphs + (self.animtxt,)  

  def __call__( self, data ):
    # update graphics with actual data
    if data != None: 
      n, dat = data
      if n == 0:
        return self.init()

      k = n % self.Npoints
      txt=[]
      for i, C in enumerate(self.Channels):
        if i > 1: 
          break  # works for 2 channels only
        self.Vhist[i, k] = dat[i]
    # update history graph
        if n>1: # !!! fix to avoid permanent display of first object in blit mode
          self.d[i] = np.concatenate((self.Vhist[i, k+1:], self.Vhist[i, :k+1]), axis=0)
          self.graphs[i].set_data(self.Ti, self.d[i])
          if self.XYmode:
            self.graphs[-1].set_data(self.d[0], self.d[1])
        txt.append('  %s:   %.3gV' % (C, self.Vhist[i,k]) )
    # update bar chart
      if n>1: # !!! fix to avoid permanent display of first object in blit mode
        self.bgraph1.set_height(dat[0])
        if self.NChannels > 1:
          self.bgraph2.set_height(dat[1])
      else:  
        self.bgraph1.set_height(0.)
        if self.NChannels > 1:
          self.bgraph2.set_height(0.)

      if self.NChannels > 1:
        self.animtxt.set_text(txt[0] + '\n' + txt[1])
      else:
        self.animtxt.set_text(txt[0])
     # -- end if != None

    if self.NChannels > 1 :
      return (self.bgraph1,) + (self.bgraph2,) + self.graphs + (self.animtxt,)
    else:
      return (self.bgraph1,) + self.graphs + (self.animtxt,)
#- -end def DataGraphs.__call__
#-end class VoltMeter
