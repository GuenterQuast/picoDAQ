# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
import matplotlib.pyplot as plt

class Histogram(object):
  ''' display histogram 

      requency distribution of a scalar quantity
  '''

  def __init__(self, 
         min, max, nbins, name='quantity'):
    '''
      Args:
        min: lower bound
        max: upper bound
        bins: number of bins
        name: name of quantity being histogrammed
    '''
    self.min = min
    self.max = max
    self.nbins = nbins
    self.entries = 0
    self.frqs = np.zeros(self.nbins)
  
  # histrogram properties
    self.width = 0.0
    self.be = np.linspace(self.min, self.max, self.nbins+1)    # bin edges
    self.bcent=(self.be[:-1] + self.be[1:])/2.                 # bin centers
    self.width = 0.9*(self.be[1]-self.be[0])                   # bar width

  # create figure 
    self.fig = plt.figure("Histogram", figsize=(5., 3.))
    self.fig.subplots_adjust(left=0.085, bottom=0.2, right=0.95, top=0.975,
               wspace=None, hspace=.25)
    self.axes = self.fig.add_subplot(1, 1, 1)
    self.axes.set_ylabel('frequency')
    self.axes.set_xlabel(name)
# guess an appropriate y-range for normalized histogram
    self.axes.set_ylim(0., 5./self.nbins)
    
  def init(self):
    # plot an empty histogram
    self.rects = self.axes.bar(self.bcent, self.frqs, align='center', 
                    width=self.width, facecolor='b', alpha=0.7)       
    # emty text
    self.animtxt = self.axes.text(0.8, 0.925 , ' ',
              transform=self.axes.transAxes,
              size='small', color='darkblue')

    return (self.animtxt,) + self.rects

  def __call__(self, vals):
    # add recent values to frequency array
    self.entries += len(vals)
    for v in vals:
      iv = int(self.nbins * (v-self.min) / (self.max-self.min))
      if iv >=0 and iv < self.nbins:
        self.frqs[iv]+=1
      norm = np.sum(self.frqs) # normalisation to one
    # set new heights for histogram bars
      for rect, frq in zip(self.rects, self.frqs):
        rect.set_height(frq/norm)
    # update text
      self.animtxt.set_text('Entries: %i'%(self.entries) )

    return (self.animtxt,) + self.rects
