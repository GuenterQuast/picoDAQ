# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np

import matplotlib
#matplotlib.use('wxagg') # set backend (qt5 not running as thread in background)
matplotlib.use('tkagg') # set backend (qt5 not running as thread in background)
#matplotlib.use('gtkagg') # set backend (qt5 not running as thread in background)
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Oscilloscope class
from .Oscilloscope import *

def mpOsci(conf, Q):
  '''Oscilloscpe display of data passed via multiprocessing.Queue
    Args:
      conf: picoConfig object
      Q:    multiprocessing.Queue()   
  '''

  # Generator to provide data to animation
  def yieldEvt_fromQ():
# random consumer of Buffer Manager, receives an event copy 
   # via a Queue from package mutiprocessing
   
   cnt = 0
   try:
     while True:
       evNr, evTime, evData = Q.get()
       #print('*==* yieldEvt_fromQ: received event %i' % evNr)
       cnt+=1
       evt = (cnt, evNr, evTime, evData)
       yield evt
   except:
     print('*==* yieldEvt_fromQ: termination signal recieved')
  
# ------- executable part -------- 
  print('*==* mpOsci starting')

  try:
    Interval = 50.
    Osci = Oscilloscope(conf)
    figOs = Osci.fig
    osciAnim = anim.FuncAnimation(figOs, Osci, yieldEvt_fromQ, 
                        init_func=Osci.init, interval=Interval, blit=True,
                        fargs=None, repeat=True, save_count=None)
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    plt.show()
    
  except:
    print('*==* mpOsci: termination signal recieved')
  exit()
