# -*- coding: utf-8 -*-

'''Histogram display in TKinter window'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk
import numpy as np, matplotlib.pyplot as plt, matplotlib.animation as anim

# import Histogram class
from .Histogram import *

def mpHist(Q, min, max, bins, interval = 2500., name='Pulse height'):
#def mpHist(min, max, bins, interval, name='some quantity'):
  ''' show animated histogram
    Args:
      Q:    multiprocessing.Queue() 
      min: minium
      max: maximum
      bins: number of bins
      interval: update interval
      name: name of histogrammed variable
  '''

  # Generator to provide data to animation
  def yieldData_fromQ():
  # receive data from multiprocessing Queue 
    cnt = 0
    try:
      while True:
        vals = Q.get()
        cnt+=1
        yield vals
    except:
      print('*==* yieldData_fromQ: termination signal recieved')


# ------- executable part -------- 
  print(' -> mpHist starting')

  try:
    H = Histogram(min, max, bins, name)
    figH = H.fig
  # figure initialized

# generate a simple window for graphics display as a tk.DrawingArea
    root = Tk.Tk()
    root.wm_title("Histogram Display")
    canvas = FigureCanvasTkAgg(figH, master=root)
    canvas.show()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    button = Tk.Button(master=root, text='Quit', command=sys.exit)
    button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
    HAnim = anim.FuncAnimation(figH, H, yieldData_fromQ, 
                        init_func=H.init, interval=interval, blit=True,
                        fargs=None, repeat=True, save_count=None)
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    Tk.mainloop()
   
  except KeyboardInterrupt:
    print('*==* mpHist: termination signal recieved')
  sys.exit()
