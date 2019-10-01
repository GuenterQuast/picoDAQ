# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class RMeter(object):
  ''' display rate history

      rate ist caclulated form event number and event time
      from single events requested at regular intervals
  '''

  def __init__(self, 
         maxRate=20., interval= 2500., name='rate history', BM = None):
    '''
      Args:
        MaxRate: maximum expected rate (for y-scale of plot)
    '''
    self.maxRate = maxRate
    self.interval = interval/1000. # time between updates in s
    self.BM = BM
    self.Npoints = 100  # number of history points
    self.R = np.zeros(self.Npoints)
    self.xplt = np.linspace(-self.Npoints*self.interval, 0., self.Npoints)

  # create figure 
    self.fig = plt.figure("RMeter", figsize=(5.,2.2))
    self.fig.subplots_adjust(left=0.05, bottom=0.2, right=0.9, top=0.95,
               wspace=None, hspace=.25)
    self.axes = self.fig.add_subplot(1,1,1)
    self.axes.yaxis.tick_right()
    #self.axes.set_title('')
    self.axes.set_xlim(self.xplt[0], self.xplt[-1])
    self.axes.set_xlabel(name)
    self.axes.set_ylim(0., self.maxRate)
    self.axes.set_ylabel('rate (HZ)')
  
  def init(self):
    self.line1, = self.axes.plot(self.xplt, np.zeros(len(self.xplt)), 
      marker='.', markerfacecolor='b', linestyle='dashed', color='grey')
    self.animtxt = self.axes.text(0.2, 0.925 , ' ',
              transform=self.axes.transAxes,
              size='small', color='darkblue')

    self.T0 = time.time() # start time
    self.t0 = self.T0     # time of last event
    self.n0 = 0
    self.N0 = 0
    return self.line1, self.animtxt  

  def __call__(self, evt):
    n = evt[0]
    if n==0: self.init()
    evNr = evt[1]
    evTime = evt[2]

    k = n%self.Npoints
    # calculate rate from event number and event Time
    
    dn = evNr - self.N0
    dt = time.time() - self.t0
    rate = dn/dt
    self.R[k] = rate
    self.N0 = evNr
    self.t0 += dt

    self.line1.set_ydata(np.concatenate( (self.R[k+1:], self.R[:k+1]) ))

    if self.BM == None:
      self.animtxt.set_text( \
         'Time: %.1fs  Events: %i  Rate: %.3gHz'\
         %(time.time()-self.T0, evNr, rate) )
    else:
      self.animtxt.set_text( \
         'Time: %.1fs  Triggers: %i  rate: %.3gHz  life: %.1f%%'\
         %(time.time()-self.T0, evNr, rate, self.BM.lifefrac) )

    return self.line1, self.animtxt  
