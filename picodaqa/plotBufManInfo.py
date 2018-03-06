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
 
    self.ymax = maxRate
    self.interval = interval/1000 # time between updates in s

    self.Npoints = 100  # number of history points
    self.R = np.zeros(self.Npoints)
    self.xplt = np.linspace(-self.Npoints*self.interval, 0., self.Npoints)

  # create figure 
    self.fig = plt.figure("BufManInfo", figsize=(5.,2.))
    self.fig.subplots_adjust(left=0.05, bottom=0.25, right=0.925, top=0.95,
               wspace=None, hspace=.25)
    self.axtext=plt.subplot2grid((7,1),(0,0), rowspan=2) 
    self.axrate=plt.subplot2grid((7,1),(2,0), rowspan=5) 
#    self.axtext.set_title('Buffer Manager Information')
    self.axtext.set_frame_on(False)
    self.axtext.get_xaxis().set_visible(False)
    self.axtext.get_yaxis().set_visible(False)
    self.axrate.yaxis.tick_right()
    self.axrate.set_ylabel('DAQ rate (HZ)')
    self.axrate.set_xlabel('rate history')
    self.ymin = 0.1
    self.axrate.set_ylim(self.ymin, self.ymax)
    self.axrate.set_yscale('log')
    self.axrate.grid(True, alpha=0.5)

  def init(self):
    self.line1, = self.axrate.plot(self.xplt, self.R, 
      marker = '.', markerfacecolor='b', linestyle='dashed', color='grey', )
    self.animtxt1 = self.axtext.text(0.015, 0.65 , ' ',
              transform=self.axtext.transAxes, color='darkblue')
    self.animtxt2 = self.axtext.text(0.2, 0.2 , ' ',
              transform=self.axtext.transAxes, color='grey')
    self.ro = 0.
    self.n0 = 0
    self.t0 = time.time()
    return self.line1, self.animtxt1, self.animtxt2  

  def __call__(self, n):
    if n == 0:
       self.init()

    k = n%self.Npoints
    RUNNING,TRun,Ntrig,Ttrig,Tlife,readrate,lifefrac,bufLevel = self.Q.get()
    self.R[k] = readrate
      
    self.line1.set_ydata(np.concatenate( (self.R[k+1:], self.R[:k+1]) ))
    self.animtxt1.set_text( \
       'Time: %.1fs  Triggers: %i  Lifetime: %.1fs (%.1f%%)'\
              %(TRun, Ntrig, Tlife, 100.*Tlife/TRun) )
    self.animtxt2.set_text( \
     'current rate: %.3gHz  life: %.1f%%  buffer: %.0f%%'\
          %(readrate, lifefrac, bufLevel) )

    return self.line1, self.animtxt1, self.animtxt2  
