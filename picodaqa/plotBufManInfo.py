# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class plotBufManInfo(object):
  ''' display statistics from Buffer Manager

        uses BufferMan InfoQue to display
        total number of events, data acquisition rate,
        life time and buffer filling level
  '''


  def __init__(self, Q, maxRate=20., interval=1000.):
    self.Q = Q
 
    self.maxRate = maxRate
    self.interval = interval/1000 # time between updates in s

    self.Npoints = 100  # number of history points
    self.R = np.zeros(self.Npoints)
    self.xplt = np.linspace(-self.Npoints*self.interval, 0., self.Npoints)

  # create figure 
    self.fig = plt.figure("BufManInfo", figsize=(5.,2.5))
    self.fig.subplots_adjust(left=0.05, bottom=0.2, right=0.925, top=0.85,
               wspace=None, hspace=.25)
    self.axes = self.fig.add_subplot(1,1,1)
    self.axes.yaxis.tick_right()
    self.axes.set_title('Buffer Manager Information')
    self.axes.set_ylabel('acquisition rate (HZ)')
    self.axes.set_xlabel('rate history')
    self.axes.set_ylim(0., self.maxRate)

  def init(self):
    self.line1, = self.axes.plot(self.xplt, self.R, 
      marker = '.', markerfacecolor='b', linestyle='dashed', color='grey', )
    self.animtxt = self.axes.text(0.015, 0.925 , ' ',
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
    RUNNING, Ntrig, Ttrig, readrate, lifefrac, bufLevel = self.Q.get()
    self.R[k] = readrate
      
    self.line1.set_ydata(np.concatenate( (self.R[k+1:], self.R[:k+1]) ))
    self.animtxt.set_text( \
     'Time: %.1fs  Triggers: %i  rate: %.3gHz  life: %.1f%%  buffer: %.0f%%'\
          %(time.time()-self.t0, Ntrig, readrate, lifefrac, bufLevel) )

    return self.line1, self.animtxt  
