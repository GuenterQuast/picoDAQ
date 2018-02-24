# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class BarDisplay(object):
  ''' horizontal bar graph display of signal property per channel'''

  def __init__(self, conf, mode=0, size=1):
    '''Args:
          conf: Configuration of channels
          mode: 0=signed, 1=absolute, 2=absolute symmetric
          size: stretch factor
    '''
   # collect relevant configuration parameters
    self.NChan = conf.NChannels
    self.CNames = conf.picoChannels
    self.Range = conf.CRanges[0]+abs(conf.ChanOffsets[0]) # voltage range
    self.trgChan = conf.trgChan
    self.mode = mode # display mode

    self.bheight = 0.8   # width of bars
    
   # data structures needed throughout the class
    self.yvals = self.NChan - 0.5 - np.arange(self.NChan) # bar position for voltages
  # 
# set up a figure to plot actual voltage and samplings from Picoscope
    fig = plt.figure("Bar Graph", figsize=(2.5*size, self.NChan*0.5*size) )
    fig.subplots_adjust(left=0.05, bottom=0.1, right=0.95, top=0.95,
                  wspace=None, hspace=.25)
    axbar = fig.add_subplot(1,1,1)
  # barchart
    axbar.set_frame_on(False)
    if self.mode==2: axbar.get_xaxis().set_visible(False)
    axbar.get_yaxis().set_visible(False)
    if self.mode==1: 
      axbar.set_xlim(0., self.Range)
    else:
      axbar.set_xlim(-self.Range, self.Range)
    axbar.set_ylim(0., self.NChan)
    for i in range(self.NChan+1):
      axbar.axhline(float(i), color = 'darkblue', linewidth=3)
    axbar.axvline(-self.Range, color = 'darkblue', linewidth=3)
    axbar.axvline(self.Range, color = 'darkblue', linewidth=3)
    axbar.axvline(0., color = 'darkblue', linewidth=1, linestyle='--')
    for i, C in enumerate(self.CNames):
      if C == self.trgChan: 
        col='red'
      else:
        col='blue'
      axbar.text(0., self.yvals[i], C, size='xx-large', color=col)
    self.fig = fig
    self.axbar = axbar
# -- end def BarDisplay __init__()

  def init(self):
  # initialize objects to be animated
    self.barsp = ()
    self.barsm = ()
    colr='gold'
    for i in range(self.NChan):
       b, = self.axbar.barh(self.yvals[i], 0. , self.bheight, 
           align='center', color = colr, alpha=0.5) 
       self.barsp += b,
       if self.mode==2:
         b, = self.axbar.barh(self.yvals[i], 0. , self.bheight, 
           align='center', color = colr, alpha=0.5) 
         self.barsm += b,

    return self.barsm + self.barsp
# -- end BarDisplay.init()

  def __call__( self, vals ):
  # update bar chart
    for i in range(self.NChan):
      self.barsp[i].set_width(vals[i])
      if self.mode==2: 
        self.barsm[i].set_width(-vals[i])

    return self.barsm + self.barsp
#- -end def BarDisplay.__call__

#-end class BarDisplay
