from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import numpy as np, matplotlib.pyplot as plt

class DataLogger(object):
  ''' history of data'''

  def __init__(self, Wtime, ConfDict, sigName):
    '''Args:  Wtime: waiting time between updates
              conf: Configuration of channels
    '''
   # collect relevant configuration parameters
    self.Npoints = 120  # number of points for history

    # get relevant oscilloscpe settings   
    self.dT = Wtime/1000. # time interval in s 
    self.Channels = ConfDict['Channels']
    self.NChannels = ConfDict['NChannels']
    self.CRanges = ConfDict['CRanges']
    self.COffsets = ConfDict['ChanOffsets']
    self.ChanColors = ConfDict['ChanColors']

   # data structures needed throughout the class
    self.Ti = self.dT* np.linspace(-self.Npoints+1, 0, self.Npoints) 
    self.Vhist = np.zeros( [self.NChannels, self.Npoints] )

# set up a figure to plot actual voltage and samplings from Picoscope
    fig = plt.figure("DataLogger", figsize=(6., 3.) )
    fig.subplots_adjust(left=0.15, bottom=0.2, right=0.85, top=0.95,
                  wspace=None, hspace=.25)
    axes=[]
  # history plot
    axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
    if self.NChannels > 1:
      axes.append(axes[0].twinx())
    for i, C in enumerate(self.Channels):
      if i > 1:
        break # works for a maximum of 2 Channels only
     # for effective voltage
     # axes[i].set_ylim(0., self.CRanges[i]-self.COffsets[i])
     # for absolute Voltage
      axes[i].set_ylim(-self.CRanges[i]-self.COffsets[i], 
                        self.CRanges[i]-self.COffsets[i])
      axes[i].set_ylabel('Chan ' + C + ' ' + sigName, color=self.ChanColors[i])
    axes[0].set_xlabel('History (s)')

    self.fig = fig
    self.axes = axes
# -- end def __init__

  def init(self):
  # initialize objects to be animated

  # history graphs
    self.graphs=()
    for i, C in enumerate(self.Channels):
      if i > 1:
        break  # max. of 2 channels
   # intitialize with graph outside range
      g,= self.axes[i].plot(self.Ti, 
          (self.CRanges[i]-self.COffsets[i])*1.1*np.ones(self.Npoints), 
          color=self.ChanColors[i])
      self.graphs += (g,)

    return self.graphs
# -- end DataLogger.init()

  def __call__( self, data ):

    if data !=None: 
      n, dat = data

      k = n % self.Npoints
      for i, C in enumerate(self.Channels):
        if i > 1: 
          break  # works for 2 channels only
        self.Vhist[i, k] = dat[i]
    # update history graph
        if n>1: # !!! fix to avoid permanent display of first object in blit mode
          self.graphs[i].set_data(self.Ti,
            np.concatenate((self.Vhist[i, k+1:], self.Vhist[i, :k+1]), axis=0) )

    return self.graphs
#- -end def DataLogger.__call__
#-end class DataLogger
