# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class plotBufManInfo(object):
  ''' display rate history '''

  def __init__(self, BM, maxRate=20.):
    self.BM = BM
    self.maxRate = maxRate

    self.Npoints = 100  # number of history points
    self.R = np.zeros(self.Npoints)
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
    self.R[k] = self.BM.readrate
      
    self.line1.set_ydata(np.concatenate( (self.R[k+1:], self.R[:k+1]) ))
    self.animtxt.set_text( \
     'Time: %.1fs  Triggers: %i  rate: %.3gHz  life: %.1f%%'\
      %(time.time()-self.t0, 
        self.BM.Ntrig, self.BM.readrate, self.BM.lifefrac) )

    return self.line1, self.animtxt  
