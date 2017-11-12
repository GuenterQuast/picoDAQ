# -*- coding: utf-8 -*-

'''show buffer manager status in graphics window'''

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

# import plotBufManInfo class
from .plotBufManInfo import *

def mpBufManInfo(Q, maxRate = 100. , interval = 1000.):
  '''show Buffer Manager Information
    Args:
      Q:    multiprocessing.Queue()   
      maxrate: maximum rate for y-axis
      interval: update interval
  '''

  def sequence_gen():
  # generator for sequence of integers
    i=0
    while True:
      i+=1
      yield i
    return
  
# ------- executable part -------- 
  print(' -> mpBufManInfo starting')

  try:
    BMi = plotBufManInfo(Q, maxRate, interval)
    figBMi = BMi.fig

# generate a simple window for graphics display as a tk.DrawingArea
    root = Tk.Tk()
    root.wm_title("Buffer Manager Information")
    canvas = FigureCanvasTkAgg(figBMi, master=root)
    canvas.show()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    button = Tk.Button(master=root, text='Quit', command=sys.exit)
    button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
    BMiAnim = anim.FuncAnimation(figBMi, BMi, sequence_gen,
                         interval=interval, init_func=BMi.init,
                         blit=True, fargs=None, repeat=True, save_count=None) 
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    Tk.mainloop()
   
  except:
    print('*==* mpBufManInfo: termination signal recieved')
  sys.exit()
