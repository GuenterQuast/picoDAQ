# -*- coding: utf-8 -*-

'''Histogram display in TKinter window'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Histogram class
from .animHists import *

def mpHists(Q, Hdescripts, interval, name = 'Histograms'):
  ''' show animated histogram(s)
    Args:
      Q:    multiprocessing.Queue() 
      Hdescripts:  list of histogram descriptors, where each 
        descriptor is itself a list: [min, max, nbins, ymax, name, type]
          min: minimum value
          max: maximum value
          nbins: nubmer of bins
          ymax:  scale factor for bin with highest number of entries
          name: name of the quantity being histogrammed
          type: 0 linear, 1 for logarithmic y scale
  '''

  # Generator to provide data to animation
  def yieldData_fromQ():
  # receive data from multiprocessing Queue 
    cnt = 0
    try:
      while True:
        while not Q.qsize(): 
          time.sleep(0.1)
        valueslist = Q.get()
        cnt+=1
        yield valueslist
    except:
      print('*==* yieldData_fromQ: termination signal received')
      return


# ------- executable part -------- 
#  print(' -> mpHist starting')

  try:
    H = animHists(Hdescripts, name)
    figH = H.fig
# set up matplotlib animation
    HAnim = anim.FuncAnimation(figH, H, yieldData_fromQ, 
                        init_func=H.init, interval=interval, blit=True,
                        fargs=None, repeat=True, save_count=None)
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    plt.show()
  
  except:
    print('*==* mpHist: termination signal recieved')
  sys.exit()
